"""Verify preserved bytes and complete accounting, without reading any gold."""
import hashlib
import json
from pathlib import Path
import zipfile

HERE=Path(__file__).resolve().parent


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verify(path):
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        checks=json.loads(z.read('ARCHIVE-SHA256.json'))
        assert set(z.namelist())==set(checks)|{'ARCHIVE-SHA256.json'}
        for name,expected in checks.items():
            assert digest(z.read(name))==expected, name
        identity=json.loads(z.read('run.json'))
        assert identity['runner_sha256']==digest((HERE/'runner.py').read_bytes())
        assert identity['policy_sha256']==digest((HERE/'mapping.json').read_bytes())
        for name,sha in identity['rule_sha256'].items():
            assert sha==digest((HERE/'rules'/name).read_bytes())
        assert identity['manifest_sha256']==digest(z.read('manifest.json'))
        manifest=json.loads(z.read('manifest.json'))
        ledger=[json.loads(line) for line in z.read('ledger.jsonl').splitlines()]
        ids=[case['case_id'] for case in manifest['cases']]
        assert [row['case_id'] for row in ledger]==ids
        assert len(set(ids))==len(ids)
        summary=json.loads(z.read('summary.json'))
        assert summary['case_count']==len(ids) and summary['accuracy'] is None
        assert summary['finding_count']==sum(len(row['findings']) for row in ledger)
        for row in ledger:
            base='raw/'+row['case_id']+'/'
            assert json.loads(z.read(base+'record.json'))==row
            if row.get('source_status')=='verified':
                assert digest(z.read(base+'stdout.json'))==row['raw_stdout_sha256']
                assert digest(z.read(base+'stderr.txt'))==row['raw_stderr_sha256']
        print(f'{path.name}: hashes and accounting verified for {len(ids)} inputs; unscored')


if __name__=='__main__':
    for path in sorted((HERE/'results').glob('*.zip')):
        verify(path)
