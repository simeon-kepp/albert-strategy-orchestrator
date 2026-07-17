#!/usr/bin/env python3
"""
RFI-IRFOS Report Generator  (obsidian / black-mirror theme)
===========================================================
JSON spec  ->  branded LaTeX  ->  forensic PDF (xelatex), gold-standard format.

Dark on EVERY page (obsidian slate), not just the cover: the document reads as an
interdisciplinary investigation dossier, not a white app-security checklist.

Usage:
    python3 gen_report.py <spec.json> <output.pdf>

Modes:
    "direct"      -> abuse/malware report, NO engagement offer (scam/criminal apps
                     reported straight to platform + regulators, e.g. Merge Chicken).
    "engagement"  -> coordinated disclosure to a legitimate operator, INCLUDES the
                     tiered offer block.

Schema: see README.md. Requires xelatex, Inter, DejaVu Sans Mono, the RFI logo PNG.
"""
import json, os, sys, re, subprocess, shutil, tempfile

LOGO = "/home/eri-irfos/Desktop/Downloads/rfi_irfos_logo_transparent.png"

_ESC = {'\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#',
        '_': r'\_', '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}'}
def esc(s):
    if s is None: return ''
    return ''.join(_ESC.get(c, c) for c in str(s))

def wrap_long_tokens(s):
    # long unbroken runs (hashes, package ids, domains) don't hyphenate on their own and
    # can blow out a fixed-width table column; seqsplit inserts breakpoints between chars.
    return re.sub(r'(\S{20,})', lambda m: '\\seqsplit{%s}' % m.group(1), s)

SEV_COLOR = {'CRITICAL': 'rfi-red', 'HIGH': 'rfi-red', 'MEDIUM': 'rfi-amber', 'LOW': 'rfi-gray'}
SEV_BOX   = {'CRITICAL': 'critbox', 'HIGH': 'critbox', 'MEDIUM': 'medbox', 'LOW': 'lowbox'}

