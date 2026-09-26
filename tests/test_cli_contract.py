import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CLI = REPO_ROOT / "cli.py"
VULNERABLE_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "vulnerable_python.py"
REVIEW_FIXTURES = REPO_ROOT / "tests" / "fixtures" / "review"


def test_help_has_one_cli_version() -> None:
    result = subprocess.run(
        [sys.executable, str(CLI)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout.count("PQC Migration Scanner") == 1
    assert "v0.3.0" in result.stdout
    assert "v0.1.0" not in result.stdout
    assert "list-rules" in result.stdout


def test_list_rules_validates_and_prints_active_version() -> None:
    result = subprocess.run(
        [sys.executable, str(CLI), "list-rules"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "2026.09.26-d7.1" in result.stdout
    assert "RSA-SIGNATURE-001" in result.stdout
    assert "Rule count    : 9" in result.stdout


def test_json_output_is_written_once(tmp_path: Path) -> None:
    output = tmp_path / "scan.json"
    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "scan",
            str(VULNERABLE_FIXTURE),
            "--format",
            "json",
            "--output",
            str(output),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    # Findings intentionally produce the scanner's policy exit code 1.
    assert result.returncode == 1
    assert result.stdout.count("PQC Migration Scanner") == 1
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["schema_version"] == "2.1"
    assert report["scan_id"]
    assert report["files_scanned"] == 1
    assert report["total_findings"] > 0
    assert len(report["records"]) == report["total_findings"]


def test_review_fixtures_produce_role_aware_advisory_plans(tmp_path: Path) -> None:
    output = tmp_path / "review.json"
    result = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "scan",
            str(REVIEW_FIXTURES),
            "--format",
            "json",
            "--output",
            str(output),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    report = json.loads(output.read_text(encoding="utf-8"))
    records = report["records"]

    jwt = next(
        record for record in records
        if record["finding"]["location"]["file_path"].endswith("review_rsa_jwt_signing.py")
    )
    transport = next(
        record for record in records
        if record["finding"]["primitive_name"] == "RSA"
        and record["finding"]["location"]["file_path"].endswith("review_rsa_key_transport.py")
    )
    import_only = next(
        record for record in records
        if record["finding"]["location"]["file_path"].endswith("review_rsa_import_only.py")
    )

    assert jwt["finding"]["role"] == "signature"
    assert jwt["finding"]["protocol_context"] == "jwt"
    assert jwt["plan"]["target_algorithm"] == "ML-DSA assessment"
    assert jwt["plan"]["rule_id"] == "RSA-SIGNATURE-001"
    assert jwt["plan"]["rule_version"] == "2026.09.26-d7.1"
    assert jwt["plan"]["standard_refs"]
    assert jwt["plan"]["patch_available"] is False

    assert transport["finding"]["role"] == "key_transport"
    assert transport["plan"]["target_standard"] == "FIPS 203"
    assert transport["plan"]["rule_id"] == "RSA-KEY-TRANSPORT-001"
    assert transport["plan"]["blocker_codes"]
    assert transport["plan"]["patch_available"] is False

    assert import_only["finding"]["role"] == "unknown"
    assert import_only["plan"]["target_algorithm"] == "UNKNOWN"
    assert import_only["plan"]["patch_available"] is False
