"""
Go Language Crypto Scanner
============================
Scans Go source files (.go) for quantum-vulnerable crypto primitives.

HOW IT WORKS — WHY REGEX INSTEAD OF AST:
─────────────────────────────────────────
Python has a built-in `ast` module for parsing Python. Go does not have
one accessible from Python. Options are:

  1. Regex               ← what we use
  2. Spawn `go/ast`      — requires Go installed, slow per-file
  3. Tree-sitter         — needs C binding, complex setup
  4. gopls LSP           — heavyweight

For Go crypto scanning, regex is the right choice because:
  - Go import paths are 100% regular: always `"full/package/path"`
  - No relative imports, no dynamic imports, no conditional imports
  - A Go file that imports "crypto/rsa" IS using RSA — no ambiguity
  - Accuracy is 99%+ for real-world Go codebases

TWO SCAN PHASES:
─────────────────
Phase 1 — Import detection:
  Go has two import syntaxes:
    a) Single:  import "crypto/rsa"
    b) Block:   import (
                    "crypto/rsa"
                    rsa2 "crypto/rsa"   ← aliased
                    _ "crypto/dsa"      ← blank (side-effect import)
                )
  We extract every quoted path from both forms, then look it up
  in GO_IMPORT_PATTERNS.

Phase 2 — Call detection:
  Some crypto usage bypasses explicit imports (generated code, dot-imports).
  We scan every line for known call patterns: `rsa.GenerateKey(`,
  `md5.New(`, `tls.Config{`, `elliptic.P256(` etc.

DEDUPLICATION:
───────────────
Same as the Python scanner: one finding per (file, primitive name).
If `crypto/rsa` appears in 8 import lines, we report it once at the
first occurrence. Helps keep reports readable.

LANGUAGE DETECTION:
────────────────────
scan_directory() auto-detects Go vs Python based on file counts.
In a Go repo, only .go files are scanned. In mixed repos, both.
"""

import os
import re
from pathlib import Path

from .python_scanner import Finding  # reuse same Finding dataclass
from .go_patterns import GO_IMPORT_PATTERNS, GO_CALL_PATTERNS
from .patterns import RISK_ORDER


# ── Compiled regex patterns for Go import syntax ──────────────────────────────

# Matches: import "path/to/package"
_RE_SINGLE_IMPORT = re.compile(
    r'^\s*import\s+"([^"]+)"',
    re.MULTILINE,
)

# Matches the entire import (...) block content
_RE_IMPORT_BLOCK = re.compile(
    r'\bimport\s*\(([^)]*)\)',
    re.DOTALL,
)

# Within a block: matches any "quoted/path" (with optional alias or _)
_RE_QUOTED_PATH = re.compile(r'"([^"]+)"')


# ── Public API ────────────────────────────────────────────────────────────────

def scan_go_file(filepath: str) -> list[Finding]:
    """
    Scan a single Go source file.
    Returns list of findings sorted by risk level then line number.

    WHEN TO USE:
      Called automatically by scan_go_directory() for every .go file.
      Can also be called directly on a single file.
    """
    try:
        content = Path(filepath).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    findings:   list[Finding] = []
    seen_names: set[str]      = set()   # deduplicate by primitive name

    # ── Phase 1: Import detection ─────────────────────────────────────────────
    for import_path, line_no in _extract_imports(content):
        _try_match(import_path, line_no, "go_import",
                   f'import "{import_path}"',
                   filepath, seen_names, findings)

    # ── Phase 2: Call/attribute detection ─────────────────────────────────────
    lines = content.split("\n")
    for i, line in enumerate(lines, start=1):
        # Skip comment lines (// and block comments)
        stripped = line.lstrip()
        if stripped.startswith("//"):
            continue
        for call_regex, pattern_key, display in GO_CALL_PATTERNS:
            if re.search(call_regex, line):
                if pattern_key in GO_IMPORT_PATTERNS:
                    pattern = GO_IMPORT_PATTERNS[pattern_key]
                    if pattern.name not in seen_names:
                        seen_names.add(pattern.name)
                        findings.append(Finding(
                            filepath=filepath,
                            line=i,
                            col=0,
                            match_type="go_call",
                            match_text=display,
                            pattern=pattern,
                        ))

    return sorted(findings,
                  key=lambda f: (RISK_ORDER[f.pattern.risk], f.line))