PREAMBLE = r"""%!TEX program = xelatex
\documentclass[11pt,a4paper]{article}
\usepackage{fontspec}\usepackage{geometry}\usepackage{xcolor}\usepackage{colortbl}
\usepackage{fancyhdr}\usepackage[explicit]{titlesec}\usepackage{hyperref}
\usepackage{longtable}\usepackage{booktabs}\usepackage{array}\usepackage{enumitem}
\usepackage{listings}\usepackage[most]{tcolorbox}\usepackage{graphicx}
\usepackage{setspace}\usepackage{microtype}\usepackage{parskip}\usepackage{afterpage}\usepackage{pagecolor}\usepackage{eso-pic}\usepackage{atbegshi}
\usepackage{seqsplit}\let\cleardoublepage\clearpage
\setmainfont{Inter}[UprightFont=*-Regular,BoldFont=*-Bold,ItalicFont=*-Italic,BoldItalicFont=*-BoldItalic,Scale=1.0]
\setmonofont{DejaVu Sans Mono}[Scale=0.82]
\geometry{a4paper, top=22mm, bottom=24mm, left=22mm, right=22mm, headheight=14pt, headsep=8mm}
\tolerance=9999\emergencystretch=3em\hyphenpenalty=50\exhyphenpenalty=50\sloppy
% ── obsidian palette ──
\definecolor{rfi-dark}{RGB}{10,15,30}\definecolor{rfi-accent}{RGB}{0,180,216}
\definecolor{rfi-teal}{RGB}{0,200,170}\definecolor{rfi-red}{RGB}{235,80,95}
\definecolor{rfi-amber}{RGB}{255,176,32}\definecolor{rfi-gray}{RGB}{140,150,170}
\definecolor{rfi-bg}{RGB}{245,247,250}\definecolor{cover-bg}{RGB}{8,11,22}
\definecolor{rfi-text}{RGB}{214,220,232}\definecolor{rfi-panel}{RGB}{20,26,44}
\definecolor{rfi-codebg}{RGB}{5,8,15}\definecolor{rfi-white}{RGB}{240,243,248}
\definecolor{rfi-brown}{RGB}{150,105,65}\definecolor{rfi-purple}{RGB}{160,120,225}
\definecolor{rfi-yellow}{RGB}{235,215,80}\definecolor{rfi-green}{RGB}{95,205,115}
\definecolor{rfi-blue}{RGB}{80,165,230}\definecolor{rfi-closed}{RGB}{75,80,95}
\hypersetup{colorlinks=true, linkcolor=rfi-accent, urlcolor=rfi-accent, pdftitle={__PDFTITLE__}, pdfauthor={RFI-IRFOS Research Team}}
\arrayrulecolor{rfi-gray!55}
\AtBeginShipout{\AtBeginShipoutUpperLeft{\color{cover-bg}\rule{\paperwidth}{\paperheight}}}
\titleformat{\section}{\large\bfseries\color{rfi-white}}{}{0pt}{#1}[{\color{rfi-accent}\vspace{2pt}\noindent\rule{\linewidth}{1.5pt}}]
\titleformat{\subsection}{\normalsize\bfseries\color{rfi-white}}{}{0pt}{#1}[{\color{rfi-accent!70}\vspace{1pt}\noindent\rule{\linewidth}{0.5pt}}]
\titleformat{\subsubsection}{\small\bfseries\color{rfi-accent!85}}{}{0pt}{\MakeUppercase{#1}}
\titlespacing*{\section}{0pt}{14pt}{6pt}\titlespacing*{\subsection}{0pt}{10pt}{4pt}\titlespacing*{\subsubsection}{0pt}{6pt}{2pt}
\pagestyle{fancy}\fancyhf{}
\fancyhead[L]{\small\color{rfi-gray}\textbf{RFI-IRFOS}}
\fancyhead[R]{\small\color{rfi-gray}__RUNHEAD__}
\fancyfoot[C]{\small\color{rfi-gray}\thepage}
\renewcommand{\headrulewidth}{0.4pt}
\renewcommand{\headrule}{\color{rfi-accent!40}\hrule width\headwidth height\headrulewidth}
\tcbset{
 findingbox/.style={colback=cover-bg, colframe=rfi-accent, coltext=rfi-text, coltitle=rfi-dark, boxrule=1.2pt, arc=3pt, left=8pt, right=8pt, top=6pt, bottom=6pt, fonttitle=\bfseries},
 critbox/.style={colback=cover-bg, colframe=rfi-red, coltext=rfi-text, coltitle=rfi-dark, boxrule=1.2pt, arc=3pt, left=8pt, right=8pt, top=6pt, bottom=6pt, fonttitle=\bfseries},
 medbox/.style={colback=cover-bg, colframe=rfi-amber, coltext=rfi-text, coltitle=rfi-dark, boxrule=1.2pt, arc=3pt, left=8pt, right=8pt, top=6pt, bottom=6pt, fonttitle=\bfseries},
 lowbox/.style={colback=cover-bg, colframe=rfi-gray, coltext=rfi-text, coltitle=rfi-dark, boxrule=1pt, arc=3pt, left=8pt, right=8pt, top=6pt, bottom=6pt, fonttitle=\bfseries},
 winbox/.style={colback=cover-bg, colframe=rfi-teal, coltext=rfi-text, coltitle=rfi-dark, boxrule=1.2pt, arc=3pt, left=8pt, right=8pt, top=6pt, bottom=6pt, fonttitle=\bfseries},
 codebox/.style={colback=rfi-codebg, colframe=rfi-accent!30, coltext=rfi-white, boxrule=0.5pt, arc=3pt, left=10pt, right=10pt, top=6pt, bottom=6pt, fontupper=\ttfamily\small}}
\lstset{basicstyle=\ttfamily\small\color{rfi-white}, backgroundcolor=\color{rfi-codebg}, breaklines=true, breakatwhitespace=false, columns=fullflexible, keepspaces=true, frame=none, xleftmargin=10pt, xrightmargin=10pt, aboveskip=6pt, belowskip=6pt}
\begin{document}\pagecolor{cover-bg}\color{rfi-text}
"""

