#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fixture="$project_root/tests/fixtures/d12_direct_md5.py"
artifact_dir="$project_root/review-artifacts/latest"
before="$(sha256sum "$fixture" | awk '{print $1}')"

mkdir -p "$artifact_dir"
cd "$project_root/.."
python3 -m pytest -q pqc_migration_tool/tests/test_d12_preview.py
python3 pqc_migration_tool/cli.py preview "$fixture" \
  --expected-sha256 "$before" \
  --line 5 \
  --output "$artifact_dir/d12-preview.json" \
  --diff-output "$artifact_dir/d12-preview.diff" >/dev/null

after="$(sha256sum "$fixture" | awk '{print $1}')"
test "$before" = "$after"
echo "D12 PASS: tests passed, artifacts generated, source unchanged ($after)"
