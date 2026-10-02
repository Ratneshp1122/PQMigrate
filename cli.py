"""
PQC Migration Tool — CLI
==========================
Usage:
  python3 cli.py scan <path>                        # scan local directory/file
  python3 cli.py scan <path> --format json|md|sarif|cbom
  python3 cli.py scan <path> --output out.md        # save report to file
  python3 cli.py scan <path> --show-safe --verbose

  python3 cli.py repo <owner/repo>                  # scan any GitHub repo
  python3 cli.py repo <https://any-git-url>         # scan any git URL
  python3 cli.py repo django/django                 # GitHub shorthand
  python3 cli.py repo pyca/cryptography --format md --output report.md
  python3 cli.py repo paramiko/paramiko --branch main --keep
  python3 cli.py repo https://gitlab.com/foo/bar    # GitLab / self-hosted

  python3 cli.py export report.json --format sarif|cbom
  python3 cli.py preview file.py --expected-sha256 HASH --line N
  python3 cli.py migration <primitive>              # show migration code example
  python3 cli.py list-patterns                      # list all detected patterns
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# ── Path setup (allow running as python3 cli.py without installing) ──────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")

from pqc_migration_tool.scanner.python_scanner import scan_file, scan_directory
from pqc_migration_tool.scanner.go_scanner import (
    scan_go_file, scan_go_directory, count_go_files, detect_primary_language
)
from pqc_migration_tool.risk.scorer import score_system
from pqc_migration_tool.report.generator import (
    export_project_report, report_cbom, report_console, report_json,
    report_markdown, report_sarif
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
        print("Usage: python3 cli.py scan <path> [--format console|json|md|sarif|cbom] "
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
        print("  --format  json|md|sarif|cbom|console")
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
    elif fmt == "sarif":
        out = report_sarif(summary, output_path=output)
        if not output:
            print(out)
    elif fmt == "cbom":
        out = report_cbom(summary, output_path=output)
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


def cmd_list_rules(args: list[str]):
    """Validate and list the active D7 migration knowledge base."""
    from pqc_migration_tool.knowledge.loader import KnowledgeBase, load_default_knowledge_base

    knowledge = KnowledgeBase.load(args[0]) if args else load_default_knowledge_base()
    print(f"\nKnowledge base: {knowledge.source_path}")
    print(f"Rules version : {knowledge.rules_version}")
    print(f"Rule count    : {len(knowledge.rules)}\n")
    print(f"  {'Rule ID':<36} {'Roles':<22} Target")
    print(f"  {'-' * 34:<36} {'-' * 20:<22} {'-' * 30}")
    for rule in knowledge.rules:
        roles = ",".join(role.value for role in rule.roles)
        print(f"  {rule.rule_id:<36} {roles:<22} {rule.target_algorithm}")
    print()


def cmd_export(args: list[str]):
    """Convert a canonical ProjectReport JSON file to SARIF or CycloneDX CBOM."""
    if not args:
        print("Usage: python3 cli.py export <report.json> --format sarif|cbom [--output file]")
        sys.exit(1)

    input_path = Path(args[0])
    export_format = _get_flag(args, "--format", None)
    output = _get_flag(args, "--output", None)
    if export_format not in {"sarif", "cbom"}:
        print("Error: --format must be sarif or cbom")
        sys.exit(1)
    if not input_path.is_file():
        print(f"Error: report not found: {input_path}")
        sys.exit(1)

    try:
        report = json.loads(input_path.read_text(encoding="utf-8"))
        out = export_project_report(report, export_format, output_path=output)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"Export failed: {exc}")
        sys.exit(1)

    if output:
        label = "SARIF 2.1.0" if export_format == "sarif" else "CycloneDX 1.7 CBOM"
        print(f"  {label} report saved → {output}")
    else:
        print(out)


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


def cmd_preview(args: list[str]):
    """Generate D12 review evidence and an exact diff without editing source."""
    if not args:
        print("Usage: python3 cli.py preview <file.py> --expected-sha256 HASH --line N "
              "[--output preview.json] [--diff-output preview.diff]")
        sys.exit(1)

    from pqc_migration_tool.patcher.preview import PreviewRequest, preview_md5_to_sha256

    source = Path(args[0])
    expected = _get_flag(args, "--expected-sha256", None)
    raw_line = _get_flag(args, "--line", None)
    output = _get_flag(args, "--output", None)
    diff_output = _get_flag(args, "--diff-output", None)
    if expected is None or raw_line is None:
        print("Error: --expected-sha256 and --line are required")
        sys.exit(1)
    try:
        line_number = int(raw_line)
    except ValueError:
        print("Error: --line must be an integer")
        sys.exit(1)

    result = preview_md5_to_sha256(PreviewRequest(source, expected, line_number))
    evidence = result.to_dict()
    rendered = json.dumps(evidence, indent=2, sort_keys=True) + "\n"
    if output:
        output_path = Path(output)
        if output_path.resolve() == source.resolve():
            print("Error: evidence output must not overwrite source")
            sys.exit(1)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
    if diff_output:
        diff_path = Path(diff_output)
        if diff_path.resolve() == source.resolve():
            print("Error: diff output must not overwrite source")
            sys.exit(1)
        diff_path.parent.mkdir(parents=True, exist_ok=True)
        diff_path.write_text(result.diff, encoding="utf-8")
    print(rendered, end="")
    if result.status != "generated":
        sys.exit(2)


def cmd_verify_preview(args: list[str]):
    """Run D13 bounded verification in a disposable filesystem copy."""
    if not args:
        print("Usage: python3 cli.py verify-preview <file.py> --project-root DIR "
              "--expected-sha256 HASH --line N [--timeout SEC] [--output evidence.json]")
        sys.exit(1)
    from pqc_migration_tool.verification.isolated import (
        IsolatedVerificationRequest,
        verify_preview_in_isolation,
    )

    source = Path(args[0])
    root = _get_flag(args, "--project-root", None)
    expected = _get_flag(args, "--expected-sha256", None)
    raw_line = _get_flag(args, "--line", None)
    raw_timeout = _get_flag(args, "--timeout", "10")
    output = _get_flag(args, "--output", None)
    if root is None or expected is None or raw_line is None:
        print("Error: --project-root, --expected-sha256, and --line are required")
        sys.exit(1)
    try:
        line_number = int(raw_line)
        timeout_seconds = int(raw_timeout)
    except ValueError:
        print("Error: --line and --timeout must be integers")
        sys.exit(1)
    evidence = verify_preview_in_isolation(IsolatedVerificationRequest(
        Path(root), source, expected, line_number, timeout_seconds
    ))
    rendered = json.dumps(evidence, indent=2, sort_keys=True) + "\n"
    if output:
        output_path = Path(output)
        if output_path.resolve() == source.resolve():
            print("Error: evidence output must not overwrite source")
            sys.exit(1)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    if evidence["status"] != "verified_bounded":
        sys.exit(2)


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
        print("  export <report.json>       Convert JSON to SARIF 2.1.0 or CycloneDX 1.7 CBOM")
        print("  preview <file.py>          Generate a hash-bound D12 diff; never edits source")
        print("  verify-preview <file.py>   Verify D12 preview in a disposable copy")
        print("  migration <primitive>      Show migration code example")
        print("  list-patterns             List all detectable patterns")
        print("  list-rules [yaml-path]    Validate and list D7 rules")
        print()
        print("Examples:")
        print("  python3 cli.py scan /home/ratneshp0411/")
        print("  python3 cli.py repo paramiko/paramiko")
        print("  python3 cli.py repo pyca/cryptography --format md --output report.md")
        print("  python3 cli.py repo https://github.com/ansible/ansible")
        print("  python3 cli.py export report.json --format sarif --output report.sarif.json")
        print("  python3 cli.py preview sample.py --expected-sha256 HASH --line 12")
        print("  python3 cli.py verify-preview sample.py --project-root . --expected-sha256 HASH --line 12")
        print("  python3 cli.py repo django/django --branch stable/4.2.x --keep")
        print("  python3 cli.py migration X25519")
        print("  python3 cli.py list-patterns")
        print("  python3 cli.py list-rules")
        return

    command = args[0]
    rest    = args[1:]

    def cmd_patch(args: list[str]):
        if not args:
            print("Usage: python3 cli.py patch <report_v2.json> [--verify]")
            sys.exit(1)

        report_file = args[0]
        do_verify = "--verify" in args

        from pqc_migration_tool.patcher.engine import PatcherEngine
        engine = PatcherEngine(report_file)
        engine.verify = do_verify
        engine.run()

    dispatch = {
        "scan":          cmd_scan,
        "repo":          cmd_repo,
        "patch":         cmd_patch,
        "preview":       cmd_preview,
        "verify-preview": cmd_verify_preview,
        "export":        cmd_export,
        "migration":     cmd_migration,
        "list-patterns": cmd_list_patterns,
        "list-rules":    cmd_list_rules,
    }

    if command in dispatch:
        dispatch[command](rest)
    else:
        print(f"Unknown command: {command}")
        print("Run: python3 cli.py  (no args) for help")
        sys.exit(1)


if __name__ == "__main__":
    main()