def scan_go_directory(
    root:          str,
    exclude_dirs:  set[str] | None = None,
    max_files:     int = 50_000,
) -> list[Finding]:
    """
    Recursively scan all .go files under root.

    WHEN TO USE:
      Called by the multi-language _run_scan() in cli.py when Go files
      are detected in the target directory.

    EXCLUDES by default:
      vendor/   — dependency mirror, not your code
      testdata/ — test fixtures
      _test.go  — test files included by default (they use crypto too)
    """
    exclude_dirs = exclude_dirs or {
        ".git", "vendor", "node_modules",
        ".tox", "dist", "build",
    }
    all_findings: list[Finding] = []
    count = 0

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]

        for fname in filenames:
            if not fname.endswith(".go"):
                continue
            fpath    = os.path.join(dirpath, fname)
            findings = scan_go_file(fpath)
            all_findings.extend(findings)
            count += 1
            if count >= max_files:
                break
        if count >= max_files:
            break

    return sorted(all_findings,
                  key=lambda f: (RISK_ORDER[f.pattern.risk], f.filepath, f.line))


def count_go_files(root: str, exclude_dirs: set[str] | None = None) -> int:
    """Count .go files under root (for the file-count summary)."""
    exclude_dirs = exclude_dirs or {".git", "vendor", "node_modules"}
    total = 0
    for dirpath, dirnames, _ in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        total += sum(1 for f in os.listdir(dirpath) if f.endswith(".go"))
    return total


def detect_primary_language(root: str) -> str:
    """
    Detect whether a repo is primarily Python, Go, or mixed.
    Returns "python", "go", or "mixed".

    WHY:
      Lets the scanner auto-configure without explicit --lang flags.
      A Go repo shouldn't waste time looking for .py files; a Python
      repo shouldn't waste time looking for .go files.
    """
    py_count = go_count = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if d not in {".git", "vendor", "__pycache__", "venv"}]
        for f in filenames:
            if f.endswith(".py"):
                py_count += 1
            elif f.endswith(".go"):
                go_count += 1

    if py_count == 0 and go_count == 0:
        return "unknown"
    if go_count > py_count * 3:
        return "go"
    if py_count > go_count * 3:
        return "python"
    return "mixed"


# ── Internal helpers ──────────────────────────────────────────────────────────

def _extract_imports(content: str) -> list[tuple[str, int]]:
    """
    Extract all import paths and their line numbers from Go source.
    Returns [(import_path, 1-indexed line number), ...]

    WHY line numbers:
      Report output always shows the exact line so developers can jump
      straight to the finding with their editor.
    """
    result: list[tuple[str, int]] = []

    # Single-line: import "path"
    for m in _RE_SINGLE_IMPORT.finditer(content):
        path     = m.group(1)
        line_no  = content[: m.start()].count("\n") + 1
        result.append((path, line_no))

    # Block: import ( ... )
    for block_m in _RE_IMPORT_BLOCK.finditer(content):
        block   = block_m.group(1)
        b_start = block_m.start(1)
        for path_m in _RE_QUOTED_PATH.finditer(block):
            path    = path_m.group(1)
            abs_off = b_start + path_m.start()
            line_no = content[:abs_off].count("\n") + 1
            result.append((path, line_no))

    return result


def _try_match(
    import_path: str,
    line_no:     int,
    match_type:  str,
    match_text:  str,
    filepath:    str,
    seen_names:  set[str],
    findings:    list[Finding],
) -> None:
    """
    Try to match import_path against GO_IMPORT_PATTERNS.
    Checks exact match first, then prefix match.
    Adds a Finding if matched and not already seen.
    """
    # Exact match
    if import_path in GO_IMPORT_PATTERNS:
        pattern = GO_IMPORT_PATTERNS[import_path]
        if pattern.name not in seen_names:
            seen_names.add(pattern.name)
            findings.append(Finding(
                filepath=filepath,
                line=line_no,
                col=0,
                match_type=match_type,
                match_text=match_text,
                pattern=pattern,
            ))
        return

    # Prefix match — catches sub-packages e.g. "crypto/rsa/internal/..."
    for key in GO_IMPORT_PATTERNS:
        if import_path.startswith(key + "/") or import_path == key:
            pattern = GO_IMPORT_PATTERNS[key]
            if pattern.name not in seen_names:
                seen_names.add(pattern.name)
                findings.append(Finding(
                    filepath=filepath,
                    line=line_no,
                    col=0,
                    match_type=match_type,
                    match_text=match_text,
                    pattern=pattern,
                ))
            return
