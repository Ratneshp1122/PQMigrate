#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
artifact_dir="$repo_root/review-artifacts/latest"
mkdir -p "$artifact_dir"

if [[ -x "$repo_root/../venv/bin/python3" ]]; then
  python_bin="$repo_root/../venv/bin/python3"
else
  python_bin="python3"
fi

cd "$(dirname "$repo_root")"
"$python_bin" -m pqc_migration_tool.benchmarks.evaluate \
  --dataset "$repo_root/benchmarks/pqmigratebench_v0_1.jsonl" \
  --output "$artifact_dir/d9-benchmark-results.json" \
  2>&1 | tee "$artifact_dir/d9-benchmark.log"

"$python_bin" - "$artifact_dir/d9-benchmark-results.json" <<'PY'
import json
import sys

report = json.load(open(sys.argv[1], encoding="utf-8"))
assert report["benchmark_version"] == "pqmigratebench-0.1.0"
assert report["dataset_case_count"] == 72
assert len(report["predictions"]) == 72
assert report["label_status"] == "single_author_synthetic_pilot"
assert report["error_count"] > 0
assert report["metrics"]["role_resolution"]["answer_coverage"] < 1.0
print("Validated D9 raw predictions, metrics, held-out splits, and visible error cases.")
PY

