"""
Python AST-Based Crypto Scanner
==================================
Walks Python source files using the ast module.
Detects: import statements, function calls, attribute accesses.

Usage:
  from pqc_migration_tool.scanner.python_scanner import scan_file, scan_directory
"""

import ast
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

from .patterns import (
    ATTRIBUTE_PATTERNS,
    CALL_PATTERNS,
    IMPORT_PATTERNS,
    Pattern,
    Risk,
    RISK_ORDER,
)


# ── Finding dataclass ──────────────────────────────────────────────────────────
@dataclass
class Finding:
    filepath:   str
    line:       int
    col:        int
    match_type: str     # "import" | "from_import" | "call" | "attribute"
    match_text: str     # The source text that triggered this
    pattern:    Pattern

    @property
    def is_vulnerable(self) -> bool:
        return self.pattern.risk != Risk.SAFE

    @property
    def risk_score(self) -> int:
        """Numeric score for sorting/aggregation."""
        return {Risk.CRITICAL: 100, Risk.HIGH: 70,
                Risk.MEDIUM: 40, Risk.SAFE: 0}[self.pattern.risk]

    def as_dict(self) -> dict:
        return {
            "file":         self.filepath,
            "line":         self.line,
            "primitive":    self.pattern.name,
            "family":       self.pattern.family.value,
            "risk":         self.pattern.risk.value,
            "harvest_risk": self.pattern.harvest_risk,
            "replacement":  self.pattern.replacement,
            "guidance":     self.pattern.guidance,
            "match_type":   self.match_type,
            "match_text":   self.match_text,
        }


