#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_root"
python3 -m pytest -q tests/test_d19_release_packet.py
cd "$(dirname "$repo_root")"
python3 -m pqc_migration_tool.release.readiness --root "$repo_root" --output "$repo_root/review-artifacts/latest/d19-release-readiness.json"
echo "D19 packet validated; tag/release blockers remain explicit in the artifact."
