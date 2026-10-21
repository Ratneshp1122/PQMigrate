"""Preserve original paper pages and append explicitly proposed integration work."""
from pathlib import Path
import hashlib
import html
import io
import json
import re
from pypdf import PdfReader, PdfWriter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph

HERE=Path(__file__).resolve().parent
ORIGINAL_SHA256='6cde5495e7cc16b88c274e78a6f75e244401465c894f52f61dff4e61fbbaf2d7'


def appendix(original):
    font_dir=Path('C:/Windows/Fonts')
    if (font_dir/'times.ttf').is_file():
        pdfmetrics.registerFont(TTFont('PaperTimes',str(font_dir/'times.ttf')))
        pdfmetrics.registerFont(TTFont('PaperTimesBold',str(font_dir/'timesbd.ttf')))
        normal,bold='PaperTimes','PaperTimesBold'
    else:normal,bold='Times-Roman','Times-Bold'
    width,height=map(float,[original.pages[0].mediabox.width,original.pages[0].mediabox.height])
    col=(width-72-18)/2
    stream=io.BytesIO()
    doc=BaseDocTemplate(stream,pagesize=(width,height),leftMargin=36,rightMargin=36,topMargin=43,bottomMargin=43)
    frames=[Frame(x,43,col,height-89,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0) for x in [36,36+col+18]]
    def header(canvas,doc):
        canvas.setFont(normal,8)
        canvas.drawString(36,height-25,'PQMigrate | Proposed future work | 21 October 2026')
        canvas.drawRightString(width-36,height-25,str(len(original.pages)+doc.page))
    doc.addPageTemplates(PageTemplate(id='original-style',frames=frames,onPage=header))
    body=ParagraphStyle('body',fontName=normal,fontSize=10,leading=11.5,spaceAfter=6,alignment=TA_JUSTIFY)
    heading=ParagraphStyle('h',parent=body,fontName=bold,fontSize=10,leading=12,spaceBefore=8,spaceAfter=5,keepWithNext=True,alignment=TA_LEFT)
    ref=ParagraphStyle('ref',parent=body,fontSize=8.2,leading=9.2,spaceAfter=3,alignment=TA_LEFT)
    story=[]
    for block in re.split(r'\n\s*\n',(HERE/'future_work.md').read_text(encoding='utf-8').strip()):
        style=heading if block.startswith('#') else ref if block.startswith('[A') else body
        block=re.sub(r'^#{1,2} ','',block).replace('\n',' ')
        story.append(Paragraph(html.escape(block),style))
    doc.build(story)
    return PdfReader(stream),normal


def main():
    source=HERE/'source/Draft3.pdf'
    output=HERE.parent/'output/pdf/PQMigrate_ResearchPaper_Updated.pdf'
    data=source.read_bytes()
    assert hashlib.sha256(data).hexdigest()==ORIGINAL_SHA256
    output.parent.mkdir(parents=True,exist_ok=True)
    original=PdfReader(io.BytesIO(data))
    added,font=appendix(original)
    writer=PdfWriter()
    for page in original.pages:writer.add_page(page)
    for page in added.pages:writer.add_page(page)
    writer.add_metadata({'/Title':'PQMigrate: Evidence-Driven and Abstention-Aware Planning for Post-Quantum Cryptographic Migration',
                         '/Subject':'Original eight pages preserved; proposed four-tool integration appended; no new accuracy claims'})
    with output.open('wb') as f:writer.write(f)
    rendered=PdfReader(output)
    preserved=[]
    for number,(before,after) in enumerate(zip(original.pages,rendered.pages),1):
        assert before.extract_text()==after.extract_text()
        assert before.get_contents().get_data()==after.get_contents().get_data()
        assert list(before.mediabox)==list(after.mediabox)
        preserved.append({'page':number,'content_sha256':hashlib.sha256(after.get_contents().get_data()).hexdigest()})
    audit={
        'source_sha256':ORIGINAL_SHA256,
        'output_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
        'page_count':len(rendered.pages),
        'original_page_count':len(original.pages),
        'original_page_streams_and_text_preserved':True,
        'preserved_pages':preserved,
        'appendix_pages':len(added.pages),
        'appendix_font':font,
        'theory_and_wording_changed':False,
        'original_page_formatting_changed':False,
        'numbers_or_graphs_changed':False,
        'eligible_annotation_metrics_available':False,
        'status':'proposed future-work appendix added; integration and market superiority unvalidated',
        'source_audit_sha256':hashlib.sha256((HERE/'integration_sources.json').read_bytes()).hexdigest(),
        'note':'Original paper pages and results unchanged. The appendix proposes CryptoScan, Semgrep, Where\'s Crypto? and CRYLOGGER adapters and an independent evaluation; it reports no achieved 95-percent superiority.',
    }
    (HERE/'build-audit.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(audit,indent=2))


if __name__=='__main__':main()
