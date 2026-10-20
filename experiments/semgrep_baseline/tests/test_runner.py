import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('baseline_runner', ROOT / 'runner.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


def test_manifest_rejects_labels_duplicates_and_traversal(tmp_path):
    case = dict(case_id='one', language='python', source='x()', source_sha256=r.digest(b'x()'))
    p = tmp_path / 'manifest.json'
    for cases in [[dict(case, gold_presence='yes')], [case, case],
                  [dict(case, case_id='../outside')]]:
        p.write_text(json.dumps({'cases': cases}))
        with pytest.raises(ValueError):
            r.load_manifest(p)


def test_hash_mismatch_never_scans(tmp_path):
    case = dict(case_id='one', language='python', source='x()', source_sha256='0'*64)
    result = r.scan_case(case, tmp_path, tmp_path, False, 'MUST_NOT_EXECUTE', 1, 1, {})
    assert result['status'] == 'source_failure'
    assert not (tmp_path / 'raw/one/stdout.json').exists()


def test_partial_parse_keeps_findings_and_unresolved_semantics():
    payload = {'errors': [{'type': 'Partial parsing'}], 'results': [
        {'check_id': 'candidate', 'start': {'line': 2, 'col': 3}, 'end': {'line': 2, 'col': 8}},
        {'check_id': 'candidate', 'start': {'line': 2, 'col': 3}, 'end': {'line': 2, 'col': 8}}]}
    flags = r.classify(dict(returncode=3, stderr=b'', wall_timeout=False, spawn_error=False), payload)
    assert flags['parse_failure'] and flags['nonzero_exit']
    policies = {'candidate': dict(presence='uncertain', operation='uncertain', role='uncertain',
        uncertainty_reason='Unresolved receiver', evidence_kind='unresolved_call_syntax')}
    hits = r.normalize(payload, dict(case_id='one', source_sha256='0'*64), policies)
    assert len(hits) == 2 and hits[1]['raw_result_index'] == 1
    assert hits[0]['predicted_role'] == 'uncertain'
    assert r.normalize({'results': []}, {}, {}) == []  # no finding is not a negative label


def test_timeout_crash_and_spawn_error_preserve_bytes(tmp_path):
    slow = r.execute([sys.executable, '-c', 'import time; print("partial", flush=True); time.sleep(10)'], tmp_path, 1)
    assert slow['wall_timeout'] and b'partial' in slow['stdout']
    crash = r.execute([sys.executable, '-c', 'import sys; sys.stderr.buffer.write(b"failure"); sys.exit(139)'], tmp_path, 5)
    assert r.classify(crash, None)['crash'] and crash['stderr'] == b'failure'
    missing = r.execute([str(tmp_path / 'missing-engine')], tmp_path, 1)
    assert missing['spawn_error'] and missing['stderr']


def test_version_failure_accounts_for_every_input_and_refuses_overwrite(tmp_path):
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps({'cases': [dict(case_id='one', language='python', source='',
        source_sha256=r.digest(b''))]}))
    output = tmp_path / 'run'
    args = ['--manifest', str(manifest), '--output', str(output), '--semgrep', str(tmp_path / 'missing')]
    assert r.main(args) == 2
    summary = json.loads((output / 'summary.json').read_text())
    assert summary['cases_not_run'] == ['one'] and summary['accuracy'] is None
    with pytest.raises(FileExistsError):
        r.main(args)


def test_policy_matches_sop():
    for policy in json.loads((ROOT / 'mapping.json').read_text()).values():
        assert policy['operation'] in r.OPERATIONS and policy['role'] in r.ROLES
        if 'uncertain' in (policy['presence'], policy['operation'], policy['role']):
            assert policy['uncertainty_reason']
        if policy['presence'] == 'no':
            assert policy['operation'] == policy['role'] == 'none'
