import json
import subprocess
import sys
from pathlib import Path

import pytest

from pqc_migration_tool.scanner.external_triage import build_external_triage


def _sarif(uri: str, line: int, rule: str = "RSA-001") -> dict:
    return {
        "version": "2.1.0",
        "runs": [{
            "tool": {"driver": {"name": "fixture", "version": "1.0"}},
            "results": [{
                "ruleId": rule,
                "level": "warning",
                "message": {"text": "Review RSA use"},
                "locations": [{"physicalLocation": {
                    "artifactLocation": {"uri": uri},
                    "region": {"startLine": line, "startColumn": 5},
                }}],
            }],
        }],
    }


def test_external_leads_are_grouped_but_never_promoted(tmp_path: Path) -> None:
    root = tmp_path / "source"
    root.mkdir()
    (root / "main.go").write_text("package main\n// RSA\n", encoding="utf-8")
    cryptoscan = tmp_path / "cryptoscan.sarif"
    semgrep = tmp_path / "semgrep.sarif"
    cryptoscan.write_text(json.dumps(_sarif("main.go", 2)), encoding="utf-8")
    semgrep.write_text(json.dumps(_sarif("main.go", 2, "crypto-rsa")), encoding="utf-8")
    report = tmp_path / "pqmigrate.json"
    report.write_text(json.dumps({
        "source_commit": "a" * 40,
        "records": [{"finding": {
            "id": "known", "detection_type": "import_lead", "role": "unknown",
            "location": {"file_path": str(root / "main.go"), "line_number": 2},
        }}],
    }), encoding="utf-8")

    result = build_external_triage(root, [
        ("cryptoscan", cryptoscan), ("semgrep", semgrep)
    ], report)

    assert result["candidate_count"] == 1
    assert result["external_only_count"] == 0
    candidate = result["candidates"][0]
    assert {item["tool"] for item in candidate["external_evidence"]} == {"cryptoscan", "semgrep"}
    assert candidate["triage_class"] == "inventory_overlap"
    assert candidate["review_state"] == "unverified_external_lead"
    assert candidate["planning_eligible"] is False
    assert "plan" not in candidate and "operation" not in candidate


def test_external_only_candidate_is_prioritized_for_review(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("rsa.sign(data)\n", encoding="utf-8")
    sarif = tmp_path / "scan.sarif"
    sarif.write_text(json.dumps(_sarif("a.py", 1)), encoding="utf-8")
    result = build_external_triage(tmp_path, [("cryptoscan", sarif)])
    assert result["external_only_count"] == 1
    assert result["candidates"][0]["triage_class"] == "external_only"
    assert result["candidates"][0]["source_exists"] is True


def test_outside_root_location_is_skipped(tmp_path: Path) -> None:
    root = tmp_path / "source"
    root.mkdir()
    sarif = tmp_path / "scan.sarif"
    sarif.write_text(json.dumps(_sarif("../outside.py", 1)), encoding="utf-8")
    result = build_external_triage(root, [("cryptoscan", sarif)])
    assert result["candidate_count"] == 0
    assert result["inputs"][0]["skipped_results"] == 1


def test_invalid_sarif_fails_closed(tmp_path: Path) -> None:
    sarif = tmp_path / "bad.json"
    sarif.write_text(json.dumps({"version": "2.0.0", "runs": []}), encoding="utf-8")
    with pytest.raises(ValueError, match="Not SARIF"):
        build_external_triage(tmp_path, [("semgrep", sarif)])


def test_cli_external_triage_emits_read_only_json(tmp_path: Path) -> None:
    source = tmp_path / "sample.py"
    source.write_text("rsa.sign(data)\n", encoding="utf-8")
    sarif = tmp_path / "external.sarif"
    sarif.write_text(json.dumps(_sarif("sample.py", 1)), encoding="utf-8")
    cli = Path(__file__).parents[1] / "cli.py"
    completed = subprocess.run(
        [sys.executable, str(cli), "external-triage", str(tmp_path),
         "--sarif", f"cryptoscan={sarif}"],
        capture_output=True, text=True, check=False, timeout=10,
    )
    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert result["kind"] == "external_discovery_triage"
    assert result["candidate_count"] == 1
    assert source.read_text(encoding="utf-8") == "rsa.sign(data)\n"
