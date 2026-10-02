#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m pytest -q tests/test_d15_dashboard.py tests/test_d16_dashboard.py
python3 cli.py dashboard --input review-artifacts/latest/three-fixture-report.json --check --output review-artifacts/latest/d16-dashboard-check.json
node --check dashboard/app.js
echo "D16 evidence: review-artifacts/latest/d16-dashboard-check.json"
