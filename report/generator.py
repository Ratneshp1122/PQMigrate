"""
Report Generator
==================
Three output formats:
  - Console: colored terminal output (default)
  - JSON: machine-readable, suitable for CI/CD
  - Markdown: for documentation / GitHub issues / Jira tickets
"""

import json
import sys
from pathlib import Path

from ..scanner.patterns import Risk
from ..scanner.python_scanner import Finding
from ..risk.scorer import FileSummary, SystemSummary


# ── ANSI colors (auto-disabled if not a TTY) ──────────────────────────────────
def _supports_color() -> bool:
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


class C:
    RESET  = "\033[0m"   if _supports_color() else ""
    BOLD   = "\033[1m"   if _supports_color() else ""
    RED    = "\033[91m"  if _supports_color() else ""
    ORANGE = "\033[93m"  if _supports_color() else ""
    YELLOW = "\033[33m"  if _supports_color() else ""
    GREEN  = "\033[92m"  if _supports_color() else ""
    CYAN   = "\033[96m"  if _supports_color() else ""
    DIM    = "\033[2m"   if _supports_color() else ""
    BLUE   = "\033[94m"  if _supports_color() else ""


RISK_COLOR = {
    Risk.CRITICAL: C.RED,
    Risk.HIGH:     C.ORANGE,
    Risk.MEDIUM:   C.YELLOW,
    Risk.SAFE:     C.GREEN,
}

RISK_ICON = {
    Risk.CRITICAL: "✗",
    Risk.HIGH:     "⚠",
    Risk.MEDIUM:   "~",
    Risk.SAFE:     "✓",
}


# ── Console reporter ──────────────────────────────────────────────────────────

def report_console(
    summary:   SystemSummary,
    show_safe: bool = False,
    verbose:   bool = False,
) -> None:
    _print_header(summary)
    _print_findings(summary, show_safe=show_safe, verbose=verbose)
    _print_summary_table(summary)
    _print_recommendations(summary)


def _print_header(summary: SystemSummary):
    print()
    print(f"{C.BOLD}{'═' * 70}{C.RESET}")
    print(f"{C.BOLD}  PQC Migration Scanner{C.RESET}  |  "
          f"Scanning: {C.CYAN}{summary.root}{C.RESET}")
    print(f"{'═' * 70}")
    print()


def _print_findings(summary: SystemSummary, show_safe: bool, verbose: bool):
    prev_file = None
    for fs in summary.file_summaries:
        for finding in fs.findings:
            if not show_safe and finding.pattern.risk == Risk.SAFE:
                continue

            # File header
            rel = _rel(finding.filepath, summary.root)
            if rel != prev_file:
                print(f"{C.BOLD}{C.BLUE}  {rel}{C.RESET}")
                prev_file = rel

            color = RISK_COLOR[finding.pattern.risk]
            icon  = RISK_ICON[finding.pattern.risk]

            print(
                f"    {color}{C.BOLD}[{finding.pattern.risk.value:8s}]{C.RESET} "
                f"{color}{icon}{C.RESET} "
                f"Line {finding.line:<4}  "
                f"{C.BOLD}{finding.pattern.name}{C.RESET}"
            )
            if verbose:
                print(f"           {C.DIM}{finding.match_text}{C.RESET}")
            print(f"           {C.DIM}→ {finding.pattern.replacement}{C.RESET}")
            if finding.pattern.harvest_risk:
                print(f"           {C.RED}⚡ HARVEST RISK{C.RESET}"
                      f"{C.DIM} — data encrypted today readable by future QC{C.RESET}")
        if fs.findings:
            visible = [f for f in fs.findings
                       if show_safe or f.pattern.risk != Risk.SAFE]
            if visible:
                print()


