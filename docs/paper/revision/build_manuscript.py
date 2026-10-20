"""Build one integrated manuscript without historical performance result pages."""
from pathlib import Path
import argparse
import hashlib
import html
import io
import json
import re

from pypdf import PdfReader, PdfWriter
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, PageBreak

HERE = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def prose(markdown, output, offset=0):
    body = ParagraphStyle('body', fontName='Times-Roman', fontSize=10, leading=12,
                          alignment=TA_JUSTIFY, spaceAfter=6)
    heading = ParagraphStyle('head', parent=body, fontName='Times-Bold', fontSize=11,
                             leading=13, spaceBefore=8, spaceAfter=6, keepWithNext=True)
    title = ParagraphStyle('title', parent=heading, fontSize=14, leading=16)
    bibliography = ParagraphStyle('bibliography', parent=body, fontSize=9, leading=10.5, spaceAfter=5)
    doc = BaseDocTemplate(output, pagesize=(612, 792), leftMargin=43, rightMargin=43,
                          topMargin=43, bottomMargin=43)
    frames = [Frame(43, 43, 253, 706, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0),
              Frame(316, 43, 253, 706, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)]

    def decorate(canvas, doc):
        canvas.setFont('Times-Roman', 8)
        canvas.drawString(43, 770, 'PQMigrate | Research Paper Draft 5 | 21 October 2026')
        canvas.drawRightString(569, 770, str(doc.page+offset))
        canvas.setStrokeColorRGB(.7, .7, .7)
        canvas.line(43, 761, 569, 761)
    doc.addPageTemplates(PageTemplate(id='two-column', frames=frames, onPage=decorate))
    story = []
    for block in re.split(r'\n\s*\n', markdown.strip()):
        block = block.strip()
        # A forced page marker may follow a paragraph without a blank line.
        parts = block.split('<!-- PAGE -->')
        for index, part in enumerate(parts):
            part = part.strip()
            if index:
                story.append(PageBreak())
            if not part:
                continue
            style = title if part.startswith('# ') else heading if part.startswith('## ') else bibliography if re.match(r'^\[\d+\]', part) else body
            part = re.sub(r'^#{1,2} ', '', part)
            escaped = html.escape(part).replace('\n', ' ')
            escaped = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', escaped)
            # Keep very long pinned identifiers/URLs inside the column.
            escaped = re.sub(r'([a-f0-9]{20})([a-f0-9]{20})', r'\1<font size="1"> </font>\2', escaped)
            story.append(Paragraph(escaped, style))
    doc.build(story)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--original', type=Path, default=HERE/'source/Draft3.pdf')
    parser.add_argument('--output', type=Path, default=HERE.parent/'output/pdf/PQMigrate_ResearchPaper_Updated.pdf')
    args=parser.parse_args()
    refs=json.loads((HERE/'references.json').read_text(encoding='utf-8'))
    reference_md='## References\n\n'+'\n\n'.join(
        f"[{r['id']}] {r['citation']} [Online]. Available: {r['url']}" for r in refs)
    manuscript=((HERE/'front.md').read_text(encoding='utf-8').strip()+'\n\n'+
                (HERE/'back.md').read_text(encoding='utf-8').strip()+'\n\n')
    (HERE/'manuscript.md').write_text(manuscript+reference_md+'\n',encoding='utf-8')
    (HERE.parent/'PQMIGRATE_PAPER_DRAFT_V0_1.md').write_text(manuscript+reference_md+'\n',encoding='utf-8')
    rendered=io.BytesIO()
    prose(manuscript+'\n<!-- PAGE -->\n'+reference_md,rendered)
    writer=PdfWriter()
    for p in PdfReader(rendered).pages: writer.add_page(p)
    writer.add_metadata({'/Title':'PQMigrate: Evidence-Driven and Abstention-Aware Planning for Post-Quantum Cryptographic Migration',
                         '/Subject':'Draft 5; integrated revision; historical performance results removed; real-code evaluation ongoing'})
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('wb') as f: writer.write(f)
    result=PdfReader(args.output)
    text='\n'.join(p.extract_text() for p in result.pages)
    for old_marker in ['Table II.', 'Table III.', 'Table IV.', 'Table V.',
                       '40/52', '40/40', '0.870', '0.769', 'Draft 3', 'Draft 4']:
        assert old_marker not in text, old_marker
    for number in range(1,len(refs)+1):
        assert f'[{number}]' in text
    audit=dict(original_sha256=sha(args.original.read_bytes()),revised_sha256=sha(args.output.read_bytes()),
        page_count=len(result.pages),citation_count=len(refs),
        verification_date='2026-10-21',historical_result_pages_removed=True,
        note='One integrated manuscript; historical performance tables, plots and numerical findings removed at author request. No replacement accuracy calculated.')
    (HERE/'build-audit.json').write_text(json.dumps(audit,indent=2)+'\n',newline='\n')
    print(json.dumps(audit,indent=2))


if __name__=='__main__': main()
