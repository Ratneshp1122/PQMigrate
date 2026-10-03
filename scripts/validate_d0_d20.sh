#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "[D20] D0-D11"; bash scripts/validate_d0_d11.sh --strict
echo "[D20] D12"; bash scripts/run_d12_preview.sh
echo "[D20] D13"; bash scripts/run_d13_verification.sh
echo "[D20] D14-D15"; bash scripts/run_d14_d15.sh
echo "[D20] D16"; bash scripts/run_d16_dashboard.sh
echo "[D20] D17"; bash scripts/run_d17_website.sh
echo "[D20] D18"; bash scripts/run_d18_baselines.sh
echo "[D20] D19"; bash scripts/run_d19_release_readiness.sh
python3 - <<'PY'
import hashlib, json, subprocess
from datetime import datetime, timezone
from pathlib import Path
root=Path(".").resolve()
artifacts=["d0-d11-validation-summary.json","d12-preview.json","d13-verification.json","d14-interoperability.json","d15-dashboard-check.json","d16-dashboard-check.json","d17-website-check.json","d18-baselines.json","d19-release-readiness.json"]
digests={}
for name in artifacts:
    path=root/"review-artifacts/latest"/name
    if not path.is_file(): raise SystemExit(f"missing D20 artifact: {name}")
    digests[name]=hashlib.sha256(path.read_bytes()).hexdigest()
commit=subprocess.run(["git","rev-parse","HEAD"],capture_output=True,text=True,check=True).stdout.strip()
report={"schema_version":"2026.10.03-d20.1","generated_at":datetime.now(timezone.utc).isoformat(),"status":"pass","source_commit":commit,"validated_range":"D0-D20","artifact_sha256":digests,"deployment":{"cli":"local_wsl_validated","dashboard":"loopback_only","public_site":"local_static_preview","spring_backend":"tests_only","react_frontend":"production_build_only","public_hosting":"not_deployed"},"claim_boundaries":["Automatic mutation remains disabled.","D14 is digest-contract evidence, not PQC/hybrid interoperability.","D9/D18 use a single-author synthetic Python RSA pilot.","Passing this gate is not production security certification."]}
(root/"review-artifacts/latest/d20-integration-summary.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps(report,indent=2,sort_keys=True))
PY
echo "D0-D20 integration validation PASS"