DOT_COLOR = {'white': 'rfi-white', 'brown': 'rfi-brown', 'purple': 'rfi-purple',
             'red': 'rfi-red', 'yellow': 'rfi-yellow', 'green': 'rfi-green',
             'blue': 'rfi-blue', 'orange': 'rfi-amber', 'closed': 'rfi-closed',
             'teal': 'rfi-teal', 'gray': 'rfi-gray'}
DOT_SHAPE = {'circle': '●', 'diamond': '◆'}  # verified present in Inter Regular

def dot_cell(d):
    # {"dot": "colorname", "shape": "circle"|"diamond" (default circle), "label": "text"}
    color = DOT_COLOR.get(d.get('dot'), 'rfi-gray')
    shape = DOT_SHAPE.get(d.get('shape', 'circle'), DOT_SHAPE['circle'])
    label = esc(d.get('label', ''))
    return "\\textcolor{%s}{\\Large %s}\\ %s" % (color, shape, label)

def codebox(raw):
    return "\\begin{tcolorbox}[codebox]\n\\begin{lstlisting}\n" + (raw or '') + "\n\\end{lstlisting}\n\\end{tcolorbox}\n"

def table(headers, rows, widths=None):
    n = len(headers)
    if widths is None:
        widths = ['p{%.1fcm}' % (13.6 / n)] * n
    colspec = ''.join(widths)
    out = ["\\begin{longtable}{@{}" + colspec + "@{}}", "\\toprule",
           ' & '.join('\\textbf{\\color{rfi-white}%s}' % esc(h) for h in headers) + ' \\\\', "\\midrule", "\\endhead"]
    for r in rows:
        out.append(' & '.join((dot_cell(c) if isinstance(c, dict) else wrap_long_tokens(esc(c))) for c in r) + ' \\\\[3pt]')
    out += ["\\bottomrule", "\\end{longtable}", ""]
    return '\n'.join(out)

def block(b):
    t = b.get('type')
    if t == 'para':   return wrap_long_tokens(esc(b['text'])) + "\n\n"
    if t == 'code':   return codebox(b['lines'])
    if t == 'table':  return table(b['headers'], b['rows'], b.get('widths'))
    if t == 'bullets':
        items = '\n'.join('  \\item %s' % wrap_long_tokens(esc(i)) for i in b['items'])
        return "\\begin{itemize}[leftmargin=14pt, itemsep=2pt]\n" + items + "\n\\end{itemize}\n"
    if t == 'box':
        style = {'win': 'winbox', 'crit': 'critbox', 'finding': 'findingbox',
                 'med': 'medbox', 'low': 'lowbox'}.get(b.get('style', 'finding'), 'findingbox')
        title = (', title={%s}' % esc(b['title'])) if b.get('title') else ''
        return "\\begin{tcolorbox}[%s%s]\n%s\n\\end{tcolorbox}\n\\vspace{4pt}\n" % (style, title, wrap_long_tokens(esc(b['text'])))
    return ''

