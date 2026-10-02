import pytest
from pqc_migration_tool.lab.d14_interop import SCENARIOS, run_exchange, run_interop_lab

def test_matching_migrated_peers_negotiate_sha256():
    result = run_exchange(SCENARIOS[1])
    assert result["success"] and result["selected_mode"] == "sha256"
    assert result["digest_bytes"] == 32 and result["expectation_met"]

def test_mismatched_peers_fail_visibly():
    result = run_exchange(SCENARIOS[4])
    assert not result["success"] and result["status"] == "no_common_mode"
    assert result["selected_mode"] is None and result["expectation_met"]

def test_bad_digest_fails_visibly():
    result = run_exchange(SCENARIOS[5])
    assert not result["success"] and result["status"] == "digest_mismatch"

def test_repeated_matrix_records_denominators_and_environment():
    report = run_interop_lab(3)
    assert report["status"] == "pass_bounded" and report["total_samples"] == len(SCENARIOS) * 3
    assert report["roadmap_hybrid_matrix_completed"] is False
    assert all(row["sample_count"] == 3 and row["expectations_met"] for row in report["summaries"])
    assert report["environment"]["python"] and "PQC or hybrid KEM interoperability" in report["not_claimed"]

def test_invalid_repeat_count_refuses():
    with pytest.raises(ValueError, match="1..1000"):
        run_interop_lab(0)
