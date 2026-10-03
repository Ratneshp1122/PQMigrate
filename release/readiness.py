"""Generate D19 faculty-packet and v0.1 release-candidate readiness evidence."""
from __future__ import annotations
import argparse, json, subprocess
from datetime import datetime, timezone
from pathlib import Path
REQUIRED=["docs/review/d19-faculty-demo-packet.md","docs/review/d19-release-checklist.md","review-artifacts/latest/d0-d11-validation-summary.json","review-artifacts/latest/d12-preview.json","review-artifacts/latest/d13-verification.json","review-artifacts/latest/d14-interoperability.json","review-artifacts/latest/d16-dashboard-check.json","review-artifacts/latest/d17-website-check.json","review-artifacts/latest/d18-baselines.json"]

def _git(root,*args):
    result=subprocess.run(["git","-C",str(root),*args],capture_output=True,text=True,check=False,timeout=5)
    return result.stdout.strip() if result.returncode==0 else None

def assess(root):
    root=Path(root).resolve(); missing=[item for item in REQUIRED if not (root/item).is_file()]
    commit=_git(root,"rev-parse","HEAD"); dirty=(_git(root,"status","--porcelain") or "").splitlines()
    tag_target=_git(root,"rev-list","-n","1","v0.1.0"); tag_exists=tag_target is not None; blockers=[]
    if missing: blockers.append("D19_REQUIRED_EVIDENCE_MISSING")
    if dirty: blockers.append("D19_WORKTREE_NOT_CLEAN")
    if not tag_exists: blockers.append("D19_V0_1_TAG_NOT_CREATED")
    return {"schema_version":"2026.10.03-d19.1","generated_at":datetime.now(timezone.utc).isoformat(),"packet_ready":not missing,"release_eligible":not blockers,"tag_name":"v0.1.0","tag_created":tag_exists,"tag_target":tag_target,"source_commit":commit,"dirty_path_count":len(dirty),"missing_files":missing,"blocker_codes":blockers,"status":"release_ready" if not blockers else ("packet_ready_release_pending" if not missing else "blocked")}

def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--root",default="."); parser.add_argument("--output"); args=parser.parse_args()
    report=assess(args.root); payload=json.dumps(report,indent=2,sort_keys=True)+"\n"
    if args.output: Path(args.output).write_text(payload,encoding="utf-8")
    print(payload,end="")
if __name__=="__main__": main()
