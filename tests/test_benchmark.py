import json
from pathlib import Path

import pytest

from pqc_migration_tool.benchmarks.build_dataset import build_cases
from pqc_migration_tool.benchmarks.evaluate import BenchmarkError, evaluate, load_cases


DATASET = Path(__file__).parents[1] / "benchmarks" / "pqmigratebench_v0_1.jsonl"


def test_dataset_is_versioned_unique_and_has_held_out_splits() -> None:
    cases = load_cases(DATASET)

    assert len(cases) == 72
    assert {case["benchmark_version"] for case in cases} == {"pqmigratebench-0.1.0"}
    assert len({case["id"] for case in cases}) == 72
    assert {case["split"] for case in cases} == {"train", "dev", "test"}
    assert all(case["label_status"] == "single_author_synthetic_pilot" for case in cases)
    assert any(case["gold"]["role"] == "unknown" for case in cases)
    assert any(case["category"] == "unsupported_valid_operation" for case in cases)


def test_committed_jsonl_matches_the_reviewable_generator() -> None:
    assert load_cases(DATASET) == build_cases()


def test_evaluator_emits_raw_predictions_metrics_and_errors() -> None:
    report = evaluate(DATASET)

    assert report["dataset_case_count"] == 72
    assert report["evaluated_case_count"] == 72
    assert len(report["dataset_sha256"]) == 64
    assert len(report["predictions"]) == 72
    assert report["parse_failure_count"] == 4
    assert report["error_count"] > 0
    assert report["metrics"]["operation_detection"]["fn"] > 0
    assert report["metrics"]["role_resolution"]["answer_coverage"] < 1.0
    assert set(report["metrics_by_split"]) == {"train", "dev", "test"}


def test_test_split_is_evaluated_without_train_or_dev_rows() -> None:
    report = evaluate(DATASET, "test")

    assert report["selected_split"] == "test"
    assert {row["split"] for row in report["predictions"]} == {"test"}
    assert report["evaluated_case_count"] == report["split_counts"]["test"]


def test_loader_rejects_duplicate_ids(tmp_path: Path) -> None:
    first = DATASET.read_text(encoding="utf-8").splitlines()[0]
    path = tmp_path / "duplicate.jsonl"
    path.write_text("\n".join([first] * 60) + "\n", encoding="utf-8")

    with pytest.raises(BenchmarkError, match="Duplicate case id"):
        load_cases(path)


def test_loader_rejects_too_small_dataset(tmp_path: Path) -> None:
    cases = DATASET.read_text(encoding="utf-8").splitlines()[:3]
    path = tmp_path / "small.jsonl"
    path.write_text("\n".join(cases) + "\n", encoding="utf-8")

    with pytest.raises(BenchmarkError, match="60-100"):
        load_cases(path)

