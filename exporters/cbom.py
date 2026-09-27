"""CycloneDX 1.7 Cryptographic Bill of Materials export."""

import re
from typing import Any

from .common import joined, records, relative_path, source_root, text


CBOM_SCHEMA_URI = "http://cyclonedx.org/schema/bom-1.7.schema.json"


def _primitive(finding: dict[str, Any]) -> str:
    name = str(finding.get("primitive_name", "")).lower()
    role = finding.get("role")
    if "hash" in name or "sha" in name or "md5" in name or role == "hash":
        return "hash"
    if role == "signature" or any(value in name for value in ("ecdsa", "ed25519", "dsa", "signature")):
        return "signature"
    if any(value in name for value in ("aes", "des", "chacha", "symmetric")):
        return "block-cipher"
    if role == "key_establishment":
        return "key-agree"
    if role == "key_transport" or "rsa" in name:
        return "pke"
    if role == "mac":
        return "mac"
    return "unknown"


def _crypto_properties(finding: dict[str, Any]) -> dict[str, Any]:
    name = str(finding.get("primitive_name", "")).lower()
    context = str(finding.get("protocol_context", "")).lower()
    if "tls" in name or context == "tls":
        return {"assetType": "protocol", "protocolProperties": {"type": "tls"}}
    if "ssh" in name or context in {"ssh", "possible_ssh"}:
        return {"assetType": "protocol", "protocolProperties": {"type": "ssh"}}
    return {"assetType": "algorithm", "algorithmProperties": {"primitive": _primitive(finding)}}


def _property(name: str, value: Any) -> dict[str, str]:
    return {"name": f"pqmigrate:{name}", "value": text(value)}


def _component(record: dict[str, Any], root) -> dict[str, Any]:
    finding = record["finding"]
    location = finding["location"]
    plan = record.get("plan") or {}
    trace = plan.get("decision_trace") or {}
    frame: dict[str, Any] = {
        "module": relative_path(location["file_path"], root),
        "line": max(1, int(location.get("line_number") or 1)),
    }
    if location.get("column") is not None:
        frame["column"] = max(1, int(location["column"]) + 1)

    properties = [
        _property("finding-id", finding.get("id")),
        _property("role", finding.get("role")),
        _property("operation", finding.get("operation")),
        _property("status", finding.get("status")),
        _property("confidence", finding.get("confidence")),
        _property("detection-type", finding.get("detection_type")),
        _property("protocol-context", finding.get("protocol_context")),
        _property("rule-id", plan.get("rule_id")),
        _property("rule-version", plan.get("rule_version")),
        _property("trace-id", trace.get("trace_id")),
        _property("decision-outcome", trace.get("outcome")),
        _property("blocker-codes", joined(plan.get("blocker_codes"))),
        _property("standard-refs", joined(plan.get("standard_refs"))),
        _property("target-algorithm", plan.get("target_algorithm")),
        _property("patch-available", bool(plan.get("patch_available", False))),
    ]
    return {
        "type": "cryptographic-asset",
        "bom-ref": f"pqmigrate:crypto:{finding.get('id')}",
        "name": text(finding.get("primitive_name") or "Unknown cryptographic usage"),
        "cryptoProperties": _crypto_properties(finding),
        "evidence": {"callstack": {"frames": [frame]}},
        "properties": properties,
    }


def build_cbom(report: dict[str, Any]) -> dict[str, Any]:
    """Map a PQMigrate ProjectReport dictionary to a CycloneDX 1.7 CBOM."""
    root = source_root(report)
    components = [_component(record, root) for record in records(report)]
    references = [component["bom-ref"] for component in components]
    project_name = text(report.get("project_name") or "scanned-project")
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "-", project_name).strip("-") or "scanned-project"
    app_ref = f"application:{safe_name}"
    source_commit = text(report.get("source_commit"))
    app_version = source_commit[:12] if source_commit else "unknown"

    document: dict[str, Any] = {
        "$schema": CBOM_SCHEMA_URI,
        "bomFormat": "CycloneDX",
        "specVersion": "1.7",
        "serialNumber": f"urn:uuid:{report.get('scan_id')}",
        "version": 1,
        "metadata": {
            "timestamp": report.get("scan_timestamp"),
            "tools": {"components": [{"type": "application", "name": "PQMigrate", "version": text(report.get("scanner_version") or "0.3.0")}]},
            "component": {"type": "application", "bom-ref": app_ref, "name": project_name, "version": app_version},
        },
        "components": components,
        "dependencies": [{"ref": app_ref, "dependsOn": references}]
        + [{"ref": reference, "dependsOn": []} for reference in references],
        "compositions": [{"aggregate": "incomplete", "assemblies": references}],
        "properties": [
            _property("scan-id", report.get("scan_id")),
            _property("schema-version", report.get("schema_version")),
            _property("scanner-version", report.get("scanner_version")),
            _property("rules-version", report.get("rules_version")),
            _property("source-commit", report.get("source_commit")),
            _property(
                "scope-note",
                "Bounded static-analysis inventory; absence of a component is not proof that cryptography is absent.",
            ),
        ],
    }
    return document