def _print_summary_table(summary: SystemSummary):
    print(f"{'─' * 70}")
    print(f"{C.BOLD}  SCAN SUMMARY{C.RESET}")
    print(f"{'─' * 70}")
    print(f"  Files scanned      : {summary.files_scanned}")
    print(f"  Files with issues  : {summary.files_with_findings}")
    print(f"  Total findings     : {summary.total_findings}")
    print()
    print(f"  {C.RED}{C.BOLD}  CRITICAL{C.RESET}          : {summary.critical_count}")
    print(f"  {C.ORANGE}{C.BOLD}  HIGH    {C.RESET}          : {summary.high_count}")
    print(f"  {C.YELLOW}  MEDIUM  {C.RESET}          : {summary.medium_count}")
    print(f"  {C.GREEN}  SAFE    {C.RESET}          : {summary.safe_count}")
    print()
    print(f"  Harvest-risk files : {summary.harvest_risk_files}  "
          f"{C.DIM}(data encrypted today, readable by future QC){C.RESET}")
    print()
    score_color = (C.RED if summary.system_risk_score >= 70
                   else C.ORANGE if summary.system_risk_score >= 40
                   else C.YELLOW if summary.system_risk_score >= 10
                   else C.GREEN)
    print(f"  {C.BOLD}Risk Score   : {score_color}{summary.system_risk_score:.1f}/100{C.RESET}")
    print(f"  {C.BOLD}CISA Grade   : {score_color}{summary.compliance_grade}{C.RESET}")
    print()


def _print_recommendations(summary: SystemSummary):
    if summary.critical_count == 0 and summary.high_count == 0:
        return
    print(f"{'─' * 70}")
    print(f"{C.BOLD}  MIGRATION PRIORITY{C.RESET}")
    print(f"{'─' * 70}")

    if summary.harvest_risk_files > 0:
        print(f"  {C.RED}1. IMMEDIATE — Harvest risk files ({summary.harvest_risk_files}){C.RESET}")
        print(f"     Key exchange protocols protecting sensitive long-term data.")
        print(f"     Adversaries may be collecting this data today.")
        print(f"     → Migrate to Hybrid X25519+ML-KEM-768 (IETF pattern)")
        print()

    if summary.critical_count > 0:
        print(f"  {C.RED}2. CRITICAL — {summary.critical_count} findings{C.RESET}")
        print(f"     RSA, ECDH, ECDSA, DSA — all broken by Shor's algorithm.")
        print(f"     → ML-KEM-768 (key encapsulation), ML-DSA-65 (signatures)")
        print(f"     Reference: NIST FIPS 203/204 — https://csrc.nist.gov/pqcrypto")
        print()

    print(f"  Run with --migration to see before/after code examples.")
    print()


# ── JSON reporter ─────────────────────────────────────────────────────────────

def report_json(summary: SystemSummary, output_path: str | None = None) -> str:
    import uuid
    from datetime import datetime
    import os
    from pqc_migration_tool.schema.models import ProjectReport, CryptoIR, CodeLocation, CryptoRole, CryptoOperation, SecurityStatus, ConfidenceLevel
    from pqc_migration_tool.resolver.planner import MigrationPlanner
    
    planner = MigrationPlanner()
    records = []
    
    for fs in summary.file_summaries:
        for f in fs.findings:
            is_import = "import" in f.match_type.lower()
            role = CryptoRole.UNKNOWN
            op = CryptoOperation.UNKNOWN
            
            if not is_import:
                name_lower = f.pattern.name.lower()
                if any(x in name_lower for x in ["sign", "ecdsa", "ed25519", "dsa"]):
                    role = CryptoRole.SIGNATURE
                    op = CryptoOperation.SIGN
                elif any(x in name_lower for x in ["x25519", "ecdh", "dh"]):
                    role = CryptoRole.KEY_ESTABLISHMENT
                    op = CryptoOperation.GENERATE
                elif "encrypt" in name_lower or "rsa" in name_lower:
                    role = CryptoRole.KEY_TRANSPORT
                    op = CryptoOperation.ENCRYPT
                elif "sha" in name_lower or "md5" in name_lower:
                    role = CryptoRole.HASH
                    op = CryptoOperation.HASH
                elif "aes" in name_lower:
                    role = CryptoRole.ENCRYPTION
                    op = CryptoOperation.ENCRYPT
                    
            status = SecurityStatus.QUANTUM_VULNERABLE
            if f.pattern.risk.value == "SAFE":
                status = SecurityStatus.STANDARDIZED_PQC
            elif "sha256" in f.pattern.name.lower() or "aes" in f.pattern.name.lower():
                status = SecurityStatus.QUANTUM_SECURITY_REDUCED
            elif f.pattern.risk.value == "MEDIUM":
                status = SecurityStatus.DEPRECATED_CLASSICALLY
                
            ir = CryptoIR(
                id=uuid.uuid4().hex[:12],
                primitive_name=f.pattern.name,
                location=CodeLocation(
                    file_path=f.filepath,
                    line_number=f.line,
                    column=f.col,
                    context_snippet=f.match_text
                ),
                role=role,
                operation=op,
                status=status,
                confidence=ConfidenceLevel.AMBIGUOUS if is_import else ConfidenceLevel.DIRECT,
                detection_type="import_lead" if is_import else "operation_candidate"
            )
            records.append(planner.generate_plan(ir))
            
    report = ProjectReport(
        project_name=os.path.basename(os.path.abspath(summary.root)),
        scan_timestamp=datetime.utcnow().isoformat(),
        files_scanned=summary.files_scanned,
        total_findings=summary.total_findings,
        records=records
    )
    
    out = report.to_json()
    if output_path:
        Path(output_path).write_text(out)
        print(f"  JSON report (Schema v2) saved → {output_path}")
    return out


