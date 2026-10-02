#!/usr/bin/env bash
set -euo pipefail
project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python_bin="python3"
if [[ -x "$project_root/../venv/bin/python3" ]]; then python_bin="$project_root/../venv/bin/python3"; fi
artifact_dir="$project_root/review-artifacts/latest"
cd "$project_root/.."
"$python_bin" -m pytest -q pqc_migration_tool/tests/test_d14_interop.py pqc_migration_tool/tests/test_d15_dashboard.py
"$python_bin" pqc_migration_tool/cli.py interop-lab --repeats 20 --output "$artifact_dir/d14-interoperability.json" >/dev/null
"$python_bin" pqc_migration_tool/cli.py dashboard --input "$artifact_dir/three-fixture-report.json" --source-root "$project_root" --check --output "$artifact_dir/d15-dashboard-check.json" >/dev/null
echo "D14 bounded + D15 PASS: selected compatibility matrix and offline read-only dashboard checks passed"
