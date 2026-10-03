import json
from pathlib import Path
ROOT=Path(__file__).parents[1]
def test_d17_validation_synchronizes_volatile_provenance():
    script=(ROOT/"scripts/run_d17_website.sh").read_text()
    assert script.index("sync_sample_summary.py") < script.index("test_d17_website.py")
def test_full_gate_orders_every_milestone_without_creating_git_tag():
    script=(ROOT/"scripts/validate_d0_d20.sh").read_text()
    expected=["validate_d0_d11.sh","run_d12_preview.sh","run_d13_verification.sh","run_d14_d15.sh","run_d16_dashboard.sh","run_d17_website.sh","run_d18_baselines.sh","run_d19_release_readiness.sh"]
    positions=[script.index(item) for item in expected]
    assert positions==sorted(positions)
    assert "git tag" not in script and "git push" not in script
def test_d20_document_states_local_not_production_deployment():
    text=(ROOT/"docs/review/d20-integration-release-gate.md").read_text()
    assert "not a production deployment" in text
    assert "d20-integration-summary.json" in text
