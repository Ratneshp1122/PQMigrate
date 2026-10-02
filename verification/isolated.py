"""D13 disposable-copy verification for a D12 transformation preview."""

from __future__ import annotations

import ast
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pqc_migration_tool.patcher.preview import (
    PREVIEW_VERSION,
    PreviewRequest,
    materialize_preview_bytes,
    preview_md5_to_sha256,
)


VERIFICATION_VERSION = "2026.10.02-d13.1"
DEFAULT_TIMEOUT_SECONDS = 10
MAX_TIMEOUT_SECONDS = 60


@dataclass(frozen=True)
class IsolatedVerificationRequest:
    project_root: Path
    source_path: Path
    expected_sha256: str
    line_number: int
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS


def _base_evidence(request: IsolatedVerificationRequest) -> dict[str, Any]:
    return {
        "schema_version": VERIFICATION_VERSION,
        "preview_schema_version": PREVIEW_VERSION,
        "status": "refused",
        "project_root": str(request.project_root),
        "source_path": str(request.source_path),
        "line_number": request.line_number,
        "timeout_seconds": request.timeout_seconds,
        "blocker_codes": [],
        "checks": {
            "preview_generated": False,
            "isolated_syntax_check": False,
            "ast_rescan": False,
            "original_source_unchanged": False,
            "isolated_copy_removed": False,
        },
        "test_command": None,
        "test_exit_code": None,
        "test_stdout": "",
        "test_stderr": "",
        "source_sha256_before": None,
        "source_sha256_after": None,
        "preview_sha256": None,
        "isolated_mutation_performed": False,
        "mutation_performed": False,
        "eligible_for_apply": False,
        "limitations": [
            "Isolation is a disposable filesystem copy, not an OS container or network sandbox.",
            "Only Python syntax and the selected AST replacement are checked.",
            "Project tests, runtime behavior, digest-size compatibility, and peers remain unverified.",
        ],
    }


def _direct_hash_calls(source: str, attribute: str, line: int) -> int:
    tree = ast.parse(source)
    return sum(
        1 for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == attribute
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "hashlib"
        and node.func.lineno == line
    )


def verify_preview_in_isolation(request: IsolatedVerificationRequest) -> dict[str, Any]:
    """Apply to a disposable copy, verify, rescan, and always remove the copy."""
    evidence = _base_evidence(request)
    if request.timeout_seconds < 1 or request.timeout_seconds > MAX_TIMEOUT_SECONDS:
        evidence["blocker_codes"] = ["D13_INVALID_TIMEOUT"]
        return evidence

    if request.project_root.is_symlink() or request.source_path.is_symlink():
        evidence["blocker_codes"] = ["D13_UNSAFE_SYMLINK_PATH"]
        return evidence
    root = request.project_root.resolve()
    source = request.source_path.resolve()
    if not root.is_dir():
        evidence["blocker_codes"] = ["D13_INVALID_PROJECT_ROOT"]
        return evidence
    try:
        relative_source = source.relative_to(root)
    except ValueError:
        evidence["blocker_codes"] = ["D13_SOURCE_OUTSIDE_PROJECT"]
        return evidence

    preview_request = PreviewRequest(source, request.expected_sha256, request.line_number)
    preview = preview_md5_to_sha256(preview_request)
    evidence["preview"] = preview.to_dict()
    evidence["source_sha256_before"] = preview.source_sha256
    evidence["preview_sha256"] = preview.preview_sha256
    if preview.status != "generated":
        evidence["blocker_codes"] = ["D13_PREVIEW_REFUSED", *preview.blocker_codes]
        return evidence
    evidence["checks"]["preview_generated"] = True
    preview_bytes = materialize_preview_bytes(preview_request, preview)
    if preview_bytes is None:
        evidence["blocker_codes"] = ["D13_PREVIEW_BINDING_CHANGED"]
        return evidence

    isolated_root = Path(tempfile.mkdtemp(prefix="pqmigrate-d13-"))
    isolated_target = isolated_root / relative_source
    try:
        isolated_target.parent.mkdir(parents=True, exist_ok=True)
        isolated_target.write_bytes(preview_bytes)
        evidence["isolated_mutation_performed"] = True
        evidence["test_command"] = [sys.executable, "-m", "py_compile", f"<isolated>/{relative_source.as_posix()}"]
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        try:
            completed = subprocess.run(
                [sys.executable, "-m", "py_compile", str(isolated_target)],
                cwd=isolated_root,
                env=environment,
                capture_output=True,
                text=True,
                timeout=request.timeout_seconds,
                check=False,
            )
            evidence["test_exit_code"] = completed.returncode
            evidence["test_stdout"] = completed.stdout[-4000:]
            evidence["test_stderr"] = completed.stderr[-4000:]
            evidence["checks"]["isolated_syntax_check"] = completed.returncode == 0
        except subprocess.TimeoutExpired:
            evidence["blocker_codes"] = ["D13_VERIFICATION_TIMEOUT"]
        except OSError:
            evidence["blocker_codes"] = ["D13_VERIFIER_START_FAILED"]

        if evidence["checks"]["isolated_syntax_check"]:
            transformed = isolated_target.read_text(encoding="utf-8")
            evidence["checks"]["ast_rescan"] = (
                _direct_hash_calls(transformed, "md5", request.line_number) == 0
                and _direct_hash_calls(transformed, "sha256", request.line_number) == 1
            )
            if not evidence["checks"]["ast_rescan"]:
                evidence["blocker_codes"] = ["D13_RESCAN_FAILED"]
    finally:
        shutil.rmtree(isolated_root, ignore_errors=True)
        evidence["checks"]["isolated_copy_removed"] = not isolated_root.exists()

    try:
        after = hashlib.sha256(source.read_bytes()).hexdigest()
    except OSError:
        after = None
    evidence["source_sha256_after"] = after
    evidence["checks"]["original_source_unchanged"] = after == preview.source_sha256
    if not evidence["checks"]["isolated_copy_removed"]:
        evidence["blocker_codes"] = ["D13_ROLLBACK_FAILED"]
    elif not evidence["checks"]["original_source_unchanged"]:
        evidence["blocker_codes"] = ["D13_ORIGINAL_SOURCE_CHANGED"]

    required = evidence["checks"]
    if all(required.values()) and not evidence["blocker_codes"]:
        evidence["status"] = "verified_bounded"
    elif not evidence["blocker_codes"]:
        evidence["status"] = "failed"
        evidence["blocker_codes"] = ["D13_VERIFICATION_INCOMPLETE"]
    else:
        evidence["status"] = "failed"
    return evidence
