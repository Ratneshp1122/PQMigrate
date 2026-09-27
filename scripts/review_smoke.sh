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
"$python_bin" -m pytest -q pqc_migration_tool/tests 2>&1 | tee "$artifact_dir/python-pytest.log"
"$python_bin" pqc_migration_tool/tests/test_scanner.py 2>&1 | tee "$artifact_dir/day5-scanner-checks.log"

cd "$repo_root"
bash scripts/run_benchmark.sh

cd "$repo_root/backend"
mvn test 2>&1 | tee "$artifact_dir/backend-maven-test.log"

cd "$repo_root/frontend"
npm run build 2>&1 | tee "$artifact_dir/frontend-build.log"

cd "$repo_root"
set +e
"$python_bin" cli.py scan tests/fixtures/review \
  --format json \
  --output "$artifact_dir/three-fixture-report.json" \
  2>&1 | tee "$artifact_dir/three-fixture-scan.log"
scanner_status=${PIPESTATUS[0]}
set -e
if [[ "$scanner_status" -ne 1 ]]; then
  echo "Expected scanner policy exit code 1, received $scanner_status" >&2
  exit 1
fi

"$python_bin" - "$artifact_dir/three-fixture-report.json" <<'PY'
import json
import sys

report = json.load(open(sys.argv[1], encoding="utf-8"))
assert report["schema_version"] == "2.2"
assert report["rules_version"] == "2026.09.26-d7.1"
assert len(report["source_commit"]) == 40
roles = {record["finding"]["role"] for record in report["records"]}
assert {"signature", "key_transport", "unknown"}.issubset(roles)
assert all(record["plan"]["patch_available"] is False for record in report["records"])
assert all(record["plan"]["rule_id"] for record in report["records"])
assert all(record["plan"]["decision_trace"]["trace_id"] for record in report["records"])
assert all(record["plan"]["decision_trace"]["source_ref"]["source_commit"] == report["source_commit"] for record in report["records"])
assert all(len(record["plan"]["decision_trace"]["steps"]) == 5 for record in report["records"])
assert all(record["plan"]["priority"]["data_exposure"] == "unknown" for record in report["records"])
assert any(record["plan"]["decision_trace"]["outcome"] == "abstain" for record in report["records"])
print("Validated role coverage, D8 decision traces, priority axes, and advisory-only plans.")
PY

git diff --check
{
  git rev-parse HEAD
  git status --short --branch
  "$python_bin" --version
  "$python_bin" -m pytest --version
  java -version
  mvn -version
  node --version
  npm --version
} 2>&1 | tee "$artifact_dir/baseline-metadata.log"

echo "Review smoke suite completed successfully."
