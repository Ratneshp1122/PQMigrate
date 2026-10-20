"""Preserve exact unscored output bytes in a deterministic, source-free ZIP."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


def archive(run):
    summary=json.loads((run/'summary.json').read_text(encoding='utf-8'))
    if summary.get('accuracy') is not None:
        raise ValueError('This archive accepts unscored runs only')
    target=run.with_suffix('.zip')
    checksums={}
    with target.open('xb') as stream, zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(run.rglob('*')):
            if not p.is_file() or p.name in {'input.py','input.go','semgrep-settings.yml'}:
                continue
            rel=p.relative_to(run).as_posix()
            data=p.read_bytes()
            checksums[rel]=hashlib.sha256(data).hexdigest()
            info=zipfile.ZipInfo(rel,date_time=(1980,1,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,data)
        info=zipfile.ZipInfo('ARCHIVE-SHA256.json',date_time=(1980,1,1,0,0,0))
        z.writestr(info,json.dumps(checksums,indent=2,sort_keys=True)+'\n')
    with zipfile.ZipFile(target) as z:
        assert z.testzip() is None
        for name,sha in checksums.items():
            assert hashlib.sha256(z.read(name)).hexdigest()==sha
    print(json.dumps(dict(archive=str(target),files=len(checksums),
                         sha256=hashlib.sha256(target.read_bytes()).hexdigest())))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run',type=Path)
    archive(parser.parse_args().run)
