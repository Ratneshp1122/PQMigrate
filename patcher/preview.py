"""D12 preview-only, AST-aware source transformations.

This module deliberately has no source-write function.  It binds a preview to
the caller-supplied SHA-256 digest, selects a Python AST node, and returns an
exact unified diff plus machine-readable evidence.
"""

from __future__ import annotations

import ast
import difflib
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .policy import PatchGate, TriState, evaluate_gate


PREVIEW_VERSION = "2026.10.02-d12.1"
TRANSFORMATION_ID = "python.hashlib.md5-to-sha256.preview-v1"
MAX_SOURCE_BYTES = 1024 * 1024
_GENERATED_PARTS = {"vendor", "vendors", "node_modules", "dist", "build", "generated"}


@dataclass(frozen=True)
class PreviewRequest:
    source_path: Path
    expected_sha256: str
    line_number: int | None = None


@dataclass(frozen=True)
class PreviewResult:
    status: str
    source_path: str
    source_sha256: str | None
    expected_sha256: str
    line_number: int | None
    blocker_codes: tuple[str, ...]
    diff: str
    candidate_count: int
    selected_span: dict[str, int] | None
    preview_sha256: str | None
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        # A D12 preview is evidence for review, never authority to apply.
        mutation_decision = evaluate_gate(
            PatchGate(known_role=TriState.TRUE if self.status == "generated" else TriState.UNKNOWN)
        )
        return {
            "schema_version": PREVIEW_VERSION,
            "transformation_id": TRANSFORMATION_ID,
            "status": self.status,
            "source_path": self.source_path,
            "source_sha256": self.source_sha256,
            "expected_sha256": self.expected_sha256,
            "line_number": self.line_number,
            "candidate_count": self.candidate_count,
            "selected_span": self.selected_span,
            "preview_sha256": self.preview_sha256,
            "diff": self.diff,
            "blocker_codes": list(self.blocker_codes),
            "explanation": self.explanation,
            "mutation_performed": False,
            "eligible_for_apply": False,
            "mutation_policy": mutation_decision.to_dict(),
            "compatibility_warning": (
                "SHA-256 changes digest length and may break protocols, schemas, stored values, "
                "wire formats, peers, and tests. D12 does not establish interoperability."
            ),
        }


def _refused(request: PreviewRequest, code: str, explanation: str,
             source_sha256: str | None = None, candidate_count: int = 0) -> PreviewResult:
    return PreviewResult(
        status="refused",
        source_path=str(request.source_path),
        source_sha256=source_sha256,
        expected_sha256=request.expected_sha256,
        line_number=request.line_number,
        blocker_codes=(code,),
        diff="",
        candidate_count=candidate_count,
        selected_span=None,
        preview_sha256=None,
        explanation=explanation,
    )


def _is_generated_or_vendored(path: Path) -> bool:
    lowered = {part.lower() for part in path.parts}
    return bool(lowered & _GENERATED_PARTS) or path.name.lower().endswith("_generated.py")


def _hashlib_is_unambiguous(tree: ast.AST) -> bool:
    imported = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "hashlib" and alias.asname is None:
                    imported = True
        elif isinstance(node, ast.Name) and node.id == "hashlib" and isinstance(node.ctx, ast.Store):
            return False
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            args = (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs)
            if any(arg.arg == "hashlib" for arg in args):
                return False
            if node.args.vararg and node.args.vararg.arg == "hashlib":
                return False
            if node.args.kwarg and node.args.kwarg.arg == "hashlib":
                return False
    return imported


def _byte_offset(lines: list[str], line_number: int, column: int) -> int:
    return sum(len(line.encode("utf-8")) for line in lines[: line_number - 1]) + column


