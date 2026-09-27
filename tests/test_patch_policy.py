import itertools
import json
from pathlib import Path
from unittest.mock import patch

from pqc_migration_tool.patcher.engine import PatcherEngine
from pqc_migration_tool.patcher.policy import PatchGate, TriState, assess_record, evaluate_gate
from pqc_migration_tool.patcher.policy_audit import build_audit
from pqc_migration_tool.verification.verifier import VerificationEngine


def test_all_243_tri_state_combinations_fail_closed() -> None:
    states = list(TriState)
    eligible = []
    for values in itertools.product(states, repeat=5):
        decision = evaluate_gate(PatchGate(*values))
        if decision.eligible:
            eligible.append(values)
        else:
            assert decision.blocker_codes
            assert any(value in {TriState.FALSE, TriState.UNKNOWN} for value in values)

    assert eligible == [(TriState.TRUE,) * 5]


def test_current_report_evidence_never_self_authorizes() -> None:
    record = {
        "finding": {"role": "signature"},
        "plan": {"patch_available": True, "requires_manual_intervention": False},
        "patch_eligibility": {
            "known_role": "true",
            "supported_construction": "true",
            "interoperable_peers": "true",
            "tests_available": "true",
            "operator_authorized": "true",
        },
    }
    decision = assess_record(record)

    assert decision.eligible is False
    assert decision.gate.known_role is TriState.TRUE
    assert decision.gate.supported_construction is TriState.UNKNOWN
    assert len(decision.blocker_codes) == 4


def test_legacy_patcher_cannot_mutate_from_report_claims(tmp_path: Path) -> None:
    target = tmp_path / "target.py"
    original = "import hashlib\ndigest = hashlib.md5(b'data').hexdigest()\n"
    target.write_text(original, encoding="utf-8")
    report = {
        "records": [
            {
                "finding": {
                    "primitive_name": "MD5",
                    "role": "hash",
                    "location": {"file_path": str(target), "line_number": 2},
                },
                "plan": {
                    "target_algorithm": "SHA-256",
                    "target_standard": "FIPS 180-4",
                    "patch_available": True,
                    "requires_manual_intervention": False,
                },
                "patch_eligibility": {name: "true" for name in PatchGate().__dict__},
            }
        ]
    }
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")

    PatcherEngine(str(report_path)).run()

    assert target.read_text(encoding="utf-8") == original
    assert not Path(f"{target}.bak").exists()


def test_missing_test_runner_fails_closed(tmp_path: Path) -> None:
    with patch("pqc_migration_tool.verification.verifier.subprocess.run", side_effect=FileNotFoundError):
        assert VerificationEngine(str(tmp_path)).run_tests() is False


def test_policy_audit_records_exact_invariant() -> None:
    audit = build_audit()

    assert audit["evaluated_combinations"] == 243
    assert audit["eligible_count"] == 1
    assert audit["ineligible_count"] == 242
    assert set(audit["eligible_vectors"][0].values()) == {"true"}
    assert audit["current_pipeline_mutation_enabled"] is False
    assert audit["report_supplied_eligibility_is_trusted"] is False
