#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_root"
python3 -m pytest -q tests/test_benchmark.py tests/test_d18_baselines.py
cd "$(dirname "$repo_root")"
python3 -m pqc_migration_tool.experiments.run_baselines --dataset "$repo_root/benchmarks/pqmigratebench_v0_1.jsonl" --output "$repo_root/review-artifacts/latest/d18-baselines.json"
echo "D18 evidence: review-artifacts/latest/d18-baselines.json"
