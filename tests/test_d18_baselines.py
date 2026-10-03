from pathlib import Path
from pqc_migration_tool.experiments.run_baselines import run
DATASET=Path(__file__).parents[1]/"benchmarks"/"pqmigratebench_v0_1.jsonl"

def test_all_baselines_use_identical_case_ids_and_denominators():
    report=run(DATASET); assert report["case_count"]==72
    assert set(report["systems"])=={"primitive_lookup","ast_call_only","no_session_secret_flow","no_protocol_context","full_pipeline"}
    ids=None
    for result in report["systems"].values():
        current=[row["id"] for row in result["predictions"]]
        if ids is None: ids=current
        assert current==ids and result["metrics"]["case_count"]==68

def test_baselines_expose_expected_tradeoffs_without_claim_inflation():
    systems=run(DATASET)["systems"]; primitive=systems["primitive_lookup"]["metrics"]["operation_detection"]; full=systems["full_pipeline"]["metrics"]["operation_detection"]
    assert primitive["recall"]>=full["recall"] and primitive["precision"]<=full["precision"]
    assert systems["no_session_secret_flow"]["metrics"]["role_resolution"]["end_to_end_role_accuracy"]<systems["full_pipeline"]["metrics"]["role_resolution"]["end_to_end_role_accuracy"]

def test_protocol_ablation_removes_jwt_context_only_from_claimed_dimension():
    systems=run(DATASET)["systems"]
    assert systems["full_pipeline"]["additional_metrics"]["protocol_context_accuracy"]==1.0
    assert systems["no_protocol_context"]["additional_metrics"]["protocol_context_accuracy"]==0.0