# ── AST visitor ───────────────────────────────────────────────────────────────
class _CryptoVisitor(ast.NodeVisitor):
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.findings: list[Finding] = []
        # name_to_module: local name → full import path (for call detection)
        self._name_to_module: dict[str, str] = {}

    # ── Import detection ───────────────────────────────────────────────────────

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            module = alias.name
            local  = alias.asname or alias.name.split(".")[0]
            self._name_to_module[local] = module
            self._check_import(module, node.lineno, node.col_offset,
                               f"import {module}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        module = node.module or ""
        for alias in node.names:
            name       = alias.name
            local      = alias.asname or name
            full_path  = f"{module}.{name}"

            # Register for later call detection
            self._name_to_module[local] = full_path

            # Try most-specific path first, then parent module
            matched = self._check_import(
                full_path, node.lineno, node.col_offset,
                f"from {module} import {name}")
            if not matched:
                self._check_import(
                    module, node.lineno, node.col_offset,
                    f"from {module} import {name}")
        self.generic_visit(node)

    def _check_import(self, module: str, line: int, col: int,
                      text: str) -> bool:
        """Check module string against pattern registry. Returns True if matched."""
        # Exact match
        if module in IMPORT_PATTERNS:
            self._add(IMPORT_PATTERNS[module], line, col, "import", text)
            return True
        # Prefix match — catches e.g. "cryptography.hazmat.primitives.asymmetric.rsa.RSAPrivateKey"
        for key in IMPORT_PATTERNS:
            if module.startswith(key + ".") or module == key:
                self._add(IMPORT_PATTERNS[key], line, col, "import", text)
                return True
        return False

    # ── Call detection (hashlib.md5(), etc.) ──────────────────────────────────

    def visit_Call(self, node: ast.Call):
        call_str = self._node_to_str(node.func)
        if call_str:
            # Direct check against call patterns
            for key, pattern in CALL_PATTERNS.items():
                if call_str == key or call_str.startswith(key + "("):
                    self._add(pattern, node.lineno, node.col_offset,
                              "call", call_str + "()")
                    break
            # Resolve via import aliases (e.g., imported hashlib → local name "h")
            # and check if the resolved name is a known pattern
            parts = call_str.split(".")
            if parts[0] in self._name_to_module:
                resolved = self._name_to_module[parts[0]]
                if len(parts) > 1:
                    resolved_full = resolved + "." + ".".join(parts[1:])
                    self._check_import(resolved, node.lineno, node.col_offset,
                                       call_str + "()")
        self.generic_visit(node)

    # ── Attribute detection (ssl.PROTOCOL_TLSv1, etc.) ───────────────────────

    def visit_Attribute(self, node: ast.Attribute):
        attr_str = self._node_to_str(node)
        if attr_str and attr_str in ATTRIBUTE_PATTERNS:
            self._add(ATTRIBUTE_PATTERNS[attr_str], node.lineno,
                      node.col_offset, "attribute", attr_str)
        self.generic_visit(node)

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _node_to_str(node: ast.expr) -> str:
        """Convert an AST node to its dotted string representation."""
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            parent = _CryptoVisitor._node_to_str(node.value)
            return f"{parent}.{node.attr}" if parent else node.attr
        return ""

    def _add(self, pattern: Pattern, line: int, col: int,
             match_type: str, text: str):
        """Add a finding, deduplicating by primitive name per file.
        Each distinct crypto primitive is reported once (first occurrence)."""
        for existing in self.findings:
            if existing.pattern.name == pattern.name:
                return  # already reported this primitive for this file
        self.findings.append(Finding(
            filepath=self.filepath,
            line=line,
            col=col,
            match_type=match_type,
            match_text=text,
            pattern=pattern,
        ))


# ── Public API ────────────────────────────────────────────────────────────────

def scan_file(filepath: str) -> list[Finding]:
    """Scan a single Python file. Returns list of findings."""
    try:
        source = Path(filepath).read_text(encoding="utf-8", errors="replace")
        tree   = ast.parse(source, filename=filepath)
    except (SyntaxError, OSError):
        return []
    visitor = _CryptoVisitor(filepath)
    visitor.visit(tree)
    # Sort: vulnerable first, then by line number
    return sorted(
        visitor.findings,
        key=lambda f: (RISK_ORDER[f.pattern.risk], f.line)
    )


def scan_directory(
    root: str,
    exclude_dirs:    set[str] | None = None,
    exclude_files:   set[str] | None = None,
    max_files:       int = 50_000,
    progress:        "ScanProgress | None" = None,
    stats:           "ScanStats | None"    = None,
    respect_gitignore: bool = True,
) -> list[Finding]:
    """
    Recursively scan all .py files under root.
    Returns all findings, sorted by risk then file then line.

    NEW in Day 4:
      - respect_gitignore: skip files/dirs listed in .gitignore
      - ALWAYS_IGNORE_DIRS: skip vendor/, node_modules/, etc. unconditionally
      - MAX_FILE_BYTES: skip minified/generated files > 1 MB
      - progress: live display callback
      - stats: accumulate scan statistics
    """
    from .gitignore import (
        build_multi_ruleset, ALWAYS_IGNORE_DIRS,
        ALWAYS_IGNORE_EXTENSIONS, MAX_FILE_BYTES
    )

    exclude_dirs  = (exclude_dirs or set()) | ALWAYS_IGNORE_DIRS
    exclude_files = exclude_files or set()
    gitignore     = build_multi_ruleset(root) if respect_gitignore else None

    all_findings: list[Finding] = []
    count = 0

    for dirpath, dirnames, filenames in os.walk(root):
        # Prune: always-ignore dirs + gitignore dirs
        pruned = []
        for d in dirnames:
            if d in exclude_dirs:
                continue
            dpath = os.path.join(dirpath, d)
            if gitignore and gitignore.is_ignored(dpath, is_dir=True):
                continue
            pruned.append(d)
        dirnames[:] = pruned

        for fname in sorted(filenames):
            if not fname.endswith(".py"):
                continue
            if fname in exclude_files:
                continue
            # Skip unwanted extensions (e.g. .pyc edge cases)
            _, ext = os.path.splitext(fname)
            if ext in ALWAYS_IGNORE_EXTENSIONS:
                continue

            fpath = os.path.join(dirpath, fname)

            # Gitignore check
            if gitignore and gitignore.is_ignored(fpath, is_dir=False):
                if stats:
                    stats.record_skip(fpath, "gitignore")
                continue

            # Size guard — skip huge generated files
            try:
                if os.path.getsize(fpath) > MAX_FILE_BYTES:
                    if stats:
                        stats.record_skip(fpath, "too large (>1MB)")
                    continue
            except OSError:
                continue

            findings = scan_file(fpath)
            all_findings.extend(findings)

            if progress:
                progress.update(fpath, len(findings))
            if stats:
                stats.record_file(fpath, len(findings))

            count += 1
            if count >= max_files:
                break
        if count >= max_files:
            break

    return sorted(all_findings,
                  key=lambda f: (RISK_ORDER[f.pattern.risk], f.filepath, f.line))


def iter_python_files(
    root:             str,
    exclude_dirs:     set[str] | None = None,
    respect_gitignore: bool = True,
) -> "Iterator[str]":
    """Yield all .py file paths under root, respecting gitignore."""
    from .gitignore import build_multi_ruleset, ALWAYS_IGNORE_DIRS, MAX_FILE_BYTES

    exclude_dirs = (exclude_dirs or set()) | ALWAYS_IGNORE_DIRS
    gitignore    = build_multi_ruleset(root) if respect_gitignore else None

    for dirpath, dirnames, filenames in os.walk(root):
        pruned = []
        for d in dirnames:
            if d in exclude_dirs:
                continue
            dpath = os.path.join(dirpath, d)
            if gitignore and gitignore.is_ignored(dpath, is_dir=True):
                continue
            pruned.append(d)
        dirnames[:] = pruned

        for fname in filenames:
            if not fname.endswith(".py"):
                continue
            fpath = os.path.join(dirpath, fname)
            if gitignore and gitignore.is_ignored(fpath, is_dir=False):
                continue
            try:
                if os.path.getsize(fpath) > MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            yield fpath


# Lazy import guard for type hints only
try:
    from .progress import ScanProgress, ScanStats
except ImportError:
    ScanProgress = None  # type: ignore
    ScanStats    = None  # type: ignore

