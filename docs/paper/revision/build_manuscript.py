"""Preserve the original PDF until locked annotation results support numeric edits."""
from pathlib import Path
import hashlib
import json
from pypdf import PdfReader

HERE=Path(__file__).resolve().parent
ORIGINAL_SHA256='6cde5495e7cc16b88c274e78a6f75e244401465c894f52f61dff4e61fbbaf2d7'


def main():
    source=HERE/'source/Draft3.pdf'
    output=HERE.parent/'output/pdf/PQMigrate_ResearchPaper_Updated.pdf'
    data=source.read_bytes()
    assert hashlib.sha256(data).hexdigest()==ORIGINAL_SHA256
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_bytes(data)
    assert output.read_bytes()==data
    audit={
        'source_sha256':ORIGINAL_SHA256,
        'output_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
        'page_count':len(PdfReader(output).pages),
        'original_pdf_preserved_byte_for_byte':True,
        'theory_and_wording_changed':False,
        'formatting_changed':False,
        'numbers_or_graphs_changed':False,
        'eligible_annotation_metrics_available':False,
        'status':'awaiting completed, locked independent annotations and comparable metrics',
        'note':'The clean A packet remains unreviewed. Unscored Semgrep findings are not annotation accuracy and cannot justify numeric replacements.',
    }
    (HERE/'build-audit.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(audit,indent=2))


if __name__=='__main__':main()
