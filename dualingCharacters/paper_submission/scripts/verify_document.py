"""Check the compiled anonymous document using installed Poppler and qpdf."""
from pathlib import Path
import json,re,subprocess
P=Path(__file__).resolve().parents[1]
def walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values():yield from walk(v)
    elif isinstance(x,list):
        for v in x:yield from walk(v)
def command(*args):return subprocess.check_output(args,text=True)
def main():
    pdf=str(P/'manuscript.pdf');text=command('pdftotext',pdf,'-');info=command('pdfinfo',pdf)
    structure=json.loads(command('qpdf','--json',pdf));dicts=list(walk(structure))
    uris=[d['/URI'] for d in dicts if '/URI'in d]
    assert uris and all(u.startswith(('https://','http://')) for u in uris)
    names={n for d in dicts if '/Names'in d and isinstance(d['/Names'],list) for n in d['/Names'][::2]}
    gotos=[d['/D'] for d in dicts if d.get('/S')=='/GoTo' and isinstance(d.get('/D'),str)]
    assert all(d in names for d in gotos), 'Broken named PDF destination'
    assert not any(d.get('/S') in ['/GoToR','/Launch','/JavaScript'] for d in dicts)
    for d in dicts:
        if '/Author' in d:assert not d['/Author']
    for token in ['/home/','file://','mantzaris','resort','IntelliSys2027/dualingCharacters']:
        assert token not in text and token not in json.dumps(structure)
    assert not re.search(r'\?\?',text)
    total=int(re.search(r'Pages:\s*(\d+)',info).group(1));assert total==16
    aux=(P/'.build/manuscript.aux').read_text();main_pages=int(re.search(r'\\newlabel\{maintextend\}\{\{6\}\{(\d+)\}',aux).group(1));assert main_pages==14
    log=(P/'.build/manuscript.log').read_text()
    assert 'Overfull' not in log
    assert 'undefined references' not in log and 'undefined on input line' not in log
    result={'main_text_pages':main_pages,'reference_pages':total-main_pages,'total_pages':total,
      'external_reference_links':len(uris),'named_internal_links_checked':len(gotos),
      'anonymous_metadata':True,'machine_paths_absent':True,'overfull_boxes':0,'unresolved_references':0,
      'limitation':'Automated document checks complement, not replace, page-by-page visual inspection.'}
    (P/'.build/document_verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
