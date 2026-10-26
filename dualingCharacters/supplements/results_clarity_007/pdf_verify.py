"""Internal PDF destinations and exact displayed evidence, including relocation."""
from pathlib import Path
import json,subprocess,shutil,xml.etree.ElementTree as ET
from supplements.evidence_validation_006.pdf_audit import audit
HERE=Path(__file__).resolve().parent

def main():
 results={};dest=Path('/tmp/clarity007_pdf_relocation');dest.mkdir(exist_ok=True)
 for name in ['READER_EDITION.pdf','FINDINGS_BRIEF.pdf']:
  path=HERE/name;result=audit(path);assert result['absolute_file_urls']==result['uri_links']==0
  if name=='READER_EDITION.pdf':assert 6<=result['pages']<=10 and result['annotations_internal']>0
  else:assert result['pages']<=2
  moved=dest/name;shutil.copyfile(path,moved);assert audit(moved)==result
  bbox=dest/(name+'.xml');subprocess.run(['pdftotext','-bbox',str(moved),str(bbox)],check=True)
  tree=ET.parse(bbox);outside=[]
  for page_no,page in enumerate(tree.findall('.//{http://www.w3.org/1999/xhtml}page'),1):
   width,height=float(page.attrib['width']),float(page.attrib['height'])
   for word in page:
    if word.tag.endswith('word') and (float(word.attrib['xMin'])<0 or float(word.attrib['xMax'])>width or float(word.attrib['yMin'])<0 or float(word.attrib['yMax'])>height):outside.append(page_no)
  assert not outside
  result['relocated_destinations_resolve']=True;result['text_outside_page_bounds']=0;results[name]=result
 text=subprocess.check_output(['pdftotext','-layout',str(HERE/'READER_EDITION.pdf'),'-']).decode();norm=''.join(text.split());expected=[]
 for g in json.loads((HERE/'tables/READER_CONTENT.json').read_text())['groups']:
  c=next(c for c in g['cells'] if c['condition']==g['primary'])
  expected += [c['selected']['text']]+([c['prior']['text']] if c['prior'] else [])+[q['text'] for q in c['extra']]
  expected += [q['text'] for q in c['followups'][:2 if g['id']=='DI5-ceecfe5fb4' else 1]]
  expected += [x['selected']['text'] for x in g['cells'] if x['condition']!=c['condition']]
  for q in c['authorization']:
   if (g['id']=='DI5-e743bcb1a6' and 'source #15' in q['label']) or (g['id']=='DI5-adc5b43b95' and 'source #11' in q['label']) or (g['id']=='DI5-2e4899b66b' and 'source #15' in q['label']):continue
   expected.append(q['text'].split(' The catalog contains')[0])
  z=c['answer_turns'][-1 if g['id']=='DI5-ceecfe5fb4' else 1];expected.append(json.dumps(z['parsed'].get('plan'),ensure_ascii=False))
 missing=[q for q in expected if ''.join(q.split()) not in norm];assert not missing,missing
 results['displayed_quotes_and_plan_fields']=len(expected)
 (HERE/'reports/PDF_VERIFICATION.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
if __name__=='__main__':main()
