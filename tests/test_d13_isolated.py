import hashlib
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from pqc_migration_tool.verification.isolated import (
    IsolatedVerificationRequest,
    verify_preview_in_isolation,
)


PROJECT = Path(__file__).parents[1]


def _project(tmp_path: Path) -> tuple[Path, Path, str]:
    root = tmp_path / "project"
    root.mkdir()
    source = root / "sample.py"
    source.write_text("import hashlib\ndigest = hashlib.md5(b'x').hexdigest()\n", encoding="utf-8")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    return root, source, digest


def test_isolated_verification_passes_and_preserves_original(tmp_path: Path) -> None:
    root, source, digest = _project(tmp_path)
    before = source.read_bytes()
    evidence = verify_preview_in_isolation(IsolatedVerificationRequest(root, source, digest, 2))
    assert evidence["status"] == "verified_bounded"
    assert all(evidence["checks"].values())
    assert evidence["isolated_mutation_performed"] is True
    assert evidence["mutation_performed"] is False
    assert evidence["eligible_for_apply"] is False
    assert source.read_bytes() == before


def test_source_outside_project_refuses(tmp_path: Path) -> None:
    root, _, _ = _project(tmp_path)
    outside = tmp_path / "outside.py"
    outside.write_text("import hashlib\nhashlib.md5(b'x')\n", encoding="utf-8")
    digest = hashlib.sha256(outside.read_bytes()).hexdigest()
    evidence = verify_preview_in_isolation(IsolatedVerificationRequest(root, outside, digest, 2))
    assert evidence["status"] == "refused"
    assert evidence["blocker_codes"] == ["D13_SOURCE_OUTSIDE_PROJECT"]


def test_refused_d12_preview_is_propagated(tmp_path: Path) -> None:
    root, source, _ = _project(tmp_path)
    evidence = verify_preview_in_isolation(IsolatedVerificationRequest(root, source, "0" * 64, 2))
    assert evidence["blocker_codes"][:2] == ["D13_PREVIEW_REFUSED", "D12_SOURCE_HASH_MISMATCH"]


def test_timeout_still_removes_isolated_copy_and_preserves_source(tmp_path: Path) -> None:
    root, source, digest = _project(tmp_path)
    before = source.read_bytes()
    with patch("pqc_migration_tool.verification.isolated.subprocess.run", side_effect=subprocess.TimeoutExpired("x", 1)):
        evidence = verify_preview_in_isolation(IsolatedVerificationRequest(root, source, digest, 2))
    assert evidence["status"] == "failed"
    assert evidence["blocker_codes"] == ["D13_VERIFICATION_TIMEOUT"]
    assert evidence["checks"]["isolated_copy_removed"] is True
    assert evidence["checks"]["original_source_unchanged"] is True
    assert source.read_bytes() == before


def test_invalid_timeout_refuses(tmp_path: Path) -> None:
    root, source, digest = _project(tmp_path)
    evidence = verify_preview_in_isolation(IsolatedVerificationRequest(root, source, digest, 2, 61))
    assert evidence["blocker_codes"] == ["D13_INVALID_TIMEOUT"]


def test_symlink_source_refuses(tmp_path: Path) -> None:
    root, source, digest = _project(tmp_path)
    link = root / "linked.py"
    try:
        link.symlink_to(source)
    except (OSError, NotImplementedError):
        return
    evidence = verify_preview_in_isolation(IsolatedVerificationRequest(root, link, digest, 2))
    assert evidence["blocker_codes"] == ["D13_UNSAFE_SYMLINK_PATH"]


def test_cli_generates_evidence_without_modifying_source(tmp_path: Path) -> None:
    root, source, digest = _project(tmp_path)
    before = source.read_bytes()
    output = tmp_path / "d13.json"
    completed = subprocess.run(
        [sys.executable, str(PROJECT / "cli.py"), "verify-preview", str(source),
         "--project-root", str(root), "--expected-sha256", digest,
         "--line", "2", "--output", str(output)],
        cwd=PROJECT.parent,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    evidence = json.loads(output.read_text(encoding="utf-8"))
    assert evidence["status"] == "verified_bounded"
    assert evidence["checks"]["isolated_copy_removed"] is True
    assert source.read_bytes() == before
