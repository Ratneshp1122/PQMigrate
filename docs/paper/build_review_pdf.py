"""Build an IEEE-style review PDF from the paper's Markdown editorial source.

This is a review layout, not a substitute for venue-specific IEEE PDF checks.
Requires reportlab, pypdf, and installed Times/DejaVu fonts. The standalone
IEEEtran .tex file is the submission-format source.
"""
from pathlib import Path
import html
import re
import textwrap
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Table, TableStyle, KeepTogether, Spacer, Preformatted, Flowable, FrameBreak
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'PQMIGRATE_RESEARCH_PAPER_IEEE.md'
OUTPUT = ROOT / 'PQMIGRATE_RESEARCH_PAPER_IEEE.pdf'
FONT_ROOT = Path('C:/Windows/Fonts')
for name, file in [('Paper','times.ttf'),('Paper-Bold','timesbd.ttf'),('Paper-Italic','timesi.ttf'),('Paper-BoldItalic','timesbi.ttf'),('Math','DejaVuSerif.ttf'),('Mono','DejaVuSansMono.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(FONT_ROOT/file)))
pdfmetrics.registerFontFamily('Paper', normal='Paper', bold='Paper-Bold', italic='Paper-Italic', boldItalic='Paper-BoldItalic')

PAGE_W, PAGE_H = A4
LEFT, RIGHT, TOP, BOTTOM, GAP = 42, 42, 46, 45, 18
COL = (PAGE_W-LEFT-RIGHT-GAP)/2
styles = {
    'body': ParagraphStyle('body',fontName='Paper',fontSize=10,leading=12,alignment=TA_JUSTIFY,spaceAfter=5,firstLineIndent=10,splitLongWords=True),
    'abstract': ParagraphStyle('abstract',fontName='Paper-Bold',fontSize=9,leading=11,alignment=TA_JUSTIFY,spaceAfter=7),
    'section': ParagraphStyle('section',fontName='Paper',fontSize=10,leading=12,alignment=TA_CENTER,spaceBefore=11,spaceAfter=6,keepWithNext=True),
    'subsection': ParagraphStyle('subsection',fontName='Paper-Italic',fontSize=10,leading=12,spaceBefore=7,spaceAfter=4,keepWithNext=True),
    'table': ParagraphStyle('table',fontName='Paper',fontSize=8,leading=9.4,spaceAfter=0),
    'caption': ParagraphStyle('caption',fontName='Paper',fontSize=8,leading=9.6,alignment=TA_CENTER,spaceBefore=5,spaceAfter=5),
    'ref': ParagraphStyle('ref',fontName='Paper',fontSize=8,leading=9.7,spaceAfter=5,leftIndent=14,firstLineIndent=-14,splitLongWords=True),
    'math': ParagraphStyle('math',fontName='Math',fontSize=8.5,leading=13,alignment=TA_CENTER,spaceAfter=5,spaceBefore=5),
    'code': ParagraphStyle('code',fontName='Mono',fontSize=7,leading=9,spaceBefore=4,spaceAfter=5),
}


def math_inline(s):
    replacements = {
      r'\operatorname{Coverage}_{O}':'Coverage<sub>O</sub>',
      r'\operatorname{Acc}_{A}':'Acc<sub>A</sub>',r'\operatorname{Acc}_{O}':'Acc<sub>O</sub>',
      r'\rho':'ρ',r'\bot':'⊥',r'\subseteq':'⊆',r'\sum_s':'Σ<sub>s</sub>',
      r'\log':'log',r'\kappa':'κ',r'\land':'∧',
    }
    for a,b in replacements.items(): s=s.replace(a,b)
    s=re.sub(r'_\{([^}]+)\}',r'<sub>\1</sub>',s)
    s=re.sub(r'_([a-zA-Z])',r'<sub>\1</sub>',s)
    if '\\' in s: raise ValueError('Unsupported inline math: '+s)
    return '<nobr><font name="Math" size="9">'+s+'</font></nobr>'


def inline(s):
    held=[]
    def hold(v):
        held.append(v)
        return f'ZZTOKEN{len(held)-1}ZZ'
    s=re.sub(r'\\\((.*?)\\\)',lambda m:hold(math_inline(m[1])),s)
    s=re.sub(r'`([^`]+)`',lambda m:hold('<font name="Mono" size="7.4">'+html.escape(m[1])+'</font>'),s)
    s=re.sub(r'https?://\S+',lambda m:hold('<link href="'+html.escape(m[0],quote=True)+'">'+html.escape(m[0])+'</link>'),s)
    s=html.escape(s)
    s=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',s)
    s=re.sub(r'\*([^*]+)\*',r'<i>\1</i>',s)
    for i,v in enumerate(held): s=s.replace(f'ZZTOKEN{i}ZZ',v)
    return s


EQUATIONS = [
    ['ρ(x) = S   if a supported signature use is linked',
     '           T   if encryption consumes a tracked secret',
     '           C   if linked encryption has unresolved purpose',
     '           ⊥   if no supported use or roles conflict'],
    ['π(x,K<sub>v</sub>) = advise(t,B)   if a compatible rule matches',
     '                   abstain(B)   otherwise'],
    ['G(x) = R(x) ∧ C(x) ∧ I(x) ∧ T(x) ∧ A(x)'],
    ['P = TP/(TP + FP),    R = TP/(TP + FN)',
     'F<sub>1</sub> = 2PR/(P + R)'],
    ['Coverage<sub>O</sub> = |A|/|O|,    Acc<sub>A</sub> = |C|/|A|',
     'Acc<sub>O</sub> = |C|/|O|'],
    ['κ = (p<sub>o</sub> − p<sub>e</sub>)/(1 − p<sub>e</sub>)'],
]


class Equation(Flowable):
    def __init__(self,index):
        super().__init__()
        self.index=index
        self.width=COL
        self.height=64 if index==1 else 39 if index==2 else 40 if index in (4,5) else 27

    def draw(self):
        c=self.canv
        c.setFont('Paper',8)
        c.drawRightString(COL,self.height/2-3,f'({self.index})')
        if self.index in (1,2):
            label='ρ(x) =' if self.index==1 else 'π(x,Kᵥ) ='
            label_width=34 if self.index==1 else 47
            c.setFont('Math',8.5)
            c.drawString(0,self.height/2-3,label)
            x=label_width+5
            mid=self.height/2
            top=self.height-5
            bottom=5
            brace=c.beginPath()
            brace.moveTo(x+7,top)
            brace.curveTo(x+1,top,x+2,mid+7,x,mid+3)
            brace.curveTo(x-1,mid+1,x-3,mid,x-5,mid)
            brace.curveTo(x-3,mid,x-1,mid-1,x,mid-3)
            brace.curveTo(x+2,mid-7,x+1,bottom,x+7,bottom)
            c.setLineWidth(.8)
            c.drawPath(brace)
            if self.index==1:
                pairs=[('S','linked signature use'),('T','encryption of a tracked secret'),('C','encryption, purpose unresolved'),('⊥','no supported use or conflicting roles')]
                for j,(term,condition) in enumerate(pairs):
                    y=self.height-14-j*13
                    c.setFont('Math',8.5)
                    c.drawString(label_width+19,y,term)
                    c.setFont('Paper',8.5)
                    c.drawString(label_width+34,y,'if '+condition)
            else:
                for j,line in enumerate(['advise(t,B)   if a compatible rule matches','abstain(B)    otherwise']):
                    c.setFont('Paper',8.5)
                    c.drawString(label_width+16,self.height-14-j*13,line)
        else:
            p=Paragraph('<br/>'.join(EQUATIONS[self.index-1]),styles['math'])
            _,h=p.wrap(COL-20,self.height)
            p.drawOn(c,0,(self.height-h)/2)


def equation(index):
    return Equation(index)


def page(canvas,doc):
    canvas.saveState()
    canvas.setFont('Paper',8)
    canvas.setFillColor(colors.HexColor('#555555'))
    canvas.drawString(LEFT,25,'PQMigrate | Internal research draft | 4 October 2026')
    canvas.drawRightString(PAGE_W-RIGHT,25,str(doc.page))
    if doc.page==1:
        title=Paragraph('PQMigrate: Evidence-Driven and Abstention-Aware Planning for Post-Quantum Cryptographic Migration',ParagraphStyle('title',fontName='Paper',fontSize=22,leading=25,alignment=TA_CENTER))
        w,h=title.wrap(PAGE_W-LEFT-RIGHT,120)
        y=PAGE_H-34-h
        title.drawOn(canvas,LEFT,y)
        author=Paragraph('Deepak Uplaonkar, Ratnesh Patnaik, Saravanan Kumar,<br/>Vaibhavi Shah, and Prince Ostwal',ParagraphStyle('authors',fontName='Paper',fontSize=10,leading=13,alignment=TA_CENTER))
        w,h=author.wrap(PAGE_W-LEFT-RIGHT,50)
        y-=h+11
        author.drawOn(canvas,LEFT,y)
        canvas.setFont('Paper-Italic',8)
        canvas.drawCentredString(PAGE_W/2,y-13,'Affiliations and corresponding-author email pending')
    canvas.restoreState()


def build():
    lines=SOURCE.read_text(encoding='utf-8').splitlines()
    story=[]
    i=lines.index('## Abstract')+1
    abstract=True
    references=False
    reference_items=[]
    eq=0
    tables=0
    while i<len(lines):
        line=lines[i].strip()
        if not line:
            i+=1
            continue
        if line.startswith('**Index Terms:**'):
            story.append(Paragraph(inline(line),styles['abstract']))
            abstract=False
        elif line.startswith('## '):
            references=line=='## References'
            if not references:
                story.append(Paragraph(inline(line[3:]).upper(),styles['section']))
        elif line.startswith('### '):
            story.append(Paragraph(inline(line[4:]),styles['subsection']))
        elif line==r'\[':
            while lines[i].strip()!=r'\]': i+=1
            eq+=1
            story.append(equation(eq))
        elif line.startswith('```'):
            code=[]
            i+=1
            while not lines[i].startswith('```'):
                code.extend(textwrap.wrap(lines[i],width=54,break_long_words=True,break_on_hyphens=False) or [''])
                i+=1
            story.append(Preformatted('\n'.join(code),styles['code']))
        elif line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].startswith('|'):
                cells=[c.strip() for c in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?',c) for c in cells): rows.append(cells)
                i+=1
            while not lines[i].strip(): i+=1
            caption=lines[i].strip()
            tables+=1
            n=len(rows[0])
            if rows[0][0]=='Module': widths=[.26,.37,.37]
            elif n==3: widths=[.37,.11,.52]
            elif rows[0][1]=='TP/FP/FN/TN': widths=[.30,.235,.155,.155,.155]
            elif n==5: widths=[.34,.165,.165,.165,.165]
            else: widths=[.22,.16,.16,.15,.145,.165]
            widths=[v/sum(widths)*COL for v in widths]
            if n==6:
                rows[0]=['Synthetic split','Total / scored','Gold ops.','TP/FN','F1','Coverage on O']
            data=[[Paragraph(('<b>'+inline(c)+'</b>') if j==0 else inline(c),styles['table']) for c in row] for j,row in enumerate(rows)]
            t=Table(data,colWidths=widths,hAlign='LEFT',repeatRows=1)
            t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),2),('RIGHTPADDING',(0,0),(-1,-1),2),('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3),('LINEABOVE',(0,0),(-1,0),.6,colors.black),('LINEBELOW',(0,0),(-1,0),.4,colors.black),('LINEBELOW',(0,-1),(-1,-1),.6,colors.black)]))
            story.append(KeepTogether([Paragraph(inline(caption),styles['caption']),t,Spacer(1,6)]))
        else:
            if abstract: line='**Abstract—** '+line
            style='abstract' if abstract else 'ref' if references else 'body'
            item=Paragraph(inline(line),styles[style])
            if references: reference_items.append(item)
            else: story.append(item)
        i+=1
    assert eq==6 and tables==5
    # Reviewed seven-page layout: balance the last page after reference four.
    # Recheck this break when the editorial source changes.
    story.extend([Paragraph('REFERENCES',styles['section']),*reference_items[:4],FrameBreak(),*reference_items[4:]])
    doc=BaseDocTemplate(str(OUTPUT),pagesize=A4,leftMargin=LEFT,rightMargin=RIGHT,topMargin=TOP,bottomMargin=BOTTOM,title=lines[0][2:],author=lines[2],subject='IEEE-style internal review manuscript; completed 72-case pilot',pageCompression=1)
    fullheight=PAGE_H-TOP-BOTTOM
    firstheight=PAGE_H-181-BOTTOM
    def frames(height):
        return [Frame(LEFT,BOTTOM,COL,height,id='left',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0),Frame(LEFT+COL+GAP,BOTTOM,COL,height,id='right',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)]
    doc.addPageTemplates([PageTemplate(id='First',frames=frames(firstheight),onPage=page,autoNextPageTemplate='Later'),PageTemplate(id='Later',frames=frames(fullheight),onPage=page)])
    doc.build(story)
    reader=PdfReader(OUTPUT)
    extracted='\n'.join(p.extract_text() for p in reader.pages)
    for required in ['0.870','0.880','52','72','References','2307.06520','Cohen','XI. PLANNED EVALUATION']:
        assert required.lower() in extracted.lower(),required
    print(f'Generated {OUTPUT.name}: {len(reader.pages)} pages, {tables} tables, {eq} equations')
    print(f'Extracted {len(extracted.split())} words; {len(reader.pages)} pages require visual review.')


if __name__=='__main__':
    build()
