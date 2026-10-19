"""Pinned, read-only real-code exploration. Never executes target repository code."""
from __future__ import annotations
import argparse
import ast
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import random
import re
import subprocess
import sys
import time

COMMIT = 'bcfb5e40fbc8eb74e1c919114f54031d03ab44e9'
TARGETS = [
    ('jpadilla/pyjwt', 'Python', 'JWT application library'),
    ('paramiko/paramiko', 'Python', 'SSH implementation'),
    ('pyca/cryptography', 'Python', 'Cryptographic primitives and bindings'),
    ('golang-jwt/jwt', 'Go', 'JWT application library'),
    ('go-jose/go-jose', 'Go', 'JOSE signing and encryption'),
    ('golang/crypto', 'Go', 'Cryptographic and protocol packages'),
]
HINT = re.compile(r'\b(rsa|ecdsa|ed25519|x25519|ecdh|sign|verify|encrypt|decrypt|Sign\w*|Verify\w*|Encrypt\w*|Decrypt\w*|jwt|jwe|jws|kem|tls|ssh)\b', re.I)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def jsonl(path, rows):
    path.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows), encoding='utf-8')


def command(args, cwd=None, timeout=240):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout)


def git(root, *args):
    result = command(['git', '-c', f'safe.directory={root}', '-C', str(root), *args])
    if result.returncode:
        raise RuntimeError(result.stderr)
    return result.stdout.strip()


def audit(source, target, output):
    sys.path.insert(0, str(source.parent))
    from pqc_migration_tool.scanner.python_scanner import iter_python_files
    from pqc_migration_tool.scanner.go_scanner import detect_primary_language
    from tree_sitter import Language, Parser
    import tree_sitter_go
    parser = Parser(Language(tree_sitter_go.language()))
    language = detect_primary_language(str(target))
    py_selected = set(map(lambda p: str(Path(p).resolve()), iter_python_files(str(target))))
    go_excluded = {'.git', 'vendor', 'node_modules', '.tox', 'dist', 'build'}
    ledger, hints, ordinary = [], [], []
    tracked = command(['git', '-C', str(target), 'ls-files', '-z']).stdout.split('\0')
    for rel in sorted(p for p in tracked if p.endswith(('.py', '.go'))):
        path = target / rel
        lang = 'Python' if path.suffix == '.py' else 'Go'
        reason = None
        if path.is_symlink():
            reason = 'symlink_not_audited'
        elif lang == 'Python' and language == 'go' or lang == 'Go' and language == 'python':
            reason = 'primary_language_selection'
        elif lang == 'Python' and str(path.resolve()) not in py_selected:
            reason = 'python_scanner_directory_ignore_or_size_policy'
        elif lang == 'Go' and any(part in go_excluded for part in Path(rel).parts[:-1]):
            reason = 'go_scanner_directory_exclusion'
        row = {'path': rel, 'language': lang, 'scope': 'test_or_fixture' if any('test' in part.lower() for part in Path(rel).parts) else 'other_source', 'eligible_by_scanner_policy': reason is None, 'exclusion_reason': reason}
        if reason:
            ledger.append(row)
            continue
        try:
            raw = path.read_bytes()
            text = raw.decode('utf-8', errors='replace')
            row.update(bytes=len(raw), source_sha256=sha(raw), decode_replacement='\ufffd' in text)
            if lang == 'Python':
                ast.parse(text, filename=rel)
                row['parse_status'] = 'ok'
            else:
                row['parse_status'] = 'syntax_error' if parser.parse(raw).root_node.has_error else 'ok'
            for lineno, line in enumerate(text.splitlines(), 1):
                if not line.strip() or line.lstrip().startswith(('#', '//')):
                    continue
                candidate = {'path': rel, 'line': lineno, 'language': lang}
                if HINT.search(line):
                    hints.append(candidate)
                else:
                    ordinary.append(candidate)
        except SyntaxError as exc:
            row.update(parse_status='syntax_error', diagnostic=f'{exc.msg} (line {exc.lineno})')
        except Exception as exc:
            row.update(parse_status='audit_error', diagnostic=repr(exc))
        ledger.append(row)
    save(output, {'primary_language': language, 'files': ledger, 'independent_text_candidates': hints, 'ordinary_line_candidates': ordinary,
                  'ledger_boundary': 'Separately observed parser outcomes and scanner file-selection policy; not scanner-emitted diagnostics. No target code executed.'})


