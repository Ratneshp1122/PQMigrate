"""Build a professional proposal PDF from researched, explicitly proposed content."""
from pathlib import Path
import html
import json
import re
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon
from pypdf import PdfReader

HERE=Path(__file__).resolve().parent
INK=colors.HexColor('#182a3a')
ACCENT=colors.HexColor('#284b63')
LIGHT=colors.HexColor('#eef2f5')
WIDTH=A4[0]-108


def para(text,style):
    return Paragraph(html.escape(text),style)


def architecture():
    d=Drawing(WIDTH,136)
    gap=8; bw=(WIDTH-3*gap)/4
    def box(x,y,w,h,title,sub=None):
        d.add(Rect(x,y,w,h,fillColor=LIGHT,strokeColor=ACCENT,strokeWidth=.6))
        d.add(String(x+w/2,y+h/2+(2 if sub else -3),title,fontName='Helvetica-Bold',fontSize=8.5,textAnchor='middle',fillColor=INK))
        if sub:d.add(String(x+w/2,y+6,sub,fontName='Helvetica',fontSize=7,textAnchor='middle',fillColor=INK))
    for i,(title,sub) in enumerate([('CryptoScan','Inventory candidates'),('Semgrep CE','Source-rule findings'),("Where's Crypto?",'Binary candidates'),('CRYLOGGER','Android observations')]):
        x=i*(bw+gap);box(x,100,bw,33,title,sub)
        d.add(Line(x+bw/2,100,x+bw/2,88,strokeColor=ACCENT,strokeWidth=.7))
    box(0,58,WIDTH,30,'Versioned adapters and evidence store','Native outputs  |  artifact identity  |  failures and uncertainty')
    d.add(Line(WIDTH/2,58,WIDTH/2,45,strokeColor=ACCENT,strokeWidth=.7))
    box(0,11,WIDTH,34,'Role review and conditional migration plans','Evidence panel  |  unresolved cases  |  blockers  |  traceable exports')
    return d


def build():
    content=json.loads((HERE/'proposal_content.json').read_text(encoding='utf-8'))
    sources=json.loads((HERE/'integration_sources.json').read_text(encoding='utf-8'))
    out=HERE.parents[1]/'proposals/PQMigrate_Integration_Proposal.pdf'
    out.parent.mkdir(parents=True,exist_ok=True)
    body=ParagraphStyle('body',fontName='Helvetica',fontSize=10,leading=13.6,spaceAfter=8,textColor=INK)
    lead=ParagraphStyle('lead',parent=body,fontName='Helvetica-Bold',fontSize=10.4,leading=14.2,spaceAfter=12)
    title=ParagraphStyle('title',parent=body,fontName='Helvetica-Bold',fontSize=21,leading=25,spaceAfter=9)
    subtitle=ParagraphStyle('sub',parent=body,fontSize=12,leading=16,spaceAfter=12)
    heading=ParagraphStyle('h',parent=body,fontName='Helvetica-Bold',fontSize=13.5,leading=17,spaceBefore=4,spaceAfter=9,keepWithNext=True)
    subhead=ParagraphStyle('h2',parent=heading,fontSize=10.8,leading=14,spaceBefore=5,spaceAfter=5)
    cell=ParagraphStyle('cell',parent=body,fontSize=9,leading=11.5,spaceAfter=0)
    headcell=ParagraphStyle('headcell',parent=cell,fontName='Helvetica-Bold',textColor=colors.white)
    reference=ParagraphStyle('ref',parent=body,fontSize=8.4,leading=10.8,spaceAfter=8)
    doc=SimpleDocTemplate(str(out),pagesize=A4,leftMargin=54,rightMargin=54,topMargin=48,bottomMargin=43,
        title=content['title'],author='PQMigrate project team')
    story=[]
    def table(spec):
        rows=[[para(t,headcell) for t in spec['headers']]]
        rows.extend([[para(t,cell) for t in row] for row in spec['rows']])
        t=Table(rows,colWidths=[WIDTH*w for w in spec['widths']],repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),ACCENT),('VALIGN',(0,0),(-1,-1),'TOP'),
            ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),
            ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,LIGHT]),
            ('LINEBELOW',(0,-1),(-1,-1),.5,colors.HexColor('#b8c4cc')),
        ]))
        return t
    for i,page in enumerate(content['pages']):
        if i:story.append(PageBreak())
        if i==0:
            story.extend([para(content['title'],title),para(content['subtitle'],subtitle),
                para(content['prepared_for']+' | '+content['date'],body),Spacer(1,8)])
        else:story.append(para(f"{i+1}  {page['title']}",heading))
        story.append(para(page['lead'],lead))
        if page.get('architecture'):
            story.extend([architecture(),para('Figure 1  Proposed evidence flow and review workflow',reference),Spacer(1,6)])
        for section in page['sections']:
            story.append(para(section['heading'],subhead))
            if 'table' in section:story.extend([table(section['table']),Spacer(1,9)])
            for text in section.get('paragraphs',[]):story.append(para(text,body))
    story.extend([PageBreak(),para('8  References and evidence basis',heading),
        para('Primary documentation reviewed on 21 October 2026. Vendor pages describe advertised capabilities, not independently verified effectiveness. Project estimates and acceptance gates in this proposal are proposed assumptions.',body)])
    for source in sources:
        story.append(para(f"[{source['id']}] {source['title']}. {source['url']}",reference))
    def decorate(canvas,doc):
        canvas.setFont('Helvetica',8)
        canvas.setFillColor(colors.HexColor('#526372'))
        if doc.page>1:canvas.drawString(54,A4[1]-27,'PQMigrate integration proposal')
        canvas.drawRightString(A4[0]-54,24,str(doc.page))
    doc.build(story,onFirstPage=decorate,onLaterPages=decorate)
    text='\n'.join(p.extract_text() for p in PdfReader(out).pages)
    for name in ['CryptoScan','Semgrep',"Where's Crypto?",'CRYLOGGER','95 percent']:
        assert name in text,name
    assert len(PdfReader(out).pages)<=10,'Unexpected document overflow'
    print(f'Proposal: {len(PdfReader(out).pages)} pages; {out}')


if __name__=='__main__':build()
