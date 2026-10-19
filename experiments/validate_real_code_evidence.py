"""Verify recorded provenance, evidence integrity, and blank annotation packets."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

run = Path(sys.argv[1]).resolve()
summary = json.loads((run / 'summary.json').read_text())
protocol = json.loads((run / 'protocol.json').read_text())
checksums = json.loads((run / 'checksums.json').read_text())
for rel, expected in checksums.items():
    assert hashlib.sha256((run / rel).read_bytes()).hexdigest() == expected, rel
assert len(summary['repositories']) == 6
assert summary['scanner_commit'] == protocol['scanner_commit'] == 'bcfb5e40fbc8eb74e1c919114f54031d03ab44e9'
assert summary['accuracy_metrics'] is None
total_files = total_findings = known = 0
known_examples = []
for item in summary['repositories']:
    assert item['status'] == 'scan_complete', item['repository']
    assert item['target_clean_after']
    out = run / item['repository'].replace('/', '__')
    report = json.loads((out / 'report.json').read_text())
    ledger = json.loads((out / 'file-ledger.json').read_text())
    assert report['source_commit'] == item['commit']
    assert report['total_findings'] == len(report['records']) == item['findings']
    assert report['files_scanned'] == sum(f['eligible_by_scanner_policy'] for f in ledger['files'])
    assert item['exit_code'] in (0, 1)
    total_files += report['files_scanned']
    total_findings += len(report['records'])
    for record in report['records']:
        finding = record['finding']
        if finding['role'] != 'unknown':
            known += 1
            known_examples.append({'repository': item['repository'], 'finding': finding})
    # On WSL, recheck every audited file hash and target revision against disk.
    target = Path(item['path'])
    if target.exists():
        actual = subprocess.check_output(['git', '-C', str(target), 'rev-parse', 'HEAD'], text=True).strip()
        assert actual == item['commit']
        for row in ledger['files']:
            if 'source_sha256' in row:
                assert hashlib.sha256((target / row['path']).read_bytes()).hexdigest() == row['source_sha256']
cases = [json.loads(line) for line in (run / 'annotation-candidates.jsonl').read_text().splitlines()]
assert len(cases) == len({c['case_id'] for c in cases}) == 240
for name in ['annotator-a', 'annotator-b']:
    packet = [json.loads(line) for line in (run / (name + '.jsonl')).read_text().splitlines()]
    assert [c['case_id'] for c in packet] == [c['case_id'] for c in cases]
    assert all(c['annotation_status'] == 'unreviewed' and c['gold_role'] is None and c['gold_presence'] is None for c in packet)
    assert all('prediction' not in c and 'matching_report_records' not in c for c in packet)
result = {'status': 'pass', 'checksummed_files': len(checksums), 'repositories': 6, 'files_reported': total_files,
          'findings': total_findings, 'known_role_records': known, 'unknown_role_records': total_findings-known,
          'annotation_candidates': len(cases), 'independently_reviewed_cases': 0,
          'known_role_examples': known_examples}
print(json.dumps(result, indent=2))
(run / 'validation.json').write_text(json.dumps(result, indent=2) + '\n')