def acquire(workspace, item, locks):
    name, language, rationale = item
    slug = name.replace('/', '__')
    target = workspace / 'repositories' / slug
    url = f'https://github.com/{name}.git'
    logs = workspace / 'acquisition'
    logs.mkdir(parents=True, exist_ok=True)
    try:
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            result = command(['git', '-c', 'core.autocrlf=false', 'clone', '--depth', '1', '--no-recurse-submodules', url, str(target)])
            (logs / (slug + '.log')).write_text(result.stdout + result.stderr, encoding='utf-8')
            if result.returncode:
                raise RuntimeError(result.stderr)
        current = git(target, 'rev-parse', 'HEAD')
        expected = locks.get(name, current)
        if current != expected:
            raise RuntimeError(f'Existing checkout {current} differs from locked {expected}; create a separate study directory to change revisions.')
        if git(target, 'status', '--porcelain', '--untracked-files=no'):
            raise RuntimeError('Target tracked files have local changes')
        licenses = []
        for path in sorted(target.iterdir()):
            if path.is_file() and re.match(r'^(licen[cs]e|copying|notice)', path.name, re.I):
                licenses.append({'path': path.name, 'sha256': sha(path.read_bytes()), 'url': f'https://github.com/{name}/blob/{current}/{path.name}'})
        return {'repository': name, 'language': language, 'rationale': rationale, 'commit': current, 'path': str(target), 'licenses': licenses, 'status': 'acquired'}
    except Exception as exc:
        return {'repository': name, 'language': language, 'status': 'acquisition_failure', 'error': repr(exc)}


def scan_one(source, run, repo):
    if repo['status'] != 'acquired':
        return repo
    target = Path(repo['path'])
    out = run / repo['repository'].replace('/', '__')
    out.mkdir(parents=True, exist_ok=True)
    record = dict(repo)
    record['artifacts'] = str(out)
    args = [sys.executable, str(source / 'cli.py'), 'scan', str(target), '--format', 'json', '--output', str(out / 'report.json'), '--quiet']
    record['command'] = args
    started = time.monotonic()
    try:
        result = command(args, timeout=180)
        record.update(exit_code=result.returncode, wall_seconds=round(time.monotonic() - started, 3))
        (out / 'stdout.log').write_text(result.stdout, encoding='utf-8')
        (out / 'stderr.log').write_text(result.stderr, encoding='utf-8')
        report = json.loads((out / 'report.json').read_text(encoding='utf-8'))
        if result.returncode not in (0, 1) or report['source_commit'] != repo['commit']:
            raise RuntimeError('Unexpected CLI exit or target-commit mismatch')
        records = report['records']
        record.update(status='scan_complete', report_sha256=sha((out / 'report.json').read_bytes()), files_reported=report['files_scanned'], findings=len(records),
                      role_counts=dict(Counter(r['finding']['role'] for r in records)),
                      operation_counts=dict(Counter(r['finding']['operation'] for r in records)),
                      detection_type_counts=dict(Counter(r['finding']['detection_type'] for r in records)),
                      decision_counts=dict(Counter((r.get('plan') or {}).get('decision_trace', {}).get('outcome', 'no_trace') for r in records)),
                      patch_available=sum(bool((r.get('plan') or {}).get('patch_available')) for r in records))
    except subprocess.TimeoutExpired as exc:
        record.update(status='scan_timeout', wall_seconds=round(time.monotonic() - started, 3), error=str(exc))
        for label, value in [('stdout', exc.stdout), ('stderr', exc.stderr)]:
            (out / (label + '.log')).write_text(value.decode('utf-8', 'replace') if isinstance(value, bytes) else value or '', encoding='utf-8')
    except Exception as exc:
        record.update(status='scan_failure', error=repr(exc))
    try:
        result = command([sys.executable, str(Path(__file__).resolve()), '--audit', '--source', str(source), '--target', str(target), '--output', str(out / 'file-ledger.json')], timeout=180)
        (out / 'audit.log').write_text(result.stdout + result.stderr, encoding='utf-8')
        if result.returncode:
            raise RuntimeError('Audit worker failed; see audit.log')
        ledger = json.loads((out / 'file-ledger.json').read_text())
        record['file_accounting'] = dict(Counter('excluded' if not f['eligible_by_scanner_policy'] else f.get('parse_status', 'missing') for f in ledger['files']))
    except Exception as exc:
        record['audit_error'] = repr(exc)
    record['target_clean_after'] = not bool(git(target, 'status', '--porcelain', '--untracked-files=no'))
    save(out / 'run.json', record)
    print(json.dumps({k: record.get(k) for k in ['repository', 'status', 'findings', 'role_counts', 'file_accounting']}), flush=True)
    return record


