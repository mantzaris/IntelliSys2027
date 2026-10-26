"""Portable PDF/link checks; optional PyPDF2 is used only for this inspection."""
import json,re,subprocess
from pathlib import Path
try:
 from pypdf import PdfReader
except ImportError:
 try:from PyPDF2 import PdfFileReader as PdfReader
 except ImportError:raise SystemExit('Missing optional inspection prerequisite: pypdf or PyPDF2; no scientific result was recalculated.')
HERE=Path(__file__).resolve().parent

def main():
 results=[]
 for name in ['manuscript','author_review']:
  path=HERE/'paper'/f'{name}.pdf';reader=PdfReader(str(path));uris=[];links=0
  for page in reader.pages:
   for ref in page.get('/Annots',[]):
    a=(ref.get_object() if hasattr(ref,'get_object') else ref.getObject());action=a.get('/A',{})
    if action.get('/URI'):uris.append(str(action['/URI']))
    if a.get('/Subtype')=='/Link':links+=1
    assert action.get('/S') not in ['/Launch','/GoToR'],'External local document dependency'
  assert all(not u.startswith(('file:','/home/','/workspace/')) for u in uris)
  text=subprocess.check_output(['pdftotext',str(path),'-'],text=True)
  assert '\ufffd' not in text,'Replacement character in extracted text'
  if name=='manuscript':
   for identifying in ['mantzaris','IntelliSys2027/','93dcc90','/home/resort','github.com/mantzaris']:
    assert identifying.casefold() not in text.casefold(),identifying
   assert not (reader.metadata if hasattr(reader,'metadata') else reader.getDocumentInfo()).get('/Author'),'Anonymous PDF author metadata is nonempty'
  aux=(HERE/'paper'/f'{name}.aux').read_text();match=re.search(r'\\newlabel\{maintextend\}\{\{[^}]*\}\{(\d+)\}',aux)
  main_pages=int(match.group(1)) if match else None
  assert main_pages is not None and main_pages<=18,(name,main_pages)
  results.append({'document':str(path.relative_to(HERE)),'pages':len(reader.pages),'main_text_last_page':main_pages,'annotation_links':links,'uri_links':len(uris),'absolute_file_links':0,'anonymous_identifying_scan':name=='manuscript','visual_inspection':'reported separately after rendering every page'})
 out=HERE/'reports/PDF_CHECKS.json';out.write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
if __name__=='__main__':main()
