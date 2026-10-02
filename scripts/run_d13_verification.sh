#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fixture="$project_root/tests/fixtures/d12_direct_md5.py"
artifact="$project_root/review-artifacts/latest/d13-verification.json"
before="$(sha256sum "$fixture" | awk '{print $1}')"
python_bin="python3"
if [[ -x "$project_root/../venv/bin/python3" ]]; then
  python_bin="$project_root/../venv/bin/python3"
fi

cd "$project_root/.."
"$python_bin" -m pytest -q \
  pqc_migration_tool/tests/test_d12_preview.py \
  pqc_migration_tool/tests/test_d13_isolated.py
"$python_bin" pqc_migration_tool/cli.py verify-preview "$fixture" \
  --project-root "$project_root" \
  --expected-sha256 "$before" \
  --line 5 \
  --timeout 10 \
  --output "$artifact" >/dev/null

after="$(sha256sum "$fixture" | awk '{print $1}')"
test "$before" = "$after"
echo "D13 PASS: disposable verification passed, rollback confirmed, source unchanged ($after)"
