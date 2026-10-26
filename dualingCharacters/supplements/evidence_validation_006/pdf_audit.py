"""Check portable PDF destinations, render every page, and make visual-review sheets."""
import argparse,json,subprocess,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from PyPDF2 import PdfFileReader
HERE=Path(__file__).resolve().parent

def audit(path):
 with path.open('rb') as f:
  pdf=PdfFileReader(f);page_ids={p.indirectRef.idnum for p in pdf.pages};links=[];uris=[]
  for number,page in enumerate(pdf.pages,1):
   for ref in page.get('/Annots',[]):
    a=ref.getObject();action=a.get('/A',{});destination=a.get('/Dest')
    if action.get('/URI'):uris.append(str(action['/URI']))
    if destination:
     assert destination[0].idnum in page_ids,'Unresolved internal page destination'
     links.append({'page':number,'target_page_object':destination[0].idnum})
  return {'pages':pdf.getNumPages(),'annotations_internal':len(links),'uri_links':len(uris),'absolute_file_urls':sum(u.startswith('file:') for u in uris),'destinations_resolve':True,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

def main():
 p=argparse.ArgumentParser();p.add_argument('--render',action='store_true');p.add_argument('--pdf',type=Path,default=HERE/'CASEBOOK_V2.pdf');args=p.parse_args()
 result=audit(args.pdf);assert result['uri_links']==0 and result['annotations_internal']>0
 old=HERE.parent/'dialogue_interpretation_005/CASEBOOK.pdf'
 result['historical_005']=audit(old) if old.exists() else {'status':'not present in this relocation'}
 temp=HERE/'reports/screenshots'/('pdf-'+result['sha256'][:8]);temp.mkdir(parents=True,exist_ok=True)
 bbox=temp/'casebook-bbox.html';subprocess.run(['pdftotext','-bbox',str(args.pdf),str(bbox)],check=True)
 tree=ET.parse(bbox);bad=[]
 for page_no,page in enumerate(tree.findall('.//{http://www.w3.org/1999/xhtml}page'),1):
  width,height=float(page.attrib['width']),float(page.attrib['height'])
  for w in page:
   if w.tag.endswith('word') and (float(w.attrib['xMin'])<0 or float(w.attrib['xMax'])>width or float(w.attrib['yMin'])<0 or float(w.attrib['yMax'])>height):bad.append(page_no)
 assert not bad,'Text outside page bounds';result['text_outside_page_bounds']=0
 text=subprocess.check_output(['pdftotext','-layout',str(args.pdf),'-']).decode();normalized=''.join(text.split());expected=[]
 for c in json.loads((HERE/'tables/EXCHANGE_CONTEXTS.json').read_text()):
  for x in c['cells']:
   if x['cited_source']:expected.append(x['cited_source']['text'])
   for card in x['timeline']:
    expected.append(card['user']['text']);z=card['position']
    if z and z['action']:expected.append(z['action']['claim'])
    if card['answer'] and z:expected.append(z['answer']['raw'])
 missing=[q for q in expected if ''.join(q.split()) not in normalized]
 assert not missing,'PDF quote/structured-output identity failure: '+repr(missing[:1])
 result['pdf_quoted_spans_verified_after_whitespace_normalization']=len(expected)
 if args.render:
  subprocess.run(['pdftoppm','-scale-to','1150','-png',str(args.pdf),str(temp/'page')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
  from PIL import Image,ImageOps,ImageDraw
  pages=sorted(temp.glob('page-*.png'));assert len(pages)==result['pages']
  sheets=[]
  for start in range(0,len(pages),4):
   group=pages[start:start+4];sheet=Image.new('RGB',(1800,2400),'#d9e1e2');draw=ImageDraw.Draw(sheet)
   for i,page in enumerate(group):
    im=Image.open(page);im.thumbnail((860,1135));x=(i%2)*900+20;y=(i//2)*1200+35
    sheet.paste(im,(x,y));draw.text((x,y-22),page.name,fill='black')
   dest=temp/f'contact-{start//4+1:02d}.png';sheet.save(dest);sheets.append(str(dest.relative_to(HERE)))
  result.update(rendered_pages=len(pages),visual_review_sheets=sheets)
 (HERE/'reports/PDF_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