def annotation_queue(run, records):
    cases, predictions = [], []
    for repo in records:
        if repo['status'] != 'scan_complete' or 'audit_error' in repo:
            continue
        out = Path(repo['artifacts'])
        target = Path(repo['path'])
        ledger = json.loads((out / 'file-ledger.json').read_text())
        report = json.loads((out / 'report.json').read_text())
        found = []
        for item in report['records']:
            loc = item['finding']['location']
            rel = Path(loc['file_path']).relative_to(target).as_posix()
            found.append({'path': rel, 'line': loc['line_number'], 'language': 'Go' if rel.endswith('.go') else 'Python'})
        rng = random.Random('pqmigrate-real-code-v1:' + repo['repository'])
        selected, seen = [], set()
        for label, population, quota in [('independent_text_search', ledger['independent_text_candidates'], 24), ('scanner_finding', found, 8), ('ordinary_source_control_candidate', ledger['ordinary_line_candidates'], 8)]:
            population = list(population)
            rng.shuffle(population)
            count = 0
            for row in population:
                key = (row['path'], row['line'])
                if key in seen:
                    continue
                seen.add(key)
                selected.append(dict(row, selection_method=label))
                count += 1
                if count == quota:
                    break
        for row in selected:
            path = target / row['path']
            raw = path.read_bytes()
            lines = raw.decode('utf-8', 'replace').splitlines()
            start, end = max(1, row['line'] - 12), min(len(lines), row['line'] + 12)
            snippet = '\n'.join(lines[start - 1:end])
            case_id = sha(f"{repo['repository']}:{repo['commit']}:{row['path']}:{row['line']}".encode())[:20]
            cases.append(dict(row, case_id=case_id, repository=repo['repository'], commit=repo['commit'], source_sha256=sha(raw), snippet_sha256=sha(snippet.encode()),
                              start_line=start, end_line=end, snippet=snippet, source_url=f"https://github.com/{repo['repository']}/blob/{repo['commit']}/{row['path']}#L{row['line']}",
                              partition='exploratory_only', annotation_status='unreviewed', gold_presence=None, gold_role=None, gold_operation=None, gold_context=None, reviewer_notes='',
                              unit='source_anchor_requires_manual_operation_delimitation'))
            predictions.append({'case_id': case_id, 'matching_report_records': [r for r in report['records'] if Path(r['finding']['location']['file_path']).relative_to(target).as_posix() == row['path'] and r['finding']['location']['line_number'] == row['line']]})
    jsonl(run / 'annotation-candidates.jsonl', cases)
    jsonl(run / 'tool-predictions-separate.jsonl', predictions)
    for name in ['annotator-a', 'annotator-b']:
        jsonl(run / (name + '.jsonl'), [{k: v for k, v in row.items() if k != 'selection_method'} for row in cases])
    duplicates = Counter(c['snippet_sha256'] for c in cases)
    return {'candidate_count': len(cases), 'per_repository': dict(Counter(c['repository'] for c in cases)), 'selection_counts': dict(Counter(c['selection_method'] for c in cases)), 'duplicate_snippet_groups': [h for h, n in duplicates.items() if n > 1], 'reviewed_count': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--workspace', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--target', type=Path)
    parser.add_argument('--audit', action='store_true')
    args = parser.parse_args()
    source = args.source.resolve()
    if args.audit:
        audit(source, args.target.resolve(), args.output)
        return
    if git(source, 'rev-parse', 'HEAD') != COMMIT or git(source, 'status', '--porcelain', '--untracked-files=no'):
        raise RuntimeError('Scanner must be the clean frozen implementation commit')
    run = args.output.resolve()
    run.mkdir(parents=True, exist_ok=False)
    lockfile = args.workspace / 'targets.lock.json'
    locks = json.loads(lockfile.read_text()) if lockfile.exists() else {}
    packages = {name: importlib.metadata.version(name) for name in ['PyYAML', 'jsonschema', 'tree-sitter', 'tree-sitter-go']}
    save(run / 'protocol.json', {'date_utc': datetime.now(timezone.utc).isoformat(), 'scanner_commit': COMMIT, 'scanner_path': str(source), 'python': sys.version, 'packages': packages,
                               'selection': 'Purposive exploratory selection before observing outputs; all six repositories are exposed development/exploration data, not holdouts.',
                               'targets': TARGETS, 'timeout_seconds_per_scan': 180, 'target_code_execution': False, 'test_source_included': True,
                               'accuracy_claims_permitted': False, 'candidate_goal_per_repository': 40, 'annotation_seed': 'pqmigrate-real-code-v1',
                               'runner_sha256': sha(Path(__file__).read_bytes())})
    with ThreadPoolExecutor(max_workers=3) as pool:
        acquired = list(pool.map(lambda item: acquire(args.workspace, item, locks), TARGETS))
    save(run / 'acquisition.json', acquired)
    locks.update({r['repository']: r['commit'] for r in acquired if r['status'] == 'acquired'})
    save(lockfile, locks)
    # Serial scans avoid competing CPU work; timings remain descriptive only.
    records = [scan_one(source, run, repo) for repo in acquired]
    annotations = annotation_queue(run, records)
    summary = {'scanner_commit': COMMIT, 'repositories': records, 'annotation': annotations,
               'accuracy_metrics': None, 'accuracy_reason': 'No independent gold labels; raw finding/answer counts are not precision, recall, or safety measurements.'}
    save(run / 'summary.json', summary)
    lines = ['# PQMigrate real-code exploration', '', f'Scanner commit: `{COMMIT}`.', '', 'Six purposively selected repositories; exploratory scans, not independent accuracy evaluation.', '', '| Repository | Status | Files reported | Findings | Known-role records | Parser ledger |', '|---|---|---:|---:|---:|---|']
    for r in records:
        known = sum(n for role, n in r.get('role_counts', {}).items() if role != 'unknown')
        lines.append(f"| {r['repository']} | {r['status']} | {r.get('files_reported', '-')} | {r.get('findings', '-')} | {known} | {r.get('file_accounting', {})} |")
    lines += ['', f"Prepared {annotations['candidate_count']} unreviewed source anchors for annotation; zero independently reviewed cases.", '',
              'Findings are inventory/report records and can include multiple records for one operation. Known roles are tool outputs, not verified correct answers. Parser ledger is independently collected because CLI reports may omit parse failures. Tests/fixtures are included and tagged in the file ledger.', '',
              'Each repository directory contains the raw JSON report, stdout/stderr, exact command and commit, timing, file ledger, and report checksum. acquisition.json retains license-file links and hashes. All six repositories must stay out of a later unseen test split.', '',
              'Annotation candidates mix 24 independent text-search anchors, up to 8 scanner anchors and up to 8 ordinary-source anchors per repository. Ordinary-source anchors are not assumed negative. Review full functions and callers when snippets lack context; delimit actual operation units before scoring. Tool predictions are in a separate file.', '',
              'Next: two independent annotators; disagreements and adjudication; evaluate all baselines on the same adjudicated units; sample additional unseen repository families for held-out evaluation. Retain the 72-case pilot as synthetic regression evidence.']
    (run / 'README.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    save(run / 'checksums.json', {str(p.relative_to(run)): sha(p.read_bytes()) for p in sorted(run.rglob('*')) if p.is_file() and p.name != 'checksums.json'})
    print(json.dumps({'output': str(run), 'annotation': annotations}), flush=True)


if __name__ == '__main__':
    main()
