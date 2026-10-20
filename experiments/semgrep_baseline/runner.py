"""Unscored, source-only Semgrep CE baseline with per-input failure accounting."""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import signal
import subprocess
import sys
import time
import urllib.request

HERE = Path(__file__).resolve().parent
VERSION = '1.181.0'
OPERATIONS = {'sign', 'verify', 'encrypt', 'decrypt', 'key_establish', 'hash',
              'mac', 'kdf', 'key_generate', 'other_crypto', 'none', 'uncertain'}
ROLES = {'signature', 'key_transport', 'key_establishment', 'encryption', 'hash',
         'mac', 'kdf', 'key_management', 'other', 'none', 'uncertain'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def load_manifest(path):
    value = json.loads(path.read_text(encoding='utf-8'))
    cases = value['cases']
    ids = set()
    for case in cases:
        cid = case['case_id']
        if not re.fullmatch(r'[a-zA-Z0-9_-]+', cid) or cid in ids:
            raise ValueError('Unsafe or duplicate case_id')
        ids.add(cid)
        if case['language'] not in {'python', 'go'}:
            raise ValueError('Unsupported manifest language')
        if not re.fullmatch(r'[a-f0-9]{64}', case['source_sha256']):
            raise ValueError('Invalid source digest')
        if 'source' not in case:
            if not re.fullmatch(r'[a-f0-9]{40}', case['commit']):
                raise ValueError('Full pinned commit required')
            if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', case['repository']):
                raise ValueError('Invalid repository')
            p = PurePosixPath(case['path'])
            if p.is_absolute() or '..' in p.parts or '\\' in case['path'] or ':' in case['path']:
                raise ValueError('Unsafe source path')
        # Never accept label-bearing inputs, including accidental annotation exports.
        allowed = {'case_id', 'language', 'source_sha256', 'source', 'repository', 'commit', 'path'}
        if set(case) - allowed:
            raise ValueError('Unexpected case fields; use source-only manifests')
    return value


def acquire(case, source_root, download):
    if 'source' in case:
        data = case['source'].encode('utf-8')
    else:
        local = source_root / case['repository'].replace('/', '__') / case['commit'] / case['path']
        if local.is_file():
            data = local.read_bytes()
        elif download:
            url = f"https://raw.githubusercontent.com/{case['repository']}/{case['commit']}/{case['path']}"
            request = urllib.request.Request(url, headers={'User-Agent': 'PQMigrate-Semgrep-baseline'})
            with urllib.request.urlopen(request, timeout=30) as response:
                data = response.read(5_000_001)
            if len(data) > 5_000_000:
                raise ValueError('Source exceeds 5 MB download limit')
            # Write only verified bytes to the cache.
            if digest(data) != case['source_sha256']:
                raise ValueError('Pinned source SHA-256 mismatch')
            local.parent.mkdir(parents=True, exist_ok=True)
            local.write_bytes(data)
        else:
            raise FileNotFoundError('Pinned source not cached; use --download to fetch it')
    if digest(data) != case['source_sha256']:
        raise ValueError('Pinned source SHA-256 mismatch')
    return data


def execute(command, cwd, deadline):
    """Preserve bytes on every exit; kill the whole scanner process tree on deadline."""
    start = time.monotonic()
    env = {k: v for k, v in os.environ.items() if k not in {
        'SEMGREP_APP_TOKEN', 'SEMGREP_RULES', 'SEMGREP_REPO_NAME', 'SEMGREP_BASELINE_COMMIT'}}
    env.update(SEMGREP_SEND_METRICS='off', SEMGREP_ENABLE_VERSION_CHECK='0',
               SEMGREP_ENABLE_METRICS='0', PYTHONIOENCODING='utf-8',
               SEMGREP_SETTINGS_FILE=str(Path(cwd) / 'semgrep-settings.yml'))
    kwargs = {'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == 'nt' else {'start_new_session': True}
    try:
        proc = subprocess.Popen(command, cwd=cwd, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, **kwargs)
    except OSError as exc:
        return {'returncode': None, 'stdout': b'', 'stderr': str(exc).encode(),
                'wall_timeout': False, 'spawn_error': True, 'seconds': time.monotonic()-start}
    timed_out = False
    try:
        out, err = proc.communicate(timeout=deadline)
    except subprocess.TimeoutExpired:
        timed_out = True
        if os.name == 'nt':
            subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        else:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        out, err = proc.communicate()
    return {'returncode': proc.returncode, 'stdout': out, 'stderr': err,
            'wall_timeout': timed_out, 'spawn_error': False, 'seconds': time.monotonic()-start}


def classify(run, payload):
    """Flags are independent: partial parse + findings is not a clean negative."""
    errors = payload.get('errors', []) if isinstance(payload, dict) else []
    kinds = json.dumps(errors).lower()
    return {
        'wall_timeout': run['wall_timeout'],
        'engine_timeout': 'timeout' in kinds or run['returncode'] == 2 and 'timeout' in run['stderr'].decode('utf-8', 'replace').lower(),
        'parse_failure': any(s in kinds for s in ['parse error', 'partial parsing', 'syntax error', 'lexical error']),
        'out_of_memory': any(s in kinds for s in ['out of memory', 'outofmemory', 'memory limit']),
        'spawn_error': run['spawn_error'],
        'crash': (run['returncode'] is not None and
                  (run['returncode'] < 0 or run['returncode'] > 128) and not run['wall_timeout']),
        'invalid_json': payload is None,
        'nonzero_exit': run['returncode'] != 0,
        'engine_error': bool(errors),
        'skipped_target': bool(payload and payload.get('paths', {}).get('skipped')),
    }


def normalize(payload, case, policies):
    """SOP spelling only. No label comparison, anchor matching or role inference."""
    output = []
    for ordinal, hit in enumerate(payload.get('results', [])):
        rule_id = hit['check_id']
        policy = policies.get(rule_id)
        if policy is None:
            raise ValueError(f'Unmapped rule: {rule_id}')
        assert policy['operation'] in OPERATIONS and policy['role'] in ROLES
        start, end = hit['start'], hit['end']
        output.append({
            'case_id': case['case_id'], 'repository': case.get('repository'),
            'commit': case.get('commit'), 'path': case.get('path'),
            'source_sha256': case['source_sha256'], 'rule_id': rule_id,
            'raw_result_index': ordinal, 'start': start, 'end': end,
            'predicted_presence': policy['presence'], 'predicted_operation': policy['operation'],
            'predicted_role': policy['role'], 'predicted_context': 'unknown',
            'uncertainty_reason': policy['uncertainty_reason'],
            'evidence_kind': policy['evidence_kind'],
            'metavariables': hit.get('extra', {}).get('metavars', {}),
            'gold_alignment': 'pending_operation_unit_decision',
        })
    return output


def scan_case(case, output, source_root, download, engine, timeout, deadline, policies):
    case_dir = output / 'raw' / case['case_id']
    case_dir.mkdir(parents=True, exist_ok=False)
    result = {'case_id': case['case_id'], 'source_sha256': case['source_sha256'],
              'language': case['language'], 'source_status': 'unavailable', 'findings': []}
    try:
        data = acquire(case, source_root, download)
    except (OSError, ValueError) as exc:
        result.update(source_error=str(exc), status='source_failure')
        write_json(case_dir / 'record.json', result)
        return result
    target = case_dir / ('input.py' if case['language'] == 'python' else 'input.go')
    target.write_bytes(data)
    config = HERE / 'rules' / f"{case['language']}.yaml"
    command = [engine, 'scan', '--oss-only', '--config', str(config), '--json',
               '--metrics=off', '--disable-version-check', '--no-git-ignore',
               '--no-rewrite-rule-ids', '--strict', '--jobs=1',
               '--timeout', str(timeout), '--timeout-threshold=1', '--max-memory=512',
               '--max-target-bytes=5000000', '--verbose', str(target)]
    run = execute(command, case_dir, deadline)
    (case_dir / 'stdout.json').write_bytes(run['stdout'])
    (case_dir / 'stderr.txt').write_bytes(run['stderr'])
    try:
        payload = json.loads(run['stdout'])
        if not isinstance(payload, dict) or not isinstance(payload.get('results'), list) or not isinstance(payload.get('errors'), list):
            payload = None
    except (ValueError, UnicodeDecodeError):
        payload = None
    flags = classify(run, payload)
    # A clean invocation must explicitly confirm that its sole target was scanned.
    if payload is not None and not payload.get('paths', {}).get('scanned'):
        flags['skipped_target'] = True
    result.update(source_status='verified', command=command,
                  returncode=run['returncode'], seconds=run['seconds'], flags=flags,
                  status='incomplete' if any(flags.values()) else 'complete',
                  raw_stdout_sha256=digest(run['stdout']), raw_stderr_sha256=digest(run['stderr']),
                  errors=payload.get('errors', []) if payload else [])
    if payload is not None:
        try:
            result['findings'] = normalize(payload, case, policies)
        except (KeyError, ValueError, TypeError) as exc:
            result.update(status='incomplete', mapping_error=str(exc))
    write_json(case_dir / 'record.json', result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='New directory; never overwrite a run')
    parser.add_argument('--source-root', type=Path, default=HERE / '.source-cache')
    parser.add_argument('--download', action='store_true')
    parser.add_argument('--semgrep', default='semgrep')
    parser.add_argument('--timeout', type=int, default=30, help='Seconds per rule/file')
    parser.add_argument('--deadline', type=int, default=120, help='Wall seconds per scanner process tree')
    parser.add_argument('--workers', type=int, default=2)
    args = parser.parse_args(argv)
    if min(args.timeout, args.deadline, args.workers) < 1:
        parser.error('Limits must be positive')
    manifest_path = args.manifest.resolve()
    manifest = load_manifest(manifest_path)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    (output / 'manifest.json').write_bytes(manifest_path.read_bytes())
    version = execute([args.semgrep, '--version'], output, 30)
    (output / 'version.stdout.txt').write_bytes(version['stdout'])
    (output / 'version.stderr.txt').write_bytes(version['stderr'])
    actual_version = version['stdout'].decode('utf-8', 'replace').strip()
    identity = {'schema_version': 'semgrep-baseline-1', 'expected_semgrep': VERSION,
                'actual_semgrep': actual_version, 'python': sys.version, 'platform': platform.platform(),
                'manifest_sha256': digest(manifest_path.read_bytes()),
                'rule_sha256': {p.name: digest(p.read_bytes()) for p in sorted((HERE / 'rules').glob('*.yaml'))},
                'policy_sha256': digest((HERE / 'mapping.json').read_bytes()),
                'runner_sha256': digest(Path(__file__).read_bytes()),
                'limits': {'rule_timeout_seconds': args.timeout, 'process_deadline_seconds': args.deadline,
                           'max_memory_mb': 512, 'workers': args.workers, 'semgrep_jobs': 1},
                'scoring': 'disabled; no gold labels are read; no accuracy comparison',
                'mapping_issue': 'https://github.com/Ratneshp1122/PQMigrate/issues/1'}
    write_json(output / 'run.json', identity)
    if version['returncode'] != 0 or actual_version != VERSION:
        write_json(output / 'summary.json', {'status': 'engine_version_failure', 'case_count': len(manifest['cases']),
                   'cases_not_run': [c['case_id'] for c in manifest['cases']], 'accuracy': None})
        return 2
    policies = json.loads((HERE / 'mapping.json').read_text(encoding='utf-8'))
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(scan_case, case, output, args.source_root.resolve(), args.download,
                               args.semgrep, args.timeout, args.deadline, policies) for case in manifest['cases']]
        results = []
        for case, future in zip(manifest['cases'], futures):
            try:
                results.append(future.result())
            except Exception as exc:
                # Preserve unexpected harness failures, never silently drop a case.
                record = {'case_id': case['case_id'], 'status': 'harness_failure', 'error': repr(exc), 'findings': []}
                write_json(output / 'raw' / case['case_id'] / 'harness-failure.json', record)
                results.append(record)
    with (output / 'ledger.jsonl').open('w', encoding='utf-8', newline='\n') as f:
        for result in results:
            f.write(json.dumps(result, sort_keys=True) + '\n')
    counts = {status: sum(r['status'] == status for r in results) for status in sorted({r['status'] for r in results})}
    write_json(output / 'summary.json', {'case_count': len(results), 'statuses': counts,
               'finding_count': sum(len(r['findings']) for r in results),
               'accuracy': None, 'gold_lock': 'not supplied',
               'interpretation': 'Execution/finding counts only; not precision, recall, TPR or agreement'})
    print(json.dumps({'cases': len(results), 'statuses': counts, 'output': str(output)}))
    return 0 if all(r['status'] == 'complete' for r in results) else 2


if __name__ == '__main__':
    raise SystemExit(main())