def preview_md5_to_sha256(request: PreviewRequest) -> PreviewResult:
    """Return a hash-bound preview or a fail-closed refusal; never modify source."""
    path = request.source_path
    expected = request.expected_sha256.lower()
    if len(expected) != 64 or any(ch not in "0123456789abcdef" for ch in expected):
        return _refused(request, "D12_INVALID_EXPECTED_SHA256", "Expected SHA-256 must be 64 hex characters.")
    if request.line_number is not None and request.line_number < 1:
        return _refused(request, "D12_INVALID_LINE", "Line number must be a positive integer.")
    if path.suffix.lower() != ".py":
        return _refused(request, "D12_UNSUPPORTED_FILE_TYPE", "Only Python .py files are supported by this preview.")
    if _is_generated_or_vendored(path):
        return _refused(request, "D12_GENERATED_OR_VENDORED_PATH", "Generated and vendored paths are outside D12 scope.")
    if not path.exists() or not path.is_file() or path.is_symlink():
        return _refused(request, "D12_UNSAFE_SOURCE_PATH", "Source must be an existing regular, non-symlink file.")

    try:
        source_bytes = path.read_bytes()
    except OSError:
        return _refused(request, "D12_SOURCE_READ_FAILED", "Source could not be read.")
    actual = hashlib.sha256(source_bytes).hexdigest()
    if actual != expected:
        return _refused(request, "D12_SOURCE_HASH_MISMATCH", "Source changed or the expected hash is incorrect.", actual)
    if len(source_bytes) > MAX_SOURCE_BYTES:
        return _refused(request, "D12_SOURCE_TOO_LARGE", "Source exceeds the 1 MiB D12 preview limit.", actual)
    try:
        source = source_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return _refused(request, "D12_SOURCE_NOT_UTF8", "D12 requires UTF-8 Python source.", actual)
    try:
        tree = ast.parse(source, filename=str(path))
    except (SyntaxError, ValueError):
        return _refused(request, "D12_PARSE_FAILED", "Python AST parsing failed; no preview was generated.", actual)
    if not _hashlib_is_unambiguous(tree):
        return _refused(request, "D12_AMBIGUOUS_HASHLIB_BINDING", "An exact, unshadowed 'import hashlib' is required.", actual)

    candidates = [
        node.func for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "md5"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "hashlib"
    ]
    if request.line_number is not None:
        selected = [node for node in candidates if node.lineno == request.line_number]
    else:
        selected = candidates
    if not candidates:
        return _refused(request, "D12_NO_SUPPORTED_CANDIDATE", "No direct hashlib.md5(...) call was found.", actual)
    if not selected:
        return _refused(request, "D12_LINE_HAS_NO_CANDIDATE", "The requested line has no supported candidate.", actual, len(candidates))
    if len(selected) != 1:
        return _refused(request, "D12_CANDIDATE_NOT_UNIQUE", "Select exactly one direct call with --line.", actual, len(candidates))

    node = selected[0]
    lines = source.splitlines(keepends=True)
    start = _byte_offset(lines, node.lineno, node.col_offset)
    end = _byte_offset(lines, node.end_lineno, node.end_col_offset)
    if source_bytes[start:end] != b"hashlib.md5":
        return _refused(request, "D12_SPAN_VALIDATION_FAILED", "AST source span did not match the expected token.", actual, len(candidates))
    preview_bytes = source_bytes[:start] + b"hashlib.sha256" + source_bytes[end:]
    preview = preview_bytes.decode("utf-8")
    diff = "".join(difflib.unified_diff(
        source.splitlines(keepends=True),
        preview.splitlines(keepends=True),
        fromfile=f"a/{path.name}",
        tofile=f"b/{path.name}",
    ))
    return PreviewResult(
        status="generated",
        source_path=str(path),
        source_sha256=actual,
        expected_sha256=expected,
        line_number=request.line_number,
        blocker_codes=("D12_APPLY_NOT_AUTHORIZED", "D12_INTEROPERABILITY_UNVERIFIED"),
        diff=diff,
        candidate_count=len(candidates),
        selected_span={
            "start_line": node.lineno,
            "start_column_utf8": node.col_offset,
            "end_line": node.end_lineno,
            "end_column_utf8": node.end_col_offset,
        },
        preview_sha256=hashlib.sha256(preview_bytes).hexdigest(),
        explanation="Preview generated from one exact AST-selected call; source was not modified.",
    )


def materialize_preview_bytes(request: PreviewRequest, result: PreviewResult) -> bytes | None:
    """Materialize an already-approved preview in memory after rechecking its binding.

    This helper never writes a file.  D13 uses it only for a disposable copy.
    Returning ``None`` is fail-closed if the source, hash, or selected span changed.
    """
    if result.status != "generated" or result.selected_span is None:
        return None
    try:
        source_bytes = request.source_path.read_bytes()
        source = source_bytes.decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    if hashlib.sha256(source_bytes).hexdigest() != result.source_sha256:
        return None
    span = result.selected_span
    lines = source.splitlines(keepends=True)
    start = _byte_offset(lines, span["start_line"], span["start_column_utf8"])
    end = _byte_offset(lines, span["end_line"], span["end_column_utf8"])
    if source_bytes[start:end] != b"hashlib.md5":
        return None
    preview_bytes = source_bytes[:start] + b"hashlib.sha256" + source_bytes[end:]
    if hashlib.sha256(preview_bytes).hexdigest() != result.preview_sha256:
        return None
    return preview_bytes
