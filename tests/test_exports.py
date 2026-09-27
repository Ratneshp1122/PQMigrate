import json
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

from pqc_migration_tool.exporters import (
    ExportValidationError,
    build_cbom,
    build_sarif,
    validate_export,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
CLI = REPO_ROOT / "cli.py"
VULNERABLE_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "vulnerable_python.py"


@pytest.fixture
def project_report() -> dict:
    source = str((REPO_ROOT / "tests" / "fixtures" / "review" / "review_rsa_jwt_signing.py").resolve())
    return {
        "schema_version": "2.2",
        "scan_id": str(uuid.uuid4()),
        "scanner_version": "0.3.0",
        "rules_version": "2026.09.26-d7.1",
        "source_commit": "a" * 40,
        "project_name": "review-fixtures",
        "scan_timestamp": "2026-09-27T00:00:00+00:00",
        "files_scanned": 1,
        "skipped_files": 0,
        "total_findings": 1,
        "errors": [],
        "records": [
            {
                "finding": {
                    "id": "finding12345",
                    "primitive_name": "RSA",
                    "location": {
                        "file_path": source,
                        "line_number": 12,
                        "column": 4,
                        "context_snippet": "private_key.sign(payload)",
                    },
                    "role": "signature",
                    "operation": "sign",
                    "status": "quantum_vulnerable",
                    "confidence": "inferred",
                    "detection_type": "linked_operation",
                    "protocol_context": "jwt",
                    "context_evidence": "same-scope call",
                },
                "plan": {
                    "target_algorithm": "ML-DSA assessment",
                    "target_standard": "FIPS 204",
                    "patch_available": False,
                    "requires_manual_intervention": True,
                    "rule_id": "RSA-SIGNATURE-001",
                    "rule_version": "2026.09.26-d7.1",
                    "blocker_codes": ["PROTOCOL_INTEROP_REQUIRED"],
                    "standard_refs": ["NIST FIPS 204"],
                    "decision_trace": {
                        "trace_id": "trace123",
                        "finding_id": "finding12345",
                        "outcome": "recommend",
                        "source_ref": {},
                        "steps": [],
                        "unresolved_fields": [],
                    },
                },
                "tests_passed": False,
                "verified_by_human": False,
            }
        ],
    }


def test_sarif_export_validates_and_preserves_traceability(project_report: dict) -> None:
    document = build_sarif(project_report)
    validate_export(document, "sarif")

    assert document["version"] == "2.1.0"
    result = document["runs"][0]["results"][0]
    assert result["ruleId"] == "RSA-SIGNATURE-001"
    assert result["level"] == "error"
    assert result["locations"][0]["physicalLocation"]["region"] == {
        "startLine": 12,
        "startColumn": 5,
    }
    assert result["properties"]["traceId"] == "trace123"
    assert result["properties"]["patchAvailable"] is False
    assert "context_snippet" not in json.dumps(document)
    assert "private_key.sign" not in json.dumps(document)


def test_cbom_export_validates_and_models_crypto_asset(project_report: dict) -> None:
    document = build_cbom(project_report)
    validate_export(document, "cbom")

    assert document["specVersion"] == "1.7"
    component = document["components"][0]
    assert component["type"] == "cryptographic-asset"
    assert component["cryptoProperties"] == {
        "assetType": "algorithm",
        "algorithmProperties": {"primitive": "signature"},
    }
    assert component["evidence"]["callstack"]["frames"][0]["line"] == 12
    properties = {item["name"]: item["value"] for item in component["properties"]}
    assert properties["pqmigrate:role"] == "signature"
    assert properties["pqmigrate:status"] == "quantum_vulnerable"
    assert properties["pqmigrate:patch-available"] == "false"
    assert document["compositions"][0]["aggregate"] == "incomplete"
    assert "context_snippet" not in json.dumps(document)


@pytest.mark.parametrize("export_format", ["sarif", "cbom"])
def test_malformed_export_is_rejected(export_format: str) -> None:
    with pytest.raises(ExportValidationError):
        validate_export({"unexpected": True}, export_format)


@pytest.mark.parametrize(
    ("export_format", "expected_key", "expected_value"),
    [("sarif", "version", "2.1.0"), ("cbom", "specVersion", "1.7")],
)
def test_cli_scan_writes_validated_external_export_once(
    tmp_path: Path,
    export_format: str,
    expected_key: str,
    expected_value: str,
) -> None:
    output = tmp_path / f"scan.{export_format}.json"
    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "scan",
            str(VULNERABLE_FIXTURE),
            "--format",
            export_format,
            "--output",
            str(output),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert result.stdout.count("PQC Migration Scanner") == 1
    document = json.loads(output.read_text(encoding="utf-8"))
    assert document[expected_key] == expected_value
    validate_export(document, export_format)


@pytest.mark.parametrize("export_format", ["sarif", "cbom"])
def test_cli_converts_existing_project_report(
    tmp_path: Path,
    project_report: dict,
    export_format: str,
) -> None:
    source = tmp_path / "project-report.json"
    output = tmp_path / f"converted.{export_format}.json"
    source.write_text(json.dumps(project_report), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "export",
            str(source),
            "--format",
            export_format,
            "--output",
            str(output),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    validate_export(json.loads(output.read_text(encoding="utf-8")), export_format)
