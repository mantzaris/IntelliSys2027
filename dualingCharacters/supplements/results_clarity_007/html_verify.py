"""Offline link verification, parsing each destination once instead of per link."""
import argparse,re
from .common import *
from supplements.evidence_validation_006.verification import Links

def run(base):
 base=Path(base).resolve();cache={};results=[]
 def parsed(path):
  path=path.resolve()
  if path not in cache:
   p=Links();p.feed(path.read_text());assert len(p.ids)==len(set(p.ids));cache[path]={'ids':set(p.ids),'links':p.links,'resources':p.resources}
  return cache[path]
 for path in [base/'READER_EDITION.html',base/'extracted/reviewer_v2_final/REVIEW.html',base/'extracted/reviewer_v2_final/EPISODES.html']:
  p=parsed(path);assert not p['resources'],'HTML must have no external dependencies'
  missing=[]
  for link in p['links']:
   if not link or link=='#':continue
   assert not re.match(r'^[a-z]+:',link),'Absolute/network URI: '+link
   name,_,fragment=link.partition('#');target=(path.parent/name if name else path).resolve()
   if not target.exists():missing.append(link);continue
   if fragment and fragment not in parsed(target)['ids']:missing.append(link)
  assert not missing,missing[:3]
  results.append({'file':str(path.relative_to(base)),'links':len(p['links']),'all_relative_targets_exist':True,'network_resources':0})
 result={'status':'passed','relocated_root':str(base),'pages':results,'unique_html_documents_parsed':len(cache)}
 write(HERE/'reports/HTML_LINKS.json',result);print(result)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',default=str(HERE));args=p.parse_args();run(args.root)
