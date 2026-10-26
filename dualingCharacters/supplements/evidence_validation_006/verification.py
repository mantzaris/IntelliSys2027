"""Reader verification and protected-history checks, with explicit prerequisites."""
import argparse,re
from html.parser import HTMLParser
from .common import *

def previous_science():
 from supplements.dialogue_interpretation_005.freeze import verify as dialogue
 from supplements.behavior_characterization_004.common import verify_science
 a=verify_science();b=dialogue()
 amendments=[]
 for m in (ROOT/'supplements/behavior_characterization_004').glob('AMENDMENT_*_MANIFEST.json'):
  doc=read(m)
  for name,value in doc['files'].items():
   p=m.parent/name
   if not p.exists():p=ROOT/name
   assert sha(p)==value
  amendments.append(m.name)
 return {'previous_scientific_verification':'passed','behavior':a,'dialogue':b,'behavior_amendments':amendments}

def protected():
 available=0;missing=[]
 for path,value in read(HERE/'PRIOR_PROTECTION.json')['protected_files'].items():
  p=ROOT/path
  if not p.exists():missing.append(path);continue
  assert sha(p)==value,'Protected historical file changed: '+path;available+=1
 changes=read(HERE/'PRESENTATION_CHANGES.json')
 for c in changes['changes']:assert sha(ROOT/c['path'])==c['new_sha256']
 return {'verified_present':available,'missing_original_packet_files':missing,
  'status':'passed' if not missing else 'available files passed; original omitted packet checks require originating mirror'}

class Links(HTMLParser):
 def __init__(self):super().__init__();self.ids=[];self.links=[];self.resources=[]
 def handle_starttag(self,tag,attrs):
  d=dict(attrs)
  if 'id' in d:self.ids.append(d['id'])
  if tag=='a' and 'href' in d:self.links.append(d['href'])
  if tag in ['img','script','iframe','link']:
   for k in ['src','href']:
    if k in d:self.resources.append(d[k])

def html_links(path):
 parser=Links();parser.feed(path.read_text());assert len(parser.ids)==len(set(parser.ids)),'Duplicate HTML IDs'
 assert not parser.resources,'No external or network resources allowed'
 missing=[];cache={path:parser}
 for link in parser.links:
  if not link or link=='#':continue
  assert not re.match(r'^[a-z]+:',link),'Unexpected URL scheme: '+link
  file,_,fragment=link.partition('#');target=path.parent/file if file else path
  if not target.exists():missing.append(link);continue
  if fragment:
   if target not in cache:
    other=Links();other.feed(target.read_text());cache[target]=other
   if fragment not in cache[target].ids:missing.append(link)
 assert not missing,'Broken local HTML links: '+repr(missing[:3])
 return {'file':str(path.relative_to(HERE)),'ids':len(parser.ids),'links':len(parser.links),'all_internal_and_relative_targets_exist':True}

def verify_new_freezes():
 for name in ['SCIENTIFIC_MANIFEST.json','EVENT_REVIEW_FREEZE.json','compatibility/FREEZE.json']:
  d=read(HERE/name)
  for p,value in d['files'].items():assert sha(ROOT/p)==value,'New frozen file changed: '+p

def main():
 result={'prior_science':previous_science(),'protected_history':protected()}
 verify_new_freezes();result['new_freezes']='passed'
 from .reader import verify
 verify()
 targets=[HERE/'DIALOGUE_EXCHANGES.html',WORK/'author/DIALOGUE_ATLAS.html',WORK/'reviewer/REVIEW.html',WORK/'reviewer/EPISODES.html']
 result['html']=[html_links(p) for p in targets if p.exists()];result['missing_html_prerequisites']=[str(p.relative_to(HERE)) for p in targets if not p.exists()]
 write(HERE/'reports/VERIFICATION.json',result);print({k:v for k,v in result.items() if k not in ['prior_science','protected_history']})
if __name__=='__main__':main()
