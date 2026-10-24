"""Compile the unfrozen author-review draft and retain compact build provenance."""
import os
from pathlib import Path
import re
import subprocess
from pcc.resources import sha256
from .common import ROOT, OUT, CACHE, write, utc
from . import draft


def main():
    draft.main()
    source=ROOT/'paper/overnight_author_review.tex'
    command=['latexmk','-cd','-pdf','-interaction=nonstopmode','-halt-on-error',str(source.relative_to(ROOT))]
    env=os.environ.copy()
    for name in ('TEXINPUTS','BSTINPUTS'):
        env[name]=str(ROOT/'artifacts/public_assets')+':'+env.get(name,'')
    log=CACHE/'latex.log'
    with log.open('w') as stream:
        result=subprocess.run(command,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT)
    inputs=[source,ROOT/'paper/references.bib',ROOT/'artifacts/public_assets/svproc.cls',ROOT/'artifacts/public_assets/splncs03.bst']
    for target in re.findall(r'\\(?:input|includegraphics)(?:\[[^\]]*\])?\{([^}]+)\}',source.read_text()):
        path=(source.parent/target).resolve()
        if not path.suffix:path=path.with_suffix('.tex')
        inputs.append(path)
    pdf=source.with_suffix('.pdf')
    record={'built_utc':utc(),'classification':'Interim author review; human scientific authorship and validation pending',
      'command':command,'returncode':result.returncode,'log_path':str(log.relative_to(ROOT)),'log_sha256':sha256(log),
      'inputs':{str(p.relative_to(ROOT)):sha256(p) for p in sorted(set(inputs))},
      'pdf_path':str(pdf.relative_to(ROOT)),'pdf_sha256':sha256(pdf) if pdf.exists() and result.returncode==0 else None,
      'tex_engine':subprocess.check_output(['pdflatex','--version'],text=True).splitlines()[0],
      'reproducibility':'Tables and figures derive from the linked analysis manifests. PDF metadata includes build time; byte identity across builds is not claimed.'}
    write(OUT/'PAPER_BUILD.json',record)
    if result.returncode:raise RuntimeError(f'Author-review build failed; see {log}')
    print({'paper':record['pdf_path'],'build_manifest':str((OUT/'PAPER_BUILD.json').relative_to(ROOT))})


if __name__=='__main__':main()
