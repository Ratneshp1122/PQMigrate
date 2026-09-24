"""
Risk Scoring Engine
======================
Converts raw scanner findings into:
  - Per-finding risk scores (0–100)
  - Per-file risk summary
  - System-level risk score + compliance grade
  - Harvest-now-decrypt-later priority flags
"""

from collections import defaultdict
from dataclasses import dataclass, field

from ..scanner.patterns import Risk
from ..scanner.python_scanner import Finding


# ── Weights ───────────────────────────────────────────────────────────────────
RISK_SCORE = {
    Risk.CRITICAL: 100,
    Risk.HIGH:      70,
    Risk.MEDIUM:    40,
    Risk.SAFE:       0,
}

HARVEST_MULTIPLIER = 1.25   # findings with harvest risk score higher


# ── Per-file summary ──────────────────────────────────────────────────────────
@dataclass
class FileSummary:
    filepath:       str
    findings:       list[Finding]
    risk_score:     float   = 0.0
    critical_count: int     = 0
    high_count:     int     = 0
    medium_count:   int     = 0
    safe_count:     int     = 0
    harvest_risk:   bool    = False
    dominant_risk:  Risk    = Risk.SAFE

    def as_dict(self) -> dict:
        return {
            "file":          self.filepath,
            "risk_score":    round(self.risk_score, 1),
            "dominant_risk": self.dominant_risk.value,
            "harvest_risk":  self.harvest_risk,
            "counts": {
                "critical": self.critical_count,
                "high":     self.high_count,
                "medium":   self.medium_count,
                "safe":     self.safe_count,
            },
        }


# ── System summary ────────────────────────────────────────────────────────────
@dataclass
class SystemSummary:
    root:                str
    files_scanned:       int
    files_with_findings: int
    total_findings:      int
    critical_count:      int
    high_count:          int
    medium_count:        int
    safe_count:          int
    harvest_risk_files:  int
    system_risk_score:   float
    compliance_grade:    str
    file_summaries:      list[FileSummary] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "root":                self.root,
            "files_scanned":       self.files_scanned,
            "files_with_findings": self.files_with_findings,
            "total_findings":      self.total_findings,
            "counts": {
                "critical": self.critical_count,
                "high":     self.high_count,
                "medium":   self.medium_count,
                "safe":     self.safe_count,
            },
            "harvest_risk_files":  self.harvest_risk_files,
            "system_risk_score":   round(self.system_risk_score, 1),
            "compliance_grade":    self.compliance_grade,
            "files":  [f.as_dict() for f in self.file_summaries],
        }


# ── Scoring functions ─────────────────────────────────────────────────────────

def score_finding(finding: Finding) -> float:
    """Return 0–100 numeric risk for a single finding."""
    base = RISK_SCORE[finding.pattern.risk]
    if finding.pattern.harvest_risk:
        base = min(100, base * HARVEST_MULTIPLIER)
    return base


def score_file(filepath: str, findings: list[Finding]) -> FileSummary:
    """Aggregate findings for a single file."""
    summary = FileSummary(filepath=filepath, findings=findings)

    if not findings:
        return summary

    scores = []
    for f in findings:
        s = score_finding(f)
        scores.append(s)
        if f.pattern.risk == Risk.CRITICAL:
            summary.critical_count += 1
        elif f.pattern.risk == Risk.HIGH:
            summary.high_count += 1
        elif f.pattern.risk == Risk.MEDIUM:
            summary.medium_count += 1
        else:
            summary.safe_count += 1
        if f.pattern.harvest_risk:
            summary.harvest_risk = True

    # File risk = max of individual scores (worst-case, not average)
    # This is intentional: one CRITICAL finding makes the file CRITICAL
    summary.risk_score = max(scores)

    # Determine dominant risk level
    if summary.critical_count > 0:
        summary.dominant_risk = Risk.CRITICAL
    elif summary.high_count > 0:
        summary.dominant_risk = Risk.HIGH
    elif summary.medium_count > 0:
        summary.dominant_risk = Risk.MEDIUM
    else:
        summary.dominant_risk = Risk.SAFE

    return summary


def score_system(
    root: str,
    all_findings: list[Finding],
    files_scanned: int,
) -> SystemSummary:
    """Aggregate all findings into a system-level risk summary."""
    # Group findings by file
    by_file: dict[str, list[Finding]] = defaultdict(list)
    for f in all_findings:
        by_file[f.filepath].append(f)

    file_summaries = [
        score_file(fp, findings)
        for fp, findings in sorted(by_file.items())
    ]

    critical = sum(f.critical_count for f in file_summaries)
    high     = sum(f.high_count     for f in file_summaries)
    medium   = sum(f.medium_count   for f in file_summaries)
    safe     = sum(f.safe_count     for f in file_summaries)
    harvest  = sum(1 for f in file_summaries if f.harvest_risk)

    # System risk: weighted average of file scores (max-weighted toward worst files)
    if file_summaries:
        scores = [f.risk_score for f in file_summaries if f.findings]
        system_score = max(scores) * 0.6 + (sum(scores) / len(scores)) * 0.4 if scores else 0.0
    else:
        system_score = 0.0

    # Compliance grade (CISA-inspired)
    if critical > 0:
        grade = "F — Immediate action required"
    elif high > 0:
        grade = "D — High priority migration needed"
    elif medium > 0:
        grade = "C — Moderate risk, plan migration"
    elif critical == 0 and high == 0 and medium == 0:
        # Either explicitly SAFE patterns found, or clean scan with no findings
        grade = "A — Quantum-ready"
    else:
        grade = "B — Low risk"

    return SystemSummary(
        root=root,
        files_scanned=files_scanned,
        files_with_findings=len([f for f in file_summaries if f.findings]),
        total_findings=len(all_findings),
        critical_count=critical,
        high_count=high,
        medium_count=medium,
        safe_count=safe,
        harvest_risk_files=harvest,
        system_risk_score=system_score,
        compliance_grade=grade,
        file_summaries=file_summaries,
    )