def build(spec):
    pdftitle = esc(spec.get('title', 'Security Report') + ' -- ' + spec.get('app', ''))
    runhead  = esc(spec.get('app', 'RFI-IRFOS') + ' -- ' + spec.get('runhead', 'Security Report'))
    tex = [PREAMBLE.replace('__PDFTITLE__', pdftitle).replace('__RUNHEAD__', runhead)]

    # ── COVER (page is already dark globally) ──
    # NOTE: each element below is its own paragraph (blank line between tex.append calls) —
    # letting a long title/subtitle/banner run together with the meta table as ONE paragraph
    # confuses LaTeX's line-breaking across mixed font sizes and produces large overfull boxes.
    tex.append("\\thispagestyle{empty}")
    tex.append("\\vspace*{16mm}\\includegraphics[width=7cm]{%s}\n" % LOGO)
    tex.append("\\vspace{12mm}{\\color{rfi-accent}\\rule{\\linewidth}{1.5pt}}\\vspace{6mm}\n")
    tex.append("{\\fontsize{26pt}{32pt}\\selectfont\\bfseries\\color{rfi-white}\\raggedright\n%s\\par}\n" % esc(spec.get('title', 'Security Report')))
    tex.append("\\vspace{4mm}{\\fontsize{16pt}{20pt}\\selectfont\\color{rfi-accent}\\raggedright\n%s\\par}\n" % esc(spec.get('app', '')))
    if spec.get('subtitle'):
        tex.append("\\vspace{2mm}{\\fontsize{11pt}{14pt}\\selectfont\\color{rfi-text}\\raggedright\n%s\\par}\n" % esc(spec['subtitle']))
    if spec.get('status_banner'):
        tex.append("\\vspace{8mm}\\colorbox{rfi-teal}{\\parbox{\\dimexpr\\linewidth-2\\fboxsep\\relax}{\\centering\\vspace{3pt}{\\bfseries\\color{rfi-dark}\\large %s}\\vspace{3pt}}}\n" % esc(spec['status_banner']))
    tex.append("\\vspace{8mm}{\\color{rfi-accent!40}\\rule{\\linewidth}{0.5pt}}\\vspace{6mm}\n")
    meta = spec.get('meta', [])
    rows = ' '.join("\\color{rfi-gray}\\small\\textbf{%s} & \\color{rfi-white}\\small %s \\\\[4pt]" % (esc(k), wrap_long_tokens(esc(v))) for k, v in meta)
    tex.append("\\begin{tabular}{@{}p{4.2cm}p{10.4cm}@{}}\n%s\n\\end{tabular}\n" % rows)
    if spec.get('sha256'):
        tex.append("\\vspace{8mm}{\\color{rfi-accent!40}\\rule{\\linewidth}{0.5pt}}\\vspace{6mm}\n")
        tex.append("{\\color{rfi-gray}\\small\\textbf{SHA-256 (base APK):}}\\\\[2pt]{\\color{rfi-white}\\ttfamily\\small %s}\n" % wrap_long_tokens(esc(spec['sha256'])))
    tex.append("\\vfill{\\color{rfi-gray}\\small rfi.irfos@gmail.com \\textbullet{} rfi-irfos.com}\\\\[4pt]\n{\\color{rfi-gray}\\small ZVR 1015608684 \\textbullet{} GISA 39261441 \\textbullet{} UID ATU83405245 \\textbullet{} Steuernummer 68 696/8736 \\textbullet{} Graz, Austria}")
    tex.append("\\newpage\\fancyhead[L]{\\small\\color{rfi-gray}\\textbf{RFI-IRFOS}}")
    tex.append("\\tableofcontents\\newpage\\pagecolor{cover-bg}")

    # ── EXECUTIVE SUMMARY ──
    tex.append("\\section{Executive Summary}")
    for p in spec.get('exec_summary', []):
        tex.append(esc(p) + "\n")
    if spec.get('scope'):
        tex.append("\\vspace{6pt}\\begin{tcolorbox}[findingbox]\n\\textbf{\\color{rfi-white}Scope:} %s\n\\end{tcolorbox}\\vspace{6pt}" % esc(spec['scope']))
    if spec.get('disposition'):
        tex.append("\\vspace{6pt}\\begin{tcolorbox}[winbox, title=Disposition]\n%s\n\\end{tcolorbox}\\vspace{6pt}" % esc(spec['disposition']))
    f = spec.get('findings', [])
    if f:
        rows = []
        for x in f:
            sevcol = SEV_COLOR.get(x['severity'], 'rfi-gray')
            rows.append("%s & \\textcolor{%s}{\\textbf{%s}} & %s \\\\[3pt]" % (esc(x['id']), sevcol, esc(x['severity']), esc(x['title'])))
        tex.append("\\vspace{8pt}\\begin{longtable}{@{}p{1.7cm}p{2.2cm}p{9.7cm}@{}}\\toprule\\textbf{\\color{rfi-white}ID} & \\textbf{\\color{rfi-white}Severity} & \\textbf{\\color{rfi-white}Title} \\\\\\midrule\\endhead")
        tex.append('\n'.join(rows))
        tex.append("\\bottomrule\\end{longtable}")
    tex.append("\\newpage")

    for s in spec.get('pre_sections', []):
        tex.append("\\section{%s}" % esc(s['title']))
        for b in s.get('blocks', []):
            tex.append(block(b))

    if f:
        tex.append("\\section{Findings}")
        for x in f:
            boxstyle = SEV_BOX.get(x['severity'], 'lowbox')
            tex.append("\\subsection{%s: %s}" % (esc(x['id']), esc(x['title'])))
            bt = x.get('box_title', '%s' % x['severity'])
            tex.append("\\begin{tcolorbox}[%s, title={%s}]\n%s\n\\end{tcolorbox}" % (boxstyle, esc(bt), wrap_long_tokens(esc(x.get('box_text', '')))))
            for b in x.get('blocks', []):
                tex.append(block(b))
            if x.get('impact'):
                tex.append("\\textbf{\\color{rfi-white}Impact:} %s\n" % wrap_long_tokens(esc(x['impact'])))
            if x.get('fix'):
                tex.append("\\textbf{\\color{rfi-white}Fix:} %s\n" % wrap_long_tokens(esc(x['fix'])))

    for s in spec.get('post_sections', []):
        tex.append("\\section{%s}" % esc(s['title']))
        for b in s.get('blocks', []):
            tex.append(block(b))

    if spec.get('mode') == 'engagement' and spec.get('offer'):
        tex.append("\\section{Engagement Offer}")
        tex.append("This report is provided free of charge under coordinated responsible disclosure principles. The following paid engagements are available:\\vspace{8pt}")
        tex.append(table(['Tier', 'Scope', 'Price'], spec['offer'], widths=['p{4.2cm}', 'p{7.4cm}', 'p{2.0cm}']))
        if spec.get('offer_note'):
            tex.append("\\vspace{6pt}" + esc(spec['offer_note']))

    tex.append("\\vspace{10pt}{\\color{rfi-gray!55}\\hrule}\\vspace{8pt}")
    tex.append("\\textbf{\\color{rfi-white}RFI-IRFOS} \\color{rfi-text}rfi.irfos@gmail.com \\textbullet{} rfi-irfos.com\\\\[4pt]\n{\\color{rfi-text}ZVR 1015608684 \\textbullet{} GISA 39261441 \\textbullet{} UID ATU83405245 \\textbullet{} Steuernummer 68 696/8736 \\textbullet{} Elisabethinergasse 25/10, 8020 Graz, Austria}")
    note = spec.get('footer_note', "All findings derive from static root-level analysis of the published application using publicly available tooling. No servers, accounts or infrastructure were probed. Technical evidence is archived under chain of custody and will be provided to regulatory authorities on request. Research conducted under ISO/IEC 29147, the freedom of scientific research (Art. 17 StGG) and GDPR Art. 89.")
    tex.append("\\vspace{6pt}{\\small\\color{rfi-gray}\n%s%s}" % (esc(note), (' REF ' + esc(spec['ref']) + '.') if spec.get('ref') else ''))
    tex.append("\\end{document}")
    return '\n'.join(tex)

def main():
    if len(sys.argv) != 3:
        print("usage: gen_report.py <spec.json> <output.pdf>"); sys.exit(1)
    spec = json.load(open(sys.argv[1], encoding='utf-8'))
    out = os.path.abspath(sys.argv[2])
    tex = build(spec)
    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, 'report.tex'), 'w', encoding='utf-8').write(tex)
        for _ in range(2):
            r = subprocess.run(['xelatex', '-interaction=nonstopmode', 'report.tex'],
                               cwd=d, capture_output=True, text=True)
        pdf = os.path.join(d, 'report.pdf')
        if not os.path.exists(pdf):
            sys.stderr.write(r.stdout[-3000:]); sys.exit("xelatex failed")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        shutil.copy(pdf, out)
    print("OK ->", out)

if __name__ == '__main__':
    main()
