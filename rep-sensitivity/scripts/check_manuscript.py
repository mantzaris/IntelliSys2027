"""Compile-output checks: abstract length, references, margins and anonymization."""
import json
from pathlib import Path
import re
import subprocess
tex=Path('manuscript/main.tex').read_text(); log=Path('manuscript/main.log').read_text()
abstract=tex.split(r'\begin{abstract}',1)[1].split(r'\keywords',1)[0]
abstract=re.sub(r'\\input\{([^}]+)\}',lambda m:Path('manuscript',m.group(1)).read_text(),abstract)
words=re.findall(r"[A-Za-z]+(?:[-'][A-Za-z]+)*",abstract)
assert 150<=len(words)<=250,len(words)
assert not re.search(r'Overfull \\[hv]box|undefined on input|There were undefined references',log)
cited=set(x for group in re.findall(r'\\cite\{([^}]+)\}',tex) for x in group.split(','))
entries=set(re.findall(r'@\w+\{([^,]+),',Path('manuscript/references.bib').read_text()))
assert cited==entries,(cited-entries,entries-cited)
info=subprocess.check_output(['pdfinfo','manuscript/main.pdf'],text=True)
pages=int(re.search(r'Pages:\s+(\d+)',info).group(1));assert pages<=25
page_text=subprocess.check_output(['pdftotext','-layout','manuscript/main.pdf','-'],text=True).split('\f')
reference_start=next((i+1 for i,p in enumerate(page_text) if re.search(r'^\s*References\s*$',p,re.M)),None)
assert reference_start is not None,'Cannot locate reference-page boundary'
# Count a shared boundary page conservatively against both limits.
main_pages=reference_start;reference_appendix_pages=pages-reference_start+1
assert main_pages<=18,(main_pages,'main-text pages')
assert reference_appendix_pages<=7,(reference_appendix_pages,'references and appendix pages')
assert r'\author{Anonymous}' in tex
result={'abstract_words':len(words),'pages':pages,'bibliography_entries':len(entries),
        'main_pages_conservative':main_pages,'reference_appendix_pages':reference_appendix_pages,
        'all_entries_cited':True,'undefined_references':False,'overfull_boxes':False,
        'human_scientific_review':'pending','submission_ready':False}
Path('records/manuscript-checks.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
