"""Read-only SARIF bridge for external crypto-discovery leads.

External results are never promoted to a PQMigrate operation, role, plan, or
gold label. This module only aligns source locations for human triage.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlparse

MAX_INPUT_BYTES = 25 * 1024 * 1024
MAX_RESULTS = 100_000


def _read_json(path: Path) -> tuple[dict, str]:
    if path.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError(f"Input exceeds {MAX_INPUT_BYTES} bytes: {path}")
    raw = path.read_bytes()
    if len(raw) > MAX_INPUT_BYTES:
        raise ValueError(f"Input exceeds {MAX_INPUT_BYTES} bytes: {path}")
    document = json.loads(raw)
    if not isinstance(document, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return document, hashlib.sha256(raw).hexdigest()


def _relative_source(root: Path, uri: str) -> tuple[str, bool] | None:
    parsed = urlparse(uri)
    if parsed.scheme not in {"", "file"} or parsed.netloc not in {"", "localhost"}:
        return None
    decoded = unquote(parsed.path if parsed.scheme else uri)
    if not decoded or "\x00" in decoded or "\\" in decoded:
        return None
    candidate = Path(decoded)
    resolved = (candidate if candidate.is_absolute() else root / candidate).resolve()
    try:
        relative = resolved.relative_to(root)
    except ValueError:
        return None
    if relative == Path("."):
        return None
    return relative.as_posix(), resolved.is_file()


def _internal_locations(root: Path, report_path: Path | None) -> tuple[dict, str | None]:
    if report_path is None:
        return {}, None
    report, _ = _read_json(report_path)
    records = report.get("records")
    if not isinstance(records, list):
        raise ValueError("PQMigrate report has no records list")
    locations: dict[tuple[str, int], list[dict]] = {}
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("finding"), dict):
            continue
        finding = record["finding"]
        location = finding.get("location", {})
        if not isinstance(location, dict):
            continue
        path = location.get("file_path")
        line = location.get("line_number")
        if not isinstance(path, str) or not isinstance(line, int) or line < 1:
            continue
        normalized = _relative_source(root, path)
        if normalized is None:
            continue
        key = (normalized[0], line)
        locations.setdefault(key, []).append({
            "id": finding.get("id"),
            "detection_type": finding.get("detection_type"),
            "role": finding.get("role"),
        })
    return locations, report.get("source_commit")


def _git_head(root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=False, timeout=3,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    commit = result.stdout.strip()
    return commit if result.returncode == 0 and len(commit) == 40 else None


def build_external_triage(
    source_root: Path,
    sarif_inputs: list[tuple[str, Path]],
    pqmigrate_report: Path | None = None,
) -> dict:
    """Align bounded SARIF locations with a canonical PQMigrate report."""
    root = source_root.resolve()
    if not root.is_dir():
        raise ValueError(f"Source root is not a directory: {root}")
    if not sarif_inputs:
        raise ValueError("At least one SARIF input is required")
    internal, source_commit = _internal_locations(root, pqmigrate_report)
    inputs: list[dict] = []
    grouped: dict[tuple[str, int], dict] = {}
    git_head = _git_head(root)
    for tool_name, path in sarif_inputs:
        if not tool_name or not tool_name.replace("-", "").replace("_", "").isalnum():
            raise ValueError(f"Invalid tool name: {tool_name!r}")
        sarif, digest = _read_json(path)
        if sarif.get("version") != "2.1.0" or not isinstance(sarif.get("runs"), list):
            raise ValueError(f"Not SARIF 2.1.0: {path}")
        retained = skipped = examined = 0
        versions: set[str] = set()
        drivers: set[str] = set()
        for run in sarif["runs"]:
            if not isinstance(run, dict) or not isinstance(run.get("results", []), list):
                raise ValueError(f"Malformed SARIF run: {path}")
            tool = run.get("tool", {})
            driver = tool.get("driver", {}) if isinstance(tool, dict) else {}
            if not isinstance(driver, dict):
                driver = {}
            if isinstance(driver.get("name"), str):
                drivers.add(driver["name"])
            version = driver.get("semanticVersion") or driver.get("version")
            if isinstance(version, str):
                versions.add(version)
            results = run.get("results", [])
            examined += len(results)
            if examined > MAX_RESULTS:
                raise ValueError(f"Too many SARIF results: {path}")
            for result in results:
                if not isinstance(result, dict):
                    skipped += 1
                    continue
                locations = result.get("locations", [])
                physical = locations[0].get("physicalLocation", {}) if locations and isinstance(locations[0], dict) else {}
                artifact = physical.get("artifactLocation", {})
                region = physical.get("region", {})
                uri = artifact.get("uri") if isinstance(artifact, dict) else None
                line = region.get("startLine") if isinstance(region, dict) else None
                normalized = _relative_source(root, uri) if isinstance(uri, str) else None
                if normalized is None or not isinstance(line, int) or line < 1:
                    skipped += 1
                    continue
                relpath, exists = normalized
                key = (relpath, line)
                candidate = grouped.setdefault(key, {
                    "path": relpath, "line": line, "source_exists": exists,
                    "external_evidence": [],
                })
                message = result.get("message", {})
                candidate["external_evidence"].append({
                    "tool": tool_name,
                    "rule_id": result.get("ruleId"),
                    "level": result.get("level"),
                    "message": message.get("text") if isinstance(message, dict) else None,
                    "column": region.get("startColumn") if isinstance(region, dict) else None,
                })
                retained += 1
        inputs.append({
            "tool": tool_name, "path": str(path.resolve()), "sha256": digest,
            "reported_drivers": sorted(drivers),
            "reported_versions": sorted(versions),
            "retained_results": retained, "skipped_results": skipped,
        })
    candidates = []
    for key, candidate in sorted(grouped.items()):
        matches = internal.get(key, [])
        candidate["pqmigrate_same_line"] = matches
        candidate["triage_class"] = (
            "linked_overlap" if any(match["detection_type"] == "linked_operation" for match in matches)
            else "inventory_overlap" if matches else "external_only"
        )
        candidate["review_state"] = "unverified_external_lead"
        candidate["planning_eligible"] = False
        candidates.append(candidate)
    return {
        "schema_version": "1.0", "kind": "external_discovery_triage",
        "source_root": str(root), "pqmigrate_source_commit": source_commit,
        "source_git_head": git_head,
        "source_commit_matches_report": (
            source_commit == git_head if source_commit and git_head else None
        ),
        "inputs": inputs, "candidate_count": len(candidates),
        "external_only_count": sum(item["triage_class"] == "external_only" for item in candidates),
        "candidates": candidates,
        "note": "Same-line overlap is not semantic agreement. External leads do not create roles or migration plans.",
    }
