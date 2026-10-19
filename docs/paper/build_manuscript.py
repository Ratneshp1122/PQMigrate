"""Render the reviewed Markdown manuscript as standalone IEEEtran LaTeX.

No network calls or external assets. Markdown remains the editorial source.
Run with Python 3 from any working directory; output is beside this script.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'PQMIGRATE_RESEARCH_PAPER_IEEE.md'
TARGET = ROOT / 'PQMIGRATE_RESEARCH_PAPER_IEEE.tex'


def inline(text, citations=True):
    held = []

    def keep(value):
        held.append(value)
        return f'ZZTOKEN{len(held)-1}ZZ'

    text = re.sub(r'\\\((.*?)\\\)', lambda m: keep('\\(' + m[1] + '\\)'), text)
    text = re.sub(r'`([^`]+)`', lambda m: keep(r'\path{' + m[1] + '}'), text)
    text = re.sub(r'https?://\S+', lambda m: keep(r'\url{' + m[0] + '}'), text)
    if citations:
        text = re.sub(r'\[(\d+)\]', lambda m: keep(r'\cite{ref' + m[1] + '}'), text)
    escaped = {'\\':r'\textbackslash{}', '&':r'\&', '%':r'\%', '$':r'\$', '#':r'\#', '_':r'\_', '{':r'\{', '}':r'\}', '~':r'\textasciitilde{}', '^':r'\textasciicircum{}'}
    text = ''.join(escaped.get(c, c) for c in text)
    text = text.replace('\u201c', '``').replace('\u201d', "''").replace('\u2019', "'")
    text = re.sub(r'\*\*(.+?)\*\*', r'\\textbf{\1}', text)
    text = re.sub(r'\*([^*]+)\*', r'\\emph{\1}', text)
    for i, value in enumerate(held):
        text = text.replace(f'ZZTOKEN{i}ZZ', value)
    return text


def build():
    lines = SOURCE.read_text(encoding='utf-8').splitlines()
    title = lines[0][2:]
    authors = lines[2]
    out = [r'''\documentclass[conference,a4paper]{IEEEtran}
\usepackage[T1]{fontenc}
\usepackage{amsmath,amssymb}
\usepackage{array,booktabs}
\usepackage{listings}
\usepackage{xurl}
\usepackage[hidelinks]{hyperref}
\usepackage{cite}
\hyphenation{crypto-graphic crypto-graphy inter-operability}
\lstset{basicstyle=\ttfamily\footnotesize,breaklines=true,columns=fullflexible,keepspaces=true,frame=single,framerule=.3pt,xleftmargin=2pt,xrightmargin=2pt}
\setlength{\emergencystretch}{1.5em}
\title{''' + inline(title, False) + '}',
           r'\author{\IEEEauthorblockN{' + inline(authors, False) + r'}\IEEEauthorblockA{Internal review manuscript --- 4 October 2026\\Affiliations and corresponding-author email pending}}',
           r'\begin{document}', r'\maketitle']
    i = lines.index('## Abstract') + 1
    out.append(r'\begin{abstract}')
    refs = False
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            out.append('')
            i += 1
            continue
        if line.startswith('**Index Terms:**'):
            out.extend([r'\end{abstract}', r'\begin{IEEEkeywords}', inline(line.split('**Index Terms:**', 1)[1].strip()), r'\end{IEEEkeywords}'])
        elif line == '## References':
            refs = True
            out.append(r'\begin{thebibliography}{00}')
        elif refs:
            m = re.match(r'\[(\d+)\]\s+(.*)', line)
            if m:
                out.append(r'\bibitem{ref' + m[1] + '}' + inline(m[2], False))
            else:
                raise ValueError('Unexpected bibliography line: ' + line)
        elif line.startswith('## '):
            heading = re.sub(r'^[IVX]+\.\s+', '', line[3:])
            out.append(r'\section{' + inline(heading, False) + '}')
        elif line.startswith('### '):
            heading = re.sub(r'^[A-Z]\.\s+', '', line[4:])
            out.append(r'\subsection{' + inline(heading, False) + '}')
        elif line == r'\[':
            math = []
            i += 1
            while lines[i].strip() != r'\]':
                math.append(lines[i])
                i += 1
            out.extend([r'\begin{equation}', *math, r'\end{equation}'])
        elif line.startswith('```'):
            code = []
            i += 1
            while not lines[i].startswith('```'):
                code.append(lines[i])
                i += 1
            out.extend([r'\begin{lstlisting}', *code, r'\end{lstlisting}'])
        elif line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                cells = [v.strip() for v in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?', c) for c in cells):
                    rows.append(cells)
                i += 1
            while i < len(lines) and not lines[i].strip():
                i += 1
            caption = re.sub(r'^Table [IVX]+\.\s*', '', lines[i].strip())
            n = len(rows[0])
            if rows[0][0] == 'Module': widths = [.24,.34,.30]
            elif n == 3: widths = [.36,.09,.43]
            elif rows[0][1] == 'TP/FP/FN/TN': widths = [.29,.23,.12,.12,.12]
            elif n == 5: widths = [.33,.1375,.1375,.1375,.1375]
            else: widths = [.20,.136,.136,.136,.136,.136]
            spec = '@{}' + ''.join(r'>{\raggedright\arraybackslash}p{' + str(w) + r'\columnwidth}' for w in widths) + '@{}'
            out.extend([r'\begin{table}[!t]', r'\caption{' + inline(caption) + '}', r'\centering\scriptsize', r'\setlength{\tabcolsep}{2pt}', r'\begin{tabular}{' + spec + '}', r'\toprule'])
            for idx, row in enumerate(rows):
                out.append(' & '.join(inline(c) for c in row) + r' \\')
                if idx == 0: out.append(r'\midrule')
            out.extend([r'\bottomrule', r'\end{tabular}', r'\end{table}'])
        elif re.match(r'^\d+\. ', line):
            out.append(r'\begin{enumerate}')
            while i < len(lines) and re.match(r'^\d+\. ', lines[i]):
                out.append(r'\item ' + inline(re.sub(r'^\d+\. ', '', lines[i])))
                i += 1
            out.append(r'\end{enumerate}')
            i -= 1
        else:
            out.append(inline(line))
        i += 1
    out.extend([r'\end{thebibliography}', r'\end{document}', ''])
    TARGET.write_text('\n'.join(out), encoding='utf-8')
    print(f'Generated {TARGET.name}: {len(out)} logical lines')


if __name__ == '__main__':
    build()
