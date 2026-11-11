"""Stage only CAPM assets and render without executing code or changing the book."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[2]
STAGE=ROOT/'logs/capm/preview-project'
QUARTO=Path(os.environ.get('QUARTO_EXE',str(Path.home()/
    'AppData/Local/Programs/Quarto/bin/quarto.exe')))

CONFIG='''project:
  type: default
  output-dir: preview
  render:
    - lectures/capm.qmd
    - notebooks/capm/capm-stata.ipynb
  resources:
    - data/capm/README.md
    - data/capm/asset-comparison-*
    - lectures/capm-lecture.pdf
    - data/capm/industry_monthly.dta
    - data/capm/beta_sim.dta
    - data/capm/source.json
    - data/capm/industry_monthly-README.md
    - data/capm/beta_sim-README.md
    - data/capm/industry_monthly-source.json
    - notebooks/capm/*.ipynb
    - tools/capm/*
    - figs/raw/capm-*
execute:
  enabled: false
lang: zh
format-links: false
number-sections: true
shift-heading-level-by: -1
toc: true
toc-depth: 2
crossref:
  fig-title: 图
  tbl-title: 表
  fig-prefix: 图
  tbl-prefix: 表
  eq-prefix: 式
format:
  html:
    theme: cosmo
    css: [book.css, preview.css]
    fontsize: 17px
    linestretch: 1.7
    code-overflow: wrap
    code-fold: false
    highlight-style: github
  typst:
    papersize: a4
    margin:
      x: 23mm
      y: 23mm
    fontsize: 12pt
    mainfont: SimSun
    monofont: Consolas
    section-numbering: "1.1"
    keep-typ: true
    include-before-body: print-header.typ
'''

# Only the isolated preview is styled; palette is taken from FORMAT 1.0.
CSS='''body {color:#252b30;}
p, figcaption, .quarto-float-caption {text-align:left;}
main figcaption.quarto-float-caption {
  text-align:center !important;font-size:0.916667rem;}
main figcaption .float-number {font-weight:700;white-space:nowrap;}
main .capm-figure {margin-top:0.85rem;margin-bottom:1.7rem;}
main .capm-table {margin-block:1.7rem;}
main .capm-figure .quarto-float, main .capm-table .quarto-float {
  margin-block:0;}
main .figure-note, main .table-note {
  font-size:0.833333rem;line-height:1.5;margin-top:0.85rem;}
main .figure-note p, main .table-note p {margin-block:0;}
main section.level1 > h1, main section.level2 > h2 {
  margin-top:1.7rem;margin-bottom:1.7rem;}
main section.level1 > h1 .header-section-number::after {content:".";}
.callout {border:0.5px solid #BFC4C8;border-left-width:3.67px;}
.callout-note {border-left-color:#2878BD;background:#F4F8FC;}
.callout-note .callout-header {background:#EAF3FB;}
.callout-tip {border-left-color:#45892D;background:#F6FAF3;}
.callout-tip .callout-header {background:#EFF7E9;}
.callout-warning {border-left-color:#9A642D;background:#FCF8F1;}
.callout-warning .callout-header {background:#F9EFDF;}
.callout-reading {border-left-color:#806298;background:#F9F6FC;}
.callout-reading .callout-header {background:#F1EBF7;}
.callout-title-container {color:#424B52;}
main figure.quarto-float {margin-block:0.85rem;}
main .quarto-float-tbl {margin-block:0.85rem;}
figure img {max-width:100%;height:auto;}
table {font-variant-numeric:tabular-nums;}
main .capm-figure figure > p {margin-bottom:0.85rem;}
main .capm-figure figcaption {margin-top:0.85rem;}
main .capm-table table {border-collapse:collapse;border-top:1.5px solid #333;
  border-bottom:1.5px solid #333;}
main .capm-table th, main .capm-table td {border:0 !important;}
main .capm-table thead {border-bottom:1px solid #333;}
main .capm-table tbody tr {border:0 !important;}
main .capm-table tbody {border:0 !important;}
pre {white-space:pre-wrap;overflow-wrap:anywhere;}
main :not(pre) > code {font-size:1em;}
main .callout.callout-style-default .callout-title-container,
main .callout.callout-style-default .callout-body-container {
  font-size:0.875rem !important;}
main .callout .callout-body-container p {font-size:1em;}
'''

HEADER='''#set text(font: ("Times New Roman", "SimSun"))
#set par(justify: true, leading: 0.65em)
#show raw: set text(size: 12pt, font: ("Consolas", "SimSun"))
#show figure.caption: it => context align(center, text(size: 11pt)[
  #strong[#it.supplement #it.counter.display(it.numbering)]#h(0.6em)#it.body
])
#show heading: set text(font: ("Times New Roman", "SimSun"))
#set heading(numbering: (..nums) => {
  if nums.pos().len() == 1 {numbering("1.", ..nums)}
  else {numbering("1.1", ..nums)}
})
#show heading.where(level: 1): set text(size: 16pt, weight: "bold")
#show heading.where(level: 2): set text(size: 14pt, weight: "bold")
// Explicit, non-collapsing spacing: at least one body line above AND below (20pt net spacing).
// Wrapping only the heading keeps it with the following paragraph without
// forcing an entire section onto a fresh page.
#show heading: it => {
  set par(justify: false)
  set block(above: 0pt, below: 0pt)
  block(sticky: true, breakable: false, above: 0pt, below: 0pt)[
    #v(20pt, weak: false)
    #it
    #v(20pt, weak: false)
  ]
}
#show link: it => {
  if type(it.dest) == str and it.dest.starts-with("https://doi.org/") {
    text(fill: rgb("#1F5A96"), it)
  } else {it}
}
// SimSun 12pt + 0.65em leading gives an observed 16pt body baseline.
// Figure/table notes are followed by at least one visible body line.
#set figure(placement: none, gap: 10pt)
#set table(stroke: none)
#show table: it => block(width: 100%, stroke: (top: 0.8pt, bottom: 0.8pt), inset: 0pt, above: 0pt, below: 0pt)[#it]
#show figure: set block(above: 8pt, below: 8pt)
#let CommentTok(s) = text(fill: rgb("#6B3B00"), raw(s))
#let callout(body: [], title: [], background_color: white, icon: none,
  icon_color: black, body_background_color: white) = {
  let label = content-to-string(title)
  let palette = if label.contains("文献") {
    ("806298", "F1EBF7", "F9F6FC")
  } else if label.contains("定价限制") or label.contains("时变风险") {
    ("9A642D", "F9EFDF", "FCF8F1")
  } else if label.contains("本讲要点") {
    ("2878BD", "EAF3FB", "F4F8FC")
  } else { ("45892D", "EFF7E9", "F6FAF3") }
  let accent = rgb(palette.at(0))
  block(breakable: false, width: 100%, below: 8pt,
    stroke: (left: (paint: accent, thickness: 2.75pt),
      top: 0.5pt + rgb("BFC4C8"), right: 0.5pt + rgb("BFC4C8"),
      bottom: 0.5pt + rgb("BFC4C8")),
    block(width: 100%, fill: rgb(palette.at(1)), inset: 7pt,
      below: 0pt)[#text(fill: accent)[#icon] #text(weight: "bold",
      fill: rgb("424B52"), size: 10.5pt)[#title]] +
    block(width: 100%, fill: rgb(palette.at(2)), inset: 8pt,
      above: 0pt)[
      #set par(justify: false)
      #set text(size: 10.5pt)
      #show raw: set text(size: 10.5pt)
      #body
    ])
}
'''


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--format',choices=['html','typst'],default='html')
    args=parser.parse_args()
    STAGE.mkdir(parents=True,exist_ok=True)
    code=(ROOT/'lectures/capm.qmd').read_text(encoding='utf-8')
    figures=re.findall(r'\.\./(figs/raw/capm-[^)]+\.png)',code)
    assert figures and len(figures)==len(set(figures))
    paths=[Path('notebooks/capm/capm-stata.ipynb')]
    paths.extend(p.relative_to(ROOT) for p in sorted((ROOT/'data/capm').glob('asset-comparison-*')) if p.is_file())
    paths.extend(p.relative_to(ROOT) for p in sorted((ROOT/'tools/capm').glob('teaching_figures_*.py')) if p.is_file())
    paths.extend(p.relative_to(ROOT) for p in sorted((ROOT/'tools/capm').glob('asset_comparison_*.py')) if p.is_file())
    paths.extend(Path('data/capm')/n for n in ['README.md','industry_monthly.dta','beta_sim.dta','source.json',
        'industry_monthly-README.md','beta_sim-README.md','industry_monthly-source.json'])
    paths.extend(Path('tools/capm')/n for n in ['capm.do','run_notebook.py',
        'validate_results.py','make_beta_sim.do','prepare_data.py',
        'fetch_sources.py','build_preview.py'])
    if (ROOT/'tools/capm/README.md').exists():paths.append(Path('tools/capm/README.md'))
    paths.extend([Path('tools/capm/capm.css'),Path('lectures/capm-lecture.pdf')])
    # Both previews use the same vector SVG, preserving hollow marker paths.
    # Native Stata PDF exports are retained as source assets for other uses.
    for name in figures:
        for ext in ['.png','.svg','.pdf']:
            paths.append(Path(name).with_suffix(ext))
        suffix='.svg'
        code=code.replace('../'+name,'../'+str(Path(name).with_suffix(suffix)).replace('\\','/'))
    if args.format=='typst':
        # Keep the PDF under lectures/ so both HTML experiment and data links resolve.
        # Pandoc's highlighted code consists of inline raw tokens. Scope their
        # 8.5pt size to the code block so body commands remain actual 12pt text.
        code=re.sub(r'(?m)^```(stata|text)\n([\s\S]*?)\n```',
            lambda m:'```{=typst}\n#block(breakable: false)[\n'+
            '#set text(size: 8.5pt)\n#show raw: set text(size: 8.5pt)\n```\n\n'+
            '```'+m[1]+'\n'+m[2]+'\n```\n\n```{=typst}\n]\n```',code)
        # Source keeps a short native caption and a separate note paragraph.
        # The group keeps image/table, caption and note together in print.
        pattern=r'(?m)^:::: \{\.(capm-(?:figure|table))\}\n([\s\S]*?)\n::::'
        def float_group(match):
            spacing=16 if match[1]=='capm-table' else 8
            body=match[2]
            note=r'(?m)^::: \{\.(?:figure|table)-note\}\n([\s\S]*?)\n:::'
            body=re.sub(note,lambda n:'```{=typst}\n#v(10pt, weak: false)\n#block(above: 0pt, below: 0pt)[\n#set text(size: 10pt)\n#set par(justify: false)\n```\n\n'+n[1]+'\n\n```{=typst}\n]\n```',body)
            return ('```{=typst}\n#block(breakable: false, above: '+str(spacing)+
                    'pt, below: 0pt)[\n'+
                    '#show figure: set block(width: 100%, above: 0pt, below: 0pt)\n```\n'+
                    body+'\n\n```{=typst}\n#v(20pt, weak: false)\n]\n```')
        code=re.sub(pattern,float_group,code)
        # Keep the explanation introducing an equation with that equation.
        # This prevents a floating graph from separating the two across pages.
        pattern=r'(?m)^([^\n]+)\n\n(\$\$\n[\s\S]+?\n\$\$ \{#eq-capm-[^\n]+\})'
        code=re.sub(pattern,lambda m:'```{=typst}\n#block(breakable: false)[\n```\n\n'+
                    m[1]+'\n\n'+m[2]+'\n\n```{=typst}\n]\n```',code)
        # References and exercises flow naturally; no forced page break or
        # whole-section nonbreakable wrapper is added.
    for rel in paths:
        target=STAGE/rel;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(ROOT/rel,target)
    target=STAGE/'lectures/capm.qmd';target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(code,encoding='utf-8')
    for name,body in [('_quarto.yml',CONFIG),('preview.css',CSS),('print-header.typ',HEADER)]:
        (STAGE/name).write_text(body,encoding='utf-8')
    shutil.copy2(ROOT/'styles.css',STAGE/'book.css')
    inputs=['lectures/capm.qmd'] if args.format=='typst' else [
        'lectures/capm.qmd','notebooks/capm/capm-stata.ipynb']
    results=[]
    for name in inputs:
        command=[str(QUARTO),'render',name,'--to',args.format,'--no-execute']
        if args.format=='html' and name.endswith('.ipynb'):
            # Keep the real unnumbered H1 in standalone previews. Book rendering
            # uses that same H1 to omit the chapter counter; never rewrite source.
            command.extend(['-M','shift-heading-level-by:0'])
        r=subprocess.run(command,cwd=STAGE,text=True,encoding='utf-8',errors='replace',capture_output=True)
        (ROOT/f'logs/capm/render-{args.format}-{Path(name).stem}.log').write_text(
            r.stdout+'\n'+r.stderr,encoding='utf-8')
        print(r.stdout[-1500:]+r.stderr[-3500:])
        results.append({'input':name,'returncode':r.returncode})
        if r.returncode:raise SystemExit(r.returncode)
        if args.format=='html':
            page=STAGE/'preview'/Path(name).with_suffix('.html')
            html=page.read_text(encoding='utf-8')
            # The number remains generated by Quarto; only its presentation changes.
            prefix=r'(<figcaption\b[^>]*>\s*)(图|表)(?:&nbsp;|\s+)([0-9.]+):?\s*'
            html=re.sub(prefix,lambda m:m[1]+'<strong class="float-number">'+m[2]+'&nbsp;'+m[3]+'</strong> ',html)
            # Quarto does not retain the source callout-prompt class.
            html=re.sub(r'(<div class=")(callout [^"\n]+)("[^>]*title="提示词 [^"]+"[^>]*>)',
                lambda m:m[1]+m[2]+' capm-prompt'+m[3],html)
            page.write_text(html,encoding='utf-8')
        if args.format=='html' and name.endswith('.ipynb'):
            # Default (non-book) previews do not rewrite this source link.
            # Adapt only derived HTML; the downloadable notebook is intact.
            page=STAGE/'preview/notebooks/capm/capm-stata.html'
            html=page.read_text(encoding='utf-8')
            html=html.replace('href="../../lectures/capm.qmd"',
                              'href="../../lectures/capm.html"')
            # A default-project notebook has no extracted book title.
            # Set only this derived HTML tab title; retain the real source H1.
            html=re.sub(r'<title>[\s\S]*?</title>',
                        '<title>CAPM：Stata 完整实验</title>',html,count=1)
            page.write_text(html,encoding='utf-8')
    report={'format':args.format,'execution_enabled':False,'results':results,
        'notebook_preview_link_mapping':{'../../lectures/capm.qmd':'../../lectures/capm.html'},
        'source_qmd_sha256':hashlib.sha256((ROOT/'lectures/capm.qmd').read_bytes()).hexdigest(),
        'figure_mapping':{p:str(Path(p).with_suffix('.svg'))
                          for p in figures}}
    (ROOT/f'logs/capm/render-{args.format}.json').write_text(json.dumps(report,indent=2),encoding='utf-8')


if __name__=='__main__':main()
