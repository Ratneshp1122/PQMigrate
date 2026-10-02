#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m pytest -q tests/test_d17_website.py
node --check website/app.js
python3 - <<'PY'
import json
from pathlib import Path
out={"schema_version":"2026.10.02-d17.1","status":"pass","pages":7,"static_only":True,"uploads":False,"analytics":False,"hosting_status":"local_preview_only"}
Path("review-artifacts/latest/d17-website-check.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
PY
echo "Preview: python3 -m http.server 4173 --directory website"
