"""SARIF 2.1.0 export for PQMigrate findings and advisory decisions."""

from typing import Any

from .common import joined, records, relative_path, source_root, text


SARIF_SCHEMA_URI = (
    "https://docs.oasis-open.org/sarif/sarif/v2.1.0/errata01/os/"
    "schemas/sarif-schema-2.1.0.json"
)


def _level(status: str) -> str:
    if status == "quantum_vulnerable":
        return "error"
    if status in {"deprecated_classically", "quantum_security_reduced", "context_dependent"}:
        return "warning"
    return "note"


def _rule_descriptor(record: dict[str, Any]) -> dict[str, Any]:
    finding = record["finding"]
    plan = record.get("plan") or {}
    rule_id = plan.get("rule_id") or "PQMIGRATE-UNRESOLVED"
    target = plan.get("target_algorithm") or "manual review"
    standard = plan.get("target_standard") or "not determined"
    return {
        "id": rule_id,
        "name": rule_id.replace("-", "_"),
        "shortDescription": {
            "text": f"Review {finding.get('primitive_name', 'cryptographic usage')} for PQC migration"
        },
        "fullDescription": {
            "text": f"PQMigrate advisory target: {target}; target standard: {standard}."
        },
        "help": {
            "text": "Review protocol constraints and interoperability before changing cryptography.",
        },
        "properties": {
            "ruleVersion": text(plan.get("rule_version")),
            "standardRefs": joined(plan.get("standard_refs")),
            "tags": ["security", "cryptography", "post-quantum-cryptography"],
        },
    }


def build_sarif(report: dict[str, Any]) -> dict[str, Any]:
    """Map a PQMigrate ProjectReport dictionary to SARIF 2.1.0."""
    report_records = records(report)
    root = source_root(report)
    descriptors: list[dict[str, Any]] = []
    rule_indexes: dict[str, int] = {}
    for record in report_records:
        rule_id = (record.get("plan") or {}).get("rule_id") or "PQMIGRATE-UNRESOLVED"
        if rule_id not in rule_indexes:
            rule_indexes[rule_id] = len(descriptors)
            descriptors.append(_rule_descriptor(record))

    artifact_uris: list[str] = []
    sarif_results: list[dict[str, Any]] = []
    for record in report_records:
        finding = record["finding"]
        location = finding["location"]
        plan = record.get("plan") or {}
        trace = plan.get("decision_trace") or {}
        uri = relative_path(location["file_path"], root)
        if uri not in artifact_uris:
            artifact_uris.append(uri)

        rule_id = plan.get("rule_id") or "PQMIGRATE-UNRESOLVED"
        region: dict[str, Any] = {"startLine": max(1, int(location.get("line_number") or 1))}
        if location.get("column") is not None:
            region["startColumn"] = max(1, int(location["column"]) + 1)

        outcome = trace.get("outcome") or "unknown"
        target = plan.get("target_algorithm") or "manual review"
        sarif_results.append(
            {
                "ruleId": rule_id,
                "ruleIndex": rule_indexes[rule_id],
                "level": _level(finding.get("status", "unknown")),
                "message": {
                    "text": (
                        f"{finding.get('primitive_name', 'Cryptographic usage')} "
                        f"({finding.get('role', 'unknown')}/{finding.get('operation', 'unknown')}) "
                        f"is {finding.get('status', 'unknown')}; advisory target: {target}; "
                        f"decision: {outcome}."
                    )
                },
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": uri, "uriBaseId": "%SRCROOT%"},
                            "region": region,
                        }
                    }
                ],
                "partialFingerprints": {"pqmigrateFindingId": text(finding.get("id"))},
                "properties": {
                    "confidence": text(finding.get("confidence")),
                    "detectionType": text(finding.get("detection_type")),
                    "protocolContext": text(finding.get("protocol_context")),
                    "traceId": text(trace.get("trace_id")),
                    "decisionOutcome": text(outcome),
                    "ruleVersion": text(plan.get("rule_version")),
                    "blockerCodes": joined(plan.get("blocker_codes")),
                    "standardRefs": joined(plan.get("standard_refs")),
                    "patchAvailable": bool(plan.get("patch_available", False)),
                },
            }
        )

    run: dict[str, Any] = {
        "tool": {
            "driver": {
                "name": "PQMigrate",
                "semanticVersion": text(report.get("scanner_version") or "0.3.0"),
                "informationUri": "https://github.com/ratneshp0411/pqc_migration_tool",
                "rules": descriptors,
            }
        },
        "invocations": [
            {
                "executionSuccessful": True,
                "properties": {
                    "scanId": text(report.get("scan_id")),
                    "schemaVersion": text(report.get("schema_version")),
                    "rulesVersion": text(report.get("rules_version")),
                    "sourceCommit": text(report.get("source_commit")),
                },
            }
        ],
        "artifacts": [{"location": {"uri": uri, "uriBaseId": "%SRCROOT%"}} for uri in artifact_uris],
        "results": sarif_results,
    }
    if root is not None:
        run["originalUriBaseIds"] = {"%SRCROOT%": {"uri": root.as_uri() + "/"}}

    return {"$schema": SARIF_SCHEMA_URI, "version": "2.1.0", "runs": [run]}
