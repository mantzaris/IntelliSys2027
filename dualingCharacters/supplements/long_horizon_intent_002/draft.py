"""Compile a separate anonymous author-review draft using the existing svproc template."""
from pathlib import Path
from datetime import datetime
import os
import re
import shutil
import subprocess
from pcc.resources import sha256
from .common import ROOT,HERE,REPORTS,ARTIFACTS,read,write,utc


def escape(text):
    conversions={'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}',
      '−':'--','–':'--','—':'---','→':r'$\rightarrow$','≥':r'$\geq$','≤':r'$\leq$','’':"'",'“':'``','”':"''",'×':r'$\times$'}
    return ''.join(conversions.get(c,c) for c in text.replace('`','').replace('**',''))


def convert_markdown(text):
    lines=text.splitlines();out=[];i=0
    while i<len(lines):
        line=lines[i]
        if line.startswith('# '):i+=1;continue
        if line.startswith('## '):out.append(r'\section{'+escape(line[3:])+'}');i+=1;continue
        if line.startswith('|'):
            table=[]
            while i<len(lines) and lines[i].startswith('|'):
                cells=[x.strip() for x in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r'[-:]+',x) for x in cells):table.append(cells)
                i+=1
            n=len(table[0]);out.extend([r'\begin{center}\scriptsize',r'\resizebox{\linewidth}{!}{\begin{tabular}{'+'l'*n+'}',r'\toprule'])
            for j,row in enumerate(table):
                if len(row)!=n:raise ValueError('Markdown table column mismatch')
                out.append(' & '.join(escape(c) for c in row)+r' \\')
                if j==0:out.append(r'\midrule')
            out.extend([r'\bottomrule\end{tabular}}',r'\end{center}']);continue
        out.append(escape(line));i+=1
    return '\n'.join(out)


def main():
    source=HERE/'MANUSCRIPT_SECTION.md';directory=REPORTS/'draft';directory.mkdir(exist_ok=True);build=ARTIFACTS/'draft_build';build.mkdir(parents=True,exist_ok=True)
    abstract=('This exploratory follow-up asks whether character-conditioned supervised adapter training preserves expressed user intent over long conversations, even when average task performance is lower. '
      'We distinguish horizon robustness, trajectory robustness, and variation across training seeds. Existing structured planning evaluations are analyzed without changing their frozen conditions, checkpoints, or queue. '
      'Each intermediate response is compared with its time-specific task state, and source availability, clarification behavior, and actual supervised-target exposure are audited separately. '
      'The completed seed-specific comparisons are heterogeneous and do not establish a consistent advantage attributable to character training. The scheduled matched-horizon interaction remains pending. '
      'A separate authored benchmark covers software, research, editorial, and operator collaboration through substantive natural-language work products. Sixteen families have paired authorized and hypothetical revisions at three controlled horizons. '
      'A private intent ledger grounds evaluation but never enters policy observations or memory. The proposed primary score combines late-conversation adherence with the worse paired world; helpful progress is rated separately. '
      'Fresh inference is gated behind the required core and prior review, under a two-hour subcap and one session deadline. Human ratings and fresh qualitative results remain pending. This package is an author-review draft, not a completed submission.')
    tex=r'''\documentclass{svproc}
\usepackage{url,graphicx,booktabs,amsmath,mathptmx}
\usepackage[hidelinks]{hyperref}
\hypersetup{pdfauthor={},pdftitle={Long-Horizon Intent Robustness: Exploratory Author Review}}
\begin{document}\mainmatter
\title{Long-Horizon Intent Robustness: An Exploratory Follow-Up}
\titlerunning{Long-Horizon Intent Robustness}
\author{Anonymous author(s)}\authorrunning{Anonymous}
\institute{Author-review draft; incomplete evidence, not for submission}
\maketitle
\begin{abstract}
'''+escape(abstract)+r'''
\keywords{conversational state, intent adherence, supervised adapters, recovery}
\end{abstract}
\noindent\textbf{Status:} This AI-assisted, author-directed draft requires human review of scientific decisions, arguments, results, and conclusions. It is not presented as a policy-compliant finished submission. No new qualitative model outcomes or human annotations are invented.

'''+convert_markdown(source.read_text())
    for name,caption in [('core_horizon_level_and_change','Existing Qwen seed17 horizon study on48 paired families. Missing32- and128-turn cells and interactions remain pending. No curve is inferred through missing horizons.'),('dynamic_core_trajectories','Completed Qwen C1/C3/C5 seed-specific64-turn trajectories,480 conversations each. Correctness is evaluated against the time-varying oracle. Missing seed cells remain pending; turns are not independent experimental subjects.')]:
        figure=REPORTS/'intent_figures'/f'{name}.pdf'
        if figure.exists():tex+='\n'+r'\begin{figure}[ht]\centering\includegraphics[width=\linewidth]{'+str(figure)+r'}\caption{'+escape(caption)+r'}\end{figure}'+'\n'
    tex+='\n'+r'\end{document}'+'\n';texpath=directory/'intent_author_review.tex';texpath.write_text(tex)
    tool=shutil.which('pdflatex')
    if not tool:
        write(REPORTS/'DRAFT_STATUS.json',{'status':'source_ready_compilation_unavailable','missing_tool':'pdflatex','source_sha256':sha256(texpath)});return
    epoch=int(datetime.fromisoformat(read(HERE/'SESSION.json')['started_utc']).timestamp())
    environment={**os.environ,'TEXINPUTS':str(ROOT/'artifacts/public_assets')+'//:'+os.environ.get('TEXINPUTS',''),
      'SOURCE_DATE_EPOCH':str(epoch),'FORCE_SOURCE_DATE':'1','TZ':'UTC'}
    log=build/'compilation.log'
    with log.open('w') as stream:
        result=subprocess.run([tool,'-interaction=nonstopmode','-halt-on-error','-output-directory='+str(build),str(texpath)],cwd=HERE,env=environment,stdout=stream,stderr=subprocess.STDOUT,timeout=60)
    pdf=build/'intent_author_review.pdf';status={'generated_utc':utc(),'status':'compiled_author_review_only' if result.returncode==0 else 'compile_failed',
      'exit_code':result.returncode,'source_sha256':sha256(texpath),'markdown_sha256':sha256(source),'abstract_words':len(abstract.split()),
      'template_sha256':sha256(ROOT/'artifacts/public_assets/svproc.cls'),'compilation_log':str(log.relative_to(ROOT)),
      'scientific_status':'Incomplete core grid; fresh qualitative results and human validation pending. No submission-readiness or compliance assertion.'}
    if result.returncode==0:
        shutil.copy2(pdf,directory/pdf.name);status.update(pdf_path=str((directory/pdf.name).relative_to(ROOT)),pdf_sha256=sha256(directory/pdf.name))
    write(REPORTS/'DRAFT_STATUS.json',status)
    if result.returncode:raise RuntimeError('Draft compile failed; inspect '+str(log))
    print({'compiled_draft':status['pdf_path'],'abstract_words':status['abstract_words']})


if __name__=='__main__':main()