# ── Markdown reporter ─────────────────────────────────────────────────────────

def report_markdown(summary: SystemSummary, output_path: str | None = None) -> str:
    lines = []
    lines.append("# PQC Migration Scan Report\n")
    lines.append(f"**Scanned:** `{summary.root}`  ")
    lines.append(f"**Risk Score:** {summary.system_risk_score:.1f}/100  ")
    lines.append(f"**CISA Grade:** {summary.compliance_grade}  ")
    lines.append("")

    # Summary table
    lines.append("## Summary\n")
    lines.append("| Metric | Count |")
    lines.append("|---|---|")
    lines.append(f"| Files scanned | {summary.files_scanned} |")
    lines.append(f"| Files with issues | {summary.files_with_findings} |")
    lines.append(f"| 🔴 CRITICAL findings | {summary.critical_count} |")
    lines.append(f"| 🟠 HIGH findings | {summary.high_count} |")
    lines.append(f"| 🟡 MEDIUM findings | {summary.medium_count} |")
    lines.append(f"| 🟢 SAFE (already PQC) | {summary.safe_count} |")
    lines.append(f"| ⚡ Harvest-risk files | {summary.harvest_risk_files} |")
    lines.append("")

    # Per-file findings
    lines.append("## Findings\n")
    for fs in summary.file_summaries:
        vulns = [f for f in fs.findings if f.pattern.risk != Risk.SAFE]
        if not vulns:
            continue
        lines.append(f"### `{_rel(fs.filepath, summary.root)}`")
        lines.append("")
        lines.append("| Line | Risk | Primitive | Replacement | Harvest? |")
        lines.append("|---|---|---|---|---|")
        for f in vulns:
            harvest = "⚡ YES" if f.pattern.harvest_risk else "No"
            icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "SAFE": "🟢"}[f.pattern.risk.value]
            lines.append(f"| {f.line} | {icon} {f.pattern.risk.value} | "
                         f"{f.pattern.name} | {f.pattern.replacement} | {harvest} |")
        lines.append("")

    # Migration references
    lines.append("## References\n")
    lines.append("- [NIST FIPS 203 (ML-KEM)](https://csrc.nist.gov/pubs/fips/203/final)")
    lines.append("- [NIST FIPS 204 (ML-DSA)](https://csrc.nist.gov/pubs/fips/204/final)")
    lines.append("- [NIST FIPS 205 (SLH-DSA)](https://csrc.nist.gov/pubs/fips/205/final)")
    lines.append("- [CISA PQC Migration](https://www.cisa.gov/resources-tools/resources/post-quantum-cryptography-pqc-resources)")
    lines.append("- [IETF Hybrid TLS Design](https://datatracker.ietf.org/doc/draft-ietf-tls-hybrid-design/)")
    lines.append("")

    out = "\n".join(lines)
    if output_path:
        Path(output_path).write_text(out)
        print(f"  Markdown report saved → {output_path}")
    return out


# ── Helpers ───────────────────────────────────────────────────────────────────

def _rel(filepath: str, root: str) -> str:
    """Return filepath relative to root for cleaner display."""
    try:
        return str(Path(filepath).relative_to(root))
    except ValueError:
        return filepath
