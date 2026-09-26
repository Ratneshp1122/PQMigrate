#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
artifact_dir="$repo_root/review-artifacts/latest"
mkdir -p "$artifact_dir"

cd "$(dirname "$repo_root")"
python3 -m pytest -q pqc_migration_tool/tests 2>&1 | tee "$artifact_dir/python-pytest.log"
python3 pqc_migration_tool/tests/test_scanner.py 2>&1 | tee "$artifact_dir/day5-scanner-checks.log"

cd "$repo_root/backend"
mvn test 2>&1 | tee "$artifact_dir/backend-maven-test.log"

cd "$repo_root/frontend"
npm run build 2>&1 | tee "$artifact_dir/frontend-build.log"

cd "$repo_root"
set +e
python3 cli.py scan tests/fixtures/review \
  --format json \
  --output "$artifact_dir/three-fixture-report.json" \
  2>&1 | tee "$artifact_dir/three-fixture-scan.log"
scanner_status=${PIPESTATUS[0]}
set -e
if [[ "$scanner_status" -ne 1 ]]; then
  echo "Expected scanner policy exit code 1, received $scanner_status" >&2
  exit 1
fi

python3 - "$artifact_dir/three-fixture-report.json" <<'PY'
import json
import sys

report = json.load(open(sys.argv[1], encoding="utf-8"))
assert report["schema_version"] == "2.1"
roles = {record["finding"]["role"] for record in report["records"]}
assert {"signature", "key_transport", "unknown"}.issubset(roles)
assert all(record["plan"]["patch_available"] is False for record in report["records"])
print("Validated role coverage and advisory-only plans.")
PY

git diff --check
{
  git rev-parse HEAD
  git status --short --branch
  python3 --version
  pytest --version
  java -version
  mvn -version
  node --version
  npm --version
} 2>&1 | tee "$artifact_dir/baseline-metadata.log"

echo "Review smoke suite completed successfully."
