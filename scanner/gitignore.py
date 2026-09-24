"""
gitignore.py — Lightweight .gitignore rule parser
===================================================

WHY we need this:
  Large repos (Kubernetes ~100k files, Vault ~50k) contain massive
  vendor/, generated/, and test-fixture directories. Without respecting
  .gitignore, our scanner wastes 80%+ of its time on non-authored code.
  vendor/ alone in a Go repo can be 10x the size of the real source.

WHY we don't use the `gitignore` pip package:
  Zero external deps keeps deployment trivial — no pip install needed
  beyond what the tool already requires. The gitignore spec is regular
  enough that 60 lines covers 95%+ of real-world patterns.

HOW it works:
  1. Load a .gitignore file → compile each line into a regex
  2. GitignoreRuleset.match(path) → True if path should be ignored
  3. Walk the directory tree, query the nearest .gitignore per subdir

GITIGNORE PATTERN RULES (implemented here):
  # comment           — skip
  blank line          — skip
  pattern             — match relative to the .gitignore's directory
  /pattern            — anchored to gitignore root only
  pattern/            — match directories only
  *.ext               — glob wildcard (fnmatch semantics)
  !pattern            — negate a previous rule (checked in order)
  **/dir              — match in any subdirectory
"""

import fnmatch
import os
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class _Rule:
    """A single compiled .gitignore rule."""
    raw:     str
    pattern: str
    negate:  bool  = False
    dir_only: bool = False
    anchored: bool = False


class GitignoreRuleset:
    """
    Parsed set of .gitignore rules for a single directory.

    Usage:
        ruleset = GitignoreRuleset.load("/path/to/repo/.gitignore")
        ruleset.is_ignored("vendor/github.com/foo", is_dir=True)  # → True
        ruleset.is_ignored("internal/core.go",      is_dir=False) # → False
    """

    def __init__(self, root: str, rules: list[_Rule]):
        self.root  = os.path.abspath(root)
        self._rules = rules

    @classmethod
    def load(cls, gitignore_path: str) -> "GitignoreRuleset":
        """Parse a .gitignore file and return a GitignoreRuleset."""
        root   = str(Path(gitignore_path).parent)
        rules: list[_Rule] = []
        try:
            with open(gitignore_path, encoding="utf-8", errors="replace") as f:
                for raw in f:
                    raw = raw.rstrip("\r\n")
                    rule = _parse_line(raw)
                    if rule:
                        rules.append(rule)
        except OSError:
            pass
        return cls(root, rules)

    @classmethod
    def empty(cls, root: str) -> "GitignoreRuleset":
        return cls(root, [])

    def is_ignored(self, path: str, is_dir: bool = False) -> bool:
        """
        Return True if `path` (absolute) matches any ignore rule.
        Rules are evaluated in order; negation rules can un-ignore a path.
        """
        try:
            rel = os.path.relpath(path, self.root).replace("\\", "/")
        except ValueError:
            return False  # On Windows, different drives

        ignored = False
        for rule in self._rules:
            if rule.dir_only and not is_dir:
                continue
            if _matches(rule, rel):
                ignored = not rule.negate
        return ignored


def build_multi_ruleset(root: str) -> "GitignoreRuleset":
    """
    Walk from `root` and collect ALL .gitignore files into a single
    merged ruleset. Rules from deeper directories take precedence
    (appended last, evaluated last in is_ignored).
    """
    all_rules: list[_Rule] = []
    for dirpath, _, filenames in os.walk(root):
        if ".gitignore" in filenames:
            rs = GitignoreRuleset.load(os.path.join(dirpath, ".gitignore"))
            all_rules.extend(rs._rules)
    return GitignoreRuleset(root, all_rules)


# ── Hard-coded always-ignore directories ──────────────────────────────────────
# These are safe to skip in ANY repo regardless of .gitignore content.
ALWAYS_IGNORE_DIRS = {
    ".git", ".hg", ".svn",
    "__pycache__", ".tox", ".pytest_cache", ".mypy_cache",
    ".venv", "venv", "env", ".env",
    "node_modules",
    "vendor",          # Go deps
    "dist", "build", "out", "target",
    ".gradle", ".idea", ".vscode",
    "testdata",        # Go test fixtures
    ".terraform",
}

ALWAYS_IGNORE_EXTENSIONS = {
    ".pyc", ".pyo", ".so", ".dll", ".dylib", ".a", ".o",
    ".whl", ".egg", ".zip", ".tar", ".gz", ".bz2", ".xz",
    ".lock",           # package-lock.json, Cargo.lock — not source
    ".pb.go",          # protobuf generated Go
    ".pb.py",          # protobuf generated Python
}

MAX_FILE_BYTES = 1_000_000  # skip files > 1 MB (generated, minified, etc.)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _parse_line(raw: str) -> _Rule | None:
    line = raw.strip()
    if not line or line.startswith("#"):
        return None

    negate   = line.startswith("!")
    if negate:
        line = line[1:]

    dir_only = line.endswith("/")
    if dir_only:
        line = line[:-1]

    anchored = "/" in line and not line.startswith("**")
    pattern  = line.lstrip("/")

    return _Rule(raw=raw, pattern=pattern, negate=negate,
                 dir_only=dir_only, anchored=anchored)


def _matches(rule: _Rule, rel_path: str) -> bool:
    """Test whether rel_path matches a gitignore rule."""
    pat  = rule.pattern
    name = rel_path.split("/")[-1]  # basename

    # ** glob → match against full path
    if "**" in pat:
        full_pat = pat.replace("**/", "").replace("/**", "")
        return fnmatch.fnmatch(rel_path, pat) or fnmatch.fnmatch(name, full_pat)

    # Anchored (contains /) → match full relative path
    if rule.anchored:
        return fnmatch.fnmatch(rel_path, pat)

    # Un-anchored → match basename OR full path
    return fnmatch.fnmatch(name, pat) or fnmatch.fnmatch(rel_path, pat)
