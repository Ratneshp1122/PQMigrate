"""Evaluate the bounded RSA resolver against PQMigrateBench v0.1."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from pqc_migration_tool.resolver.context_inference import infer_rsa_usage


DATASET_PATH = Path(__file__).with_name("pqmigratebench_v0_1.jsonl")
ALLOWED_SPLITS = {"train", "dev", "test"}
ALLOWED_ROLES = {"signature", "key_transport", "encryption", "unknown"}
ALLOWED_OPERATIONS = {"sign", "verify", "encrypt", "decrypt", "unknown"}
ALLOWED_CONTEXTS = {"jwt", "unknown"}
ALLOWED_CONFIDENCE = {"direct", "inferred", "ambiguous"}


class BenchmarkError(ValueError):
    """Raised when benchmark input is malformed or inconsistent."""


def load_cases(path: str | Path = DATASET_PATH) -> list[dict]:
    source = Path(path)
    cases: list[dict] = []
    seen: set[str] = set()
    for line_number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            case = json.loads(line)
        except json.JSONDecodeError as exc:
            raise BenchmarkError(f"Invalid JSONL at line {line_number}: {exc.msg}.") from exc
        _validate_case(case, line_number, seen)
        seen.add(case["id"])
        cases.append(case)
    if not 60 <= len(cases) <= 100:
        raise BenchmarkError(f"Pilot benchmark must contain 60-100 cases; found {len(cases)}.")
    if {case["split"] for case in cases} != ALLOWED_SPLITS:
        raise BenchmarkError("Dataset must contain train, dev, and test splits.")
    return cases


def _validate_case(case: object, line_number: int, seen: set[str]) -> None:
    if not isinstance(case, dict):
        raise BenchmarkError(f"Line {line_number} must be a JSON object.")
    required = {"benchmark_version", "id", "split", "language", "scope", "category", "accounting", "label_status", "source", "gold", "rationale"}
    missing = required - case.keys()
    if missing:
        raise BenchmarkError(f"Case on line {line_number} is missing {sorted(missing)}.")
    if case["id"] in seen:
        raise BenchmarkError(f"Duplicate case id: {case['id']}.")
    if case["split"] not in ALLOWED_SPLITS:
        raise BenchmarkError(f"Unsupported split in {case['id']}: {case['split']}.")
    if case["language"] != "python" or case["scope"] != "bounded_rsa_role_inference":
        raise BenchmarkError(f"Case {case['id']} is outside the D9 scope.")
    if case["accounting"] not in {"evaluated", "parse_failure"}:
        raise BenchmarkError(f"Unsupported accounting class in {case['id']}.")
    if not isinstance(case["source"], str) or not case["source"].strip():
        raise BenchmarkError(f"Case {case['id']} requires source text.")
    gold = case["gold"]
    if not isinstance(gold, dict) or set(gold) != {"is_operation", "role", "operation", "protocol_context", "confidence"}:
        raise BenchmarkError(f"Case {case['id']} has an invalid gold object.")
    if not isinstance(gold["is_operation"], bool):
        raise BenchmarkError(f"Case {case['id']} gold.is_operation must be boolean.")
    enum_checks = (
        ("role", ALLOWED_ROLES),
        ("operation", ALLOWED_OPERATIONS),
        ("protocol_context", ALLOWED_CONTEXTS),
        ("confidence", ALLOWED_CONFIDENCE),
    )
    for field, allowed in enum_checks:
        if gold[field] not in allowed:
            raise BenchmarkError(f"Case {case['id']} has unsupported gold.{field}: {gold[field]}.")
    if not gold["is_operation"] and (gold["role"] != "unknown" or gold["operation"] != "unknown"):
        raise BenchmarkError(f"Non-operation case {case['id']} must use unknown role and operation.")


def _ratio(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 6) if denominator else None


def _metrics(predictions: Iterable[dict]) -> dict:
    rows = [row for row in predictions if row["accounting"] == "evaluated"]
    tp = sum(row["gold"]["is_operation"] and row["predicted"]["is_operation"] for row in rows)
    fp = sum(not row["gold"]["is_operation"] and row["predicted"]["is_operation"] for row in rows)
    fn = sum(row["gold"]["is_operation"] and not row["predicted"]["is_operation"] for row in rows)
    tn = sum(not row["gold"]["is_operation"] and not row["predicted"]["is_operation"] for row in rows)
    precision = _ratio(tp, tp + fp)
    recall = _ratio(tp, tp + fn)
    f1 = None if precision is None or recall is None or precision + recall == 0 else round(2 * precision * recall / (precision + recall), 6)

    gold_operations = [row for row in rows if row["gold"]["is_operation"]]
    answered = [row for row in gold_operations if row["predicted"]["is_operation"]]
    correct_role = sum(row["predicted"]["role"] == row["gold"]["role"] for row in answered)
    end_to_end_role = sum(row["predicted"]["role"] == row["gold"]["role"] for row in gold_operations)
    return {
        "case_count": len(rows),
        "operation_detection": {
            "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "precision": precision, "recall": recall, "f1": f1,
        },
        "role_resolution": {
            "gold_operations": len(gold_operations),
            "answered": len(answered),
            "correct_among_answered": correct_role,
            "answer_coverage": _ratio(len(answered), len(gold_operations)),
            "accuracy_among_answered": _ratio(correct_role, len(answered)),
            "end_to_end_role_accuracy": _ratio(end_to_end_role, len(gold_operations)),
        },
        "negative_control_specificity": _ratio(tn, tn + fp),
    }


def _git_commit(root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=False, timeout=3,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    value = result.stdout.strip()
    return value if result.returncode == 0 and len(value) == 40 else None


def evaluate(path: str | Path = DATASET_PATH, selected_split: str = "all") -> dict:
    dataset_path = Path(path).resolve()
    cases = load_cases(dataset_path)
    if selected_split != "all" and selected_split not in ALLOWED_SPLITS:
        raise BenchmarkError(f"split must be one of all, train, dev, test; got {selected_split}.")
    selected = cases if selected_split == "all" else [case for case in cases if case["split"] == selected_split]
    predictions = []
    for case in selected:
        result = infer_rsa_usage(case["source"], f"{case['id']}.py")
        predicted = {
            "is_operation": result.role.value != "unknown",
            "role": result.role.value,
            "operation": result.operation.value,
            "protocol_context": result.protocol_context.value,
            "confidence": result.confidence.value,
            "evidence": result.evidence,
            "evidence_line": result.evidence_line,
        }
        mismatches = []
        if case["accounting"] == "evaluated":
            if predicted["is_operation"] != case["gold"]["is_operation"]:
                mismatches.append("operation_presence")
            if case["gold"]["is_operation"] and predicted["role"] != case["gold"]["role"]:
                mismatches.append("role")
            if case["gold"]["is_operation"] and predicted["operation"] != case["gold"]["operation"]:
                mismatches.append("operation")
            if case["gold"]["protocol_context"] != "unknown" and predicted["protocol_context"] != case["gold"]["protocol_context"]:
                mismatches.append("protocol_context")
        predictions.append({
            "id": case["id"], "split": case["split"], "category": case["category"],
            "accounting": case["accounting"], "gold": case["gold"],
            "predicted": predicted, "mismatches": mismatches,
        })

    dataset_bytes = dataset_path.read_bytes()
    metrics_by_split = {
        split: _metrics(row for row in predictions if row["split"] == split)
        for split in sorted({row["split"] for row in predictions})
    }
    errors = [row for row in predictions if row["mismatches"]]
    return {
        "benchmark_version": cases[0]["benchmark_version"],
        "dataset_sha256": hashlib.sha256(dataset_bytes).hexdigest(),
        "dataset_case_count": len(cases),
        "selected_split": selected_split,
        "evaluated_case_count": len(predictions),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evaluator_commit": _git_commit(dataset_path.parents[1]),
        "label_status": "single_author_synthetic_pilot",
        "scope": "Python bounded RSA role inference only; not product-wide accuracy.",
        "split_counts": dict(sorted(Counter(case["split"] for case in cases).items())),
        "category_counts": dict(sorted(Counter(case["category"] for case in cases).items())),
        "parse_failure_count": sum(row["accounting"] == "parse_failure" for row in predictions),
        "metrics": _metrics(predictions),
        "metrics_by_split": metrics_by_split,
        "error_count": len(errors),
        "errors": errors,
        "predictions": predictions,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default=str(DATASET_PATH))
    parser.add_argument("--split", default="all", choices=["all", "train", "dev", "test"])
    parser.add_argument("--output", help="Write full JSON results to this path.")
    args = parser.parse_args()
    report = evaluate(args.dataset, args.split)
    payload = json.dumps(report, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(payload, encoding="utf-8")
    summary = report["metrics"]
    print(f"Benchmark: {report['benchmark_version']} ({report['evaluated_case_count']} selected cases)")
    print(f"Label status: {report['label_status']}")
    print(f"Operation detection: {summary['operation_detection']}")
    print(f"Role resolution: {summary['role_resolution']}")
    print(f"Errors: {report['error_count']} (full raw predictions in JSON output)")


if __name__ == "__main__":
    main()

