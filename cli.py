"""
PQC Migration Tool — CLI
==========================
Usage:
  python3 cli.py scan <path>                        # scan local directory/file
  python3 cli.py scan <path> --format json|md       # JSON or Markdown output
  python3 cli.py scan <path> --output out.md        # save report to file
  python3 cli.py scan <path> --show-safe --verbose

  python3 cli.py repo <owner/repo>                  # scan any GitHub repo
  python3 cli.py repo <https://any-git-url>         # scan any git URL
  python3 cli.py repo django/django                 # GitHub shorthand
  python3 cli.py repo pyca/cryptography --format md --output report.md
  python3 cli.py repo paramiko/paramiko --branch main --keep
  python3 cli.py repo https://gitlab.com/foo/bar    # GitLab / self-hosted

  python3 cli.py migration <primitive>              # show migration code example
  python3 cli.py list-patterns                      # list all detected patterns
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

# ── Path setup (allow running as python3 cli.py without installing) ──────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

from pqc_migration_tool.scanner.python_scanner import scan_file, scan_directory
from pqc_migration_tool.scanner.go_scanner import (
    scan_go_file, scan_go_directory, count_go_files, detect_primary_language
)
from pqc_migration_tool.risk.scorer import score_system
from pqc_migration_tool.report.generator import (
    report_console, report_json, report_markdown
)
from pqc_migration_tool.mapper.crypto_map import MIGRATION_MAP
from pqc_migration_tool.scanner.patterns import IMPORT_PATTERNS, Risk
from pqc_migration_tool.scanner.go_patterns import GO_IMPORT_PATTERNS


VERSION = "0.3.0"
BANNER  = f"""
╔══════════════════════════════════════════════════════╗
║  PQC Migration Scanner  v{VERSION}                      ║
║  Finds classical crypto vulnerable to Shor/Grover    ║
║  Maps to NIST FIPS 203/204/205 PQC replacements      ║
╚══════════════════════════════════════════════════════╝
"""


# ═══════════════════════════════════════════════════════════════════════════════
# cmd_scan
# ═══════════════════════════════════════════════════════════════════════════════

def cmd_scan(args: list[str]):
    if not args:
        print("Usage: python3 cli.py scan <path> [--format console|json|md] "
              "[--output file] [--show-safe] [--verbose]")
        sys.exit(1)

    path      = args[0]
    fmt       = _get_flag(args, "--format", "console")
    output    = _get_flag(args, "--output",  None)
    show_safe = "--show-safe" in args
    verbose   = "--verbose"   in args
    quiet     = "--quiet"     in args

    if not quiet:
        print(BANNER)

    if not os.path.exists(path):
        print(f"Error: path not found: {path}")
        sys.exit(1)

    _run_scan(path, fmt, output, show_safe, verbose, quiet)


# ═══════════════════════════════════════════════════════════════════════════════
# cmd_repo — clone any git URL or GitHub shorthand, scan, report, clean up
# ═══════════════════════════════════════════════════════════════════════════════

def cmd_repo(args: list[str]):
    if not args:
        print("Usage: python3 cli.py repo <owner/repo | git-url> [options]")
        print("  --branch <name>   Clone a specific branch (default: default branch)")
        print("  --format  json|md|console")
        print("  --output  <file>  Save report to file")
        print("  --keep            Don't delete the cloned repo after scanning")
        print("  --show-safe       Include PQC-safe findings in output")
        print("  --depth   <n>     Shallow clone depth (default: 1 = fastest)")
        print()
        print("Examples:")
        print("  python3 cli.py repo paramiko/paramiko")
        print("  python3 cli.py repo pyca/cryptography --format md --output crypto_report.md")
        print("  python3 cli.py repo https://github.com/hashicorp/vault")
        print("  python3 cli.py repo django/django --branch stable/4.2.x")
        sys.exit(0)

    raw_target = args[0]
    branch     = _get_flag(args, "--branch", None)
    fmt        = _get_flag(args, "--format", "console")
    output     = _get_flag(args, "--output",  None)
    depth      = int(_get_flag(args, "--depth", "1"))
    keep       = "--keep"      in args
    show_safe  = "--show-safe" in args
    verbose    = "--verbose"   in args
    quiet      = "--quiet"     in args

    if not quiet:
        print(BANNER)

    # ── Resolve URL ───────────────────────────────────────────────────────────
    git_url, repo_name = _resolve_git_url(raw_target)

    # ── Clone ─────────────────────────────────────────────────────────────────
    clone_dir = os.path.join(tempfile.gettempdir(), f"pqc_scan_{repo_name}")

    # Re-use existing clone if present (saves time on repeated scans)
    if os.path.isdir(clone_dir):
        print(f"  ♻  Re-using existing clone at {clone_dir}")
        print(f"     (delete it or use a different --depth to force fresh clone)")
    else:
        print(f"  ⬇  Cloning {git_url}")
        cmd = ["git", "clone", f"--depth={depth}", "--single-branch"]
        if branch:
            cmd += ["--branch", branch]
        cmd += [git_url, clone_dir]

        t0 = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        elapsed = time.time() - t0

        if result.returncode != 0:
            print(f"\nClone failed:\n{result.stderr}")
            sys.exit(1)
        print(f"  ✓  Cloned in {elapsed:.1f}s → {clone_dir}")

    print()

    try:
        _run_scan(clone_dir, fmt, output, show_safe, verbose, quiet=True,
                  display_root=f"{repo_name} ({git_url})")
    finally:
        if not keep and os.path.isdir(clone_dir):
            shutil.rmtree(clone_dir, ignore_errors=True)
            print(f"\n  🗑  Cleaned up: {clone_dir}  (use --keep to retain)")


# ═══════════════════════════════════════════════════════════════════════════════
# Shared scan + report runner
# ═══════════════════════════════════════════════════════════════════════════════

def _run_scan(path: str, fmt: str, output: str | None,
              show_safe: bool, verbose: bool, quiet: bool,
              display_root: str | None = None):
    """
    Core scan runner — auto-detects language and calls appropriate scanner(s).
    Day 4: Now shows live progress + scan statistics.
    """
    from pqc_migration_tool.schema.models import ProjectReport, CryptoIR, CodeLocation, CryptoRole, CryptoOperation, SecurityStatus, ConfidenceLevel
    from pqc_migration_tool.resolver.planner import MigrationPlanner
    from pqc_migration_tool.scanner.progress import ScanProgress, ScanStats

    stats = ScanStats()

    if os.path.isfile(path):
        if path.endswith(".go"):
            findings    = scan_go_file(path)
            lang_label  = "Go"
        else:
            findings    = scan_file(path)
            lang_label  = "Python"
        files_count = 1
        root        = os.path.dirname(os.path.abspath(path))
        stats.record_file(path, len(findings))
    else:
        root       = os.path.abspath(path)
        lang       = detect_primary_language(root)
        lang_label = {"python": "Python", "go": "Go",
                      "mixed": "Python + Go", "unknown": "unknown"}[lang]

        if not quiet:
            _CYAN, _RST = "\033[96m", "\033[0m"
            print(f"  Language detected: {_CYAN}{lang_label}{_RST}")

        py_findings = []
        go_findings = []
        py_count    = 0
        go_count    = 0

        if lang in ("python", "mixed", "unknown"):
            with ScanProgress(root, quiet=quiet) as prog:
                py_findings = scan_directory(
                    path, progress=prog, stats=stats
                )
            py_count = stats.files_scanned

        if lang in ("go", "mixed"):
            with ScanProgress(root, quiet=quiet) as prog:
                go_findings = scan_go_directory(path)
                go_count    = count_go_files(path)
                # go_scanner doesn't take progress yet — just count
                prog.update(root, len(go_findings))

        findings    = py_findings + go_findings
        files_count = py_count + go_count

    stats.stop()
    if not quiet:
        print(stats.summary())

    summary      = score_system(display_root or root, findings, files_count)
    summary.root = display_root or root

    if fmt == "json":
        out = report_json(summary, output_path=output)
        if not output:
            print(out)
    elif fmt in ("md", "markdown"):
        out = report_markdown(summary, output_path=output)
        if not output:
            print(out)
    else:
        report_console(summary, show_safe=show_safe, verbose=verbose)
        if output:
            report_markdown(summary, output_path=output)

    if summary.critical_count > 0 or summary.high_count > 0:
        sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════════
# cmd_migration
# ═══════════════════════════════════════════════════════════════════════════════

def cmd_migration(args: list[str]):
    if not args:
        print("Available primitives:")
        for name in MIGRATION_MAP:
            print(f"  {name}")
        return

    primitive = args[0].upper()
    if primitive not in MIGRATION_MAP:
        matches = [k for k in MIGRATION_MAP if primitive in k.upper()]
        if matches:
            primitive = matches[0]
        else:
            print(f"Unknown primitive: {args[0]}")
            print(f"Available: {', '.join(MIGRATION_MAP.keys())}")
            return

    m = MIGRATION_MAP[primitive]
    print(f"\n{'═'*60}")
    print(f"  Migration: {m.from_primitive}  →  {m.to_primitive}")
    print(f"  Standard : {m.fips_standard}")
    print(f"  Category : {m.nist_category}")
    print(f"{'═'*60}")
    print(f"\n── BEFORE (vulnerable) {'─'*35}")
    print(m.before_code)
    print(f"\n── AFTER (quantum-safe) {'─'*34}")
    print(m.after_code)
    if m.notes:
        print(f"\n── Notes {'─'*49}")
        print(m.notes)
    if m.references:
        print(f"\n── References {'─'*44}")
        for ref in m.references:
            print(f"  {ref}")
    print()


# ═══════════════════════════════════════════════════════════════════════════════
# cmd_list_patterns
# ═══════════════════════════════════════════════════════════════════════════════

def cmd_list_patterns(args: list[str]):
    show_safe = "--show-safe" in args
    print(f"\n{'─'*80}")
    print(f"  {'Pattern (import path)':<50}  {'Risk':>8}  Harvest?")
    print(f"{'─'*80}")
    for path, pattern in sorted(IMPORT_PATTERNS.items(),
                                 key=lambda x: (x[1].risk.value, x[0])):
        if not show_safe and pattern.risk == Risk.SAFE:
            continue
        harvest = "YES ⚡" if pattern.harvest_risk else "No"
        print(f"  {path:<50}  {pattern.risk.value:>8}  {harvest}")
    print()
    if not show_safe:
        safe_count = sum(1 for p in IMPORT_PATTERNS.values() if p.risk == Risk.SAFE)
        print(f"  ({safe_count} SAFE patterns hidden — use --show-safe to display)")
    print()


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _resolve_git_url(raw: str) -> tuple[str, str]:
    """
    Convert any of these inputs into (git_url, repo_name):
      owner/repo              → https://github.com/owner/repo   , repo
      github:owner/repo       → https://github.com/owner/repo   , repo
      gitlab:owner/repo       → https://gitlab.com/owner/repo   , repo
      https://github.com/...  → as-is                           , last path segment
      git@github.com:...      → as-is                           , last path segment
    """
    # Already a full URL
    if raw.startswith("https://") or raw.startswith("git@") or raw.startswith("http://"):
        repo_name = raw.rstrip("/").split("/")[-1]
        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]
        return raw, repo_name

    # Explicit host prefix: gitlab:owner/repo or bitbucket:owner/repo
    host_map = {
        "github":    "https://github.com",
        "gitlab":    "https://gitlab.com",
        "bitbucket": "https://bitbucket.org",
    }
    for prefix, base in host_map.items():
        if raw.startswith(prefix + ":"):
            path = raw[len(prefix)+1:]
            repo_name = path.split("/")[-1].replace(".git", "")
            return f"{base}/{path}", repo_name

    # owner/repo shorthand — default to GitHub
    if re.match(r"^[\w.\-]+/[\w.\-]+$", raw):
        repo_name = raw.split("/")[1].replace(".git", "")
        return f"https://github.com/{raw}", repo_name

    # Fallback: treat as-is
    return raw, raw.split("/")[-1].replace(".git", "")


def _get_flag(args: list[str], flag: str, default):
    try:
        idx = args.index(flag)
        return args[idx + 1]
    except (ValueError, IndexError):
        return default


# ═══════════════════════════════════════════════════════════════════════════════
# main
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    args = sys.argv[1:]
    if not args:
        print(BANNER)
        print("Commands:")
        print("  scan   <path>              Scan a local file or directory")
        print("  repo   <owner/repo|url>    Clone & scan any git repository")
        print("  migration <primitive>      Show migration code example")
        print("  list-patterns             List all detectable patterns")
        print()
        print("Examples:")
        print("  python3 cli.py scan /home/ratneshp0411/")
        print("  python3 cli.py repo paramiko/paramiko")
        print("  python3 cli.py repo pyca/cryptography --format md --output report.md")
        print("  python3 cli.py repo https://github.com/ansible/ansible")
        print("  python3 cli.py repo django/django --branch stable/4.2.x --keep")
        print("  python3 cli.py migration X25519")
        print("  python3 cli.py list-patterns")
        return

    command = args[0]
    rest    = args[1:]

    dispatch = {
        "scan":          cmd_scan,
        "repo":          cmd_repo,
        "migration":     cmd_migration,
        "list-patterns": cmd_list_patterns,
    }

    if command in dispatch:
        dispatch[command](rest)
    else:
        print(f"Unknown command: {command}")
        print("Run: python3 cli.py  (no args) for help")
        sys.exit(1)


if __name__ == "__main__":
    main()


import sys
import os

# ── Path setup (allow running as python3 cli.py without installing) ───────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

from pqc_migration_tool.scanner.python_scanner import scan_file, scan_directory
from pqc_migration_tool.risk.scorer import score_system
from pqc_migration_tool.report.generator import (
    report_console, report_json, report_markdown
)
from pqc_migration_tool.mapper.crypto_map import MIGRATION_MAP
from pqc_migration_tool.scanner.patterns import IMPORT_PATTERNS, Risk


VERSION = "0.1.0"
BANNER  = f"""
╔══════════════════════════════════════════════════════╗
║  PQC Migration Scanner  v{VERSION}                      ║
║  Finds classical crypto vulnerable to Shor/Grover    ║
║  Maps to NIST FIPS 203/204/205 PQC replacements      ║
╚══════════════════════════════════════════════════════╝
"""


def cmd_scan(args: list[str]):
    if not args:
        print("Usage: python3 cli.py scan <path> [--format console|json|md] "
              "[--output file] [--show-safe] [--verbose]")
        sys.exit(1)

    path       = args[0]
    fmt        = _get_flag(args, "--format", "console")
    output     = _get_flag(args, "--output", None)
    show_safe  = "--show-safe" in args
    verbose    = "--verbose"   in args
    quiet      = "--quiet"     in args

    if not quiet:
        print(BANNER)

    if not os.path.exists(path):
        print(f"Error: path not found: {path}")
        sys.exit(1)

    # ── Scan ──────────────────────────────────────────────────────────────────
    if os.path.isfile(path):
        findings     = scan_file(path)
        files_count  = 1
        root         = os.path.dirname(os.path.abspath(path))
    else:
        findings     = scan_directory(path)
        root         = os.path.abspath(path)
        # Count py files for the summary
        files_count  = sum(
            1 for _, _, fnames in os.walk(path)
            for f in fnames if f.endswith(".py")
        )

    # ── Score ─────────────────────────────────────────────────────────────────
    summary = score_system(root, findings, files_count)

    # ── Report ────────────────────────────────────────────────────────────────
    if fmt == "json":
        out = report_json(summary, output_path=output)
        if not output:
            print(out)
    elif fmt in ("md", "markdown"):
        out = report_markdown(summary, output_path=output)
        if not output:
            print(out)
    else:
        report_console(summary, show_safe=show_safe, verbose=verbose)
        if output:
            # Also save markdown alongside
            report_markdown(summary, output_path=output)

    # Exit code: 1 if any CRITICAL/HIGH findings (for CI/CD use)
    if summary.critical_count > 0 or summary.high_count > 0:
        sys.exit(1)


def cmd_migration(args: list[str]):
    """Show before/after code migration example for a primitive."""
    if not args:
        print("Available primitives:")
        for name in MIGRATION_MAP:
            print(f"  {name}")
        return

    primitive = args[0].upper()
    if primitive not in MIGRATION_MAP:
        # Fuzzy match
        matches = [k for k in MIGRATION_MAP if primitive in k.upper()]
        if matches:
            primitive = matches[0]
        else:
            print(f"Unknown primitive: {args[0]}")
            print(f"Available: {', '.join(MIGRATION_MAP.keys())}")
            return

    m = MIGRATION_MAP[primitive]
    print(f"\n{'═'*60}")
    print(f"  Migration: {m.from_primitive}  →  {m.to_primitive}")
    print(f"  Standard : {m.fips_standard}")
    print(f"  Category : {m.nist_category}")
    print(f"{'═'*60}")
    print(f"\n── BEFORE (vulnerable) {'─'*35}")
    print(m.before_code)
    print(f"\n── AFTER (quantum-safe) {'─'*34}")
    print(m.after_code)
    if m.notes:
        print(f"\n── Notes {'─'*49}")
        print(m.notes)
    if m.references:
        print(f"\n── References {'─'*44}")
        for ref in m.references:
            print(f"  {ref}")
    print()


def cmd_list_patterns(args: list[str]):
    """List all detectable crypto patterns."""
    show_safe = "--show-safe" in args
    print(f"\n{'─'*80}")
    print(f"  {'Pattern (import path)':<50}  {'Risk':>8}  Harvest?")
    print(f"{'─'*80}")
    for path, pattern in sorted(IMPORT_PATTERNS.items(),
                                 key=lambda x: (x[1].risk.value, x[0])):
        if not show_safe and pattern.risk == Risk.SAFE:
            continue
        harvest = "YES ⚡" if pattern.harvest_risk else "No"
        print(f"  {path:<50}  {pattern.risk.value:>8}  {harvest}")
    print()
    if not show_safe:
        safe_count = sum(1 for p in IMPORT_PATTERNS.values() if p.risk == Risk.SAFE)
        print(f"  ({safe_count} SAFE patterns hidden — use --show-safe to display)")
    print()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_flag(args: list[str], flag: str, default):
    try:
        idx = args.index(flag)
        return args[idx + 1]
    except (ValueError, IndexError):
        return default


def main():
    args = sys.argv[1:]
    if not args:
        print(BANNER)
        print("Commands:")
        print("  scan <path>              Scan a file or directory")
        print("  migration <primitive>    Show migration code example")
        print("  list-patterns            List all detectable patterns")
        print()
        print("Examples:")
        print("  python3 cli.py scan /home/ratneshp0411/")
        print("  python3 cli.py scan . --format json --output report.json")
        print("  python3 cli.py scan . --format md  --output MIGRATION.md")
        print("  python3 cli.py migration X25519")
        print("  python3 cli.py migration RSA")
        print("  python3 cli.py list-patterns")
        return

    command = args[0]
    rest    = args[1:]

    if command == "scan":
        cmd_scan(rest)
    elif command == "migration":
        cmd_migration(rest)
    elif command == "list-patterns":
        cmd_list_patterns(rest)
    else:
        print(f"Unknown command: {command}")
        print("Run: python3 cli.py  (no args) for help")
        sys.exit(1)


if __name__ == "__main__":
    main()
