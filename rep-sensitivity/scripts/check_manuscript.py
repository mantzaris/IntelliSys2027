"""Check the actual single-source PDF, citations, layout and anonymous metadata."""
import json
from pathlib import Path
import re
import subprocess
from manuscript_content import validate_single_source, reference_record

tex=Path('manuscript/main.tex').read_text()
log=Path('manuscript/main.log').read_text()
validate_single_source(tex,Path('manuscript'))
assert list(Path('manuscript').rglob('*.tex'))==[Path('manuscript/main.tex')]
abstract=tex.split(r'\begin{abstract}',1)[1].split(r'\keywords',1)[0]
abstract=re.sub(r'(?<!\\)%[^\n]*','',abstract)
words=abstract.split()  # Count numerical terms too; LaTeX comments are removed above.
assert 150<=len(words)<=250,len(words)
assert not re.search(r'Overfull \\[hv]box|undefined on input|There were undefined references|multiply defined',log)
cited={x.strip() for g in re.findall(r'\\cite\{([^}]+)\}',tex) for x in g.split(',')}
entries=set(re.findall(r'\\bibitem\{([^}]+)\}',tex))
assert cited==entries,(cited-entries,entries-cited)
labels=set(re.findall(r'\\label\{((?:fig|tab):[^}]+)\}',tex))
references=set(re.findall(r'\\ref\{([^}]+)\}',tex))
assert labels<=references,('Figures/tables not discussed in text',labels-references)
verification=json.loads(reference_record(tex).read_text())
assert {e['key'] for e in verification['entries']}==entries
assert len(entries)>=20
assert tex.rfind(r'\section')==tex.index(r'\section*{Declaration on AI Assistance}')
assert tex.index(r'\appendix')<tex.index(r'\section*{Declaration on AI Assistance}')<tex.index(r'\begin{thebibliography}')
assert r'\author{Anonymous}' in tex and r'\authorrunning{Anonymous}' in tex
assert not re.search(r'mantzaris|IntelliSys2027|/home/resort|github\.com/.+rep-sensitivity',tex,re.I)
info=subprocess.check_output(['pdfinfo','manuscript/main.pdf'],text=True)
assert re.search(r'^Author:\s+Anonymous\s*$',info,re.M),info
pages=int(re.search(r'Pages:\s+(\d+)',info)[1])
page_text=subprocess.check_output(['pdftotext','-layout','manuscript/main.pdf','-'],text=True).split('\f')
appendix_start=next(i+1 for i,p in enumerate(page_text) if re.search(r'^\s*A\s+Reproducibility and Output Semantics\s*$',p,re.M))
references_start=next(i+1 for i,p in enumerate(page_text) if re.search(r'^\s*References\s*$',p,re.M))
# Explicit clearpage before appendix gives an unambiguous main-text boundary.
main_pages=appendix_start-1
reference_appendix_pages=pages-main_pages
assert main_pages<=18,(main_pages,'main-text pages')
assert reference_appendix_pages<=7,(reference_appendix_pages,'appendices and references')
assert pages<=25
figures=re.findall(r'\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}',tex)
assert len(figures)==len(set(figures))
assert not any(p.exists() for p in (Path('manuscript/references.bib'),Path('manuscript/generated')))
result={'abstract_words':len(words),'pages':pages,'main_text_pages':main_pages,
 'appendix_start_page':appendix_start,'references_start_page':references_start,
 'reference_appendix_pages':reference_appendix_pages,'figure_count':len(figures),
 'bibliography_entries':len(entries),'all_entries_verified_and_cited':True,
 'all_figures_and_tables_referenced':True,
 'single_tex_source':True,'inline_bibliography':True,'figures_beside_source':True,
 'anonymous_pdf_author':True,'undefined_references':False,'overfull_boxes':False,
 'disclosure_is_final_prose_section':True,'human_scientific_review':'pending','submission_ready':False}
Path('records/manuscript-checks.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
