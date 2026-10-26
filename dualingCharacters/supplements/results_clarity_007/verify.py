"""Changed-product checks over committed selected evidence, without original artifact paths."""
import gzip,io,re
from collections import Counter
from .common import *
from .ratings_v2 import validate_rows,FIELDS,provenance_expected
from .review_package import response
from supplements.dialogue_interpretation_005.extraction import get_value,validate_pair
from supplements.evidence_validation_006.events import select
from supplements.evidence_validation_006.review_package import scan

def run():
 required=[PREVIOUS/'evidence/author_selected_v1.tar.gz',PREVIOUS/'evidence/reviewer_events_v1.tar.gz',HERE/'tables/READER_CONTENT.json',HERE/'tables/READER_QUOTATIONS.json']
 missing=[str(p.relative_to(ROOT)) for p in required if not p.exists()]
 if missing:
  result={'status':'missing prerequisite','missing':missing,'instruction':'Restore committed006 evidence archives and run007 build; do not fabricate substitute data.'};write(HERE/'reports/VERIFICATION.json',result);print(result);return
 recs={}
 for line in gzip.decompress(members()['selected_records.jsonl.gz']).decode().splitlines():
  r=json.loads(line);key=r['file'],r['record'];assert key not in recs;recs[key]=r
 def check(q):
  l=q['locator'];r=recs[l['file'],l['record']];assert r['file_sha256']==l['sha256'];assert get_value(r['value'],l)==q['text']
 old=source_json('QUOTATIONS.json');new=read(HERE/'tables/READER_QUOTATIONS.json')
 for q in old+new:check(q)
 es=episodes();validate_pair(es);assert len(es)==48
 assert select(es,read(DIALOGUE/'SELECTION.json')['cases'])==event_selection()
 items=source_json('items.json','reviewer');scan(items);scan(source_json('episodes.json','reviewer'))
 routes=Counter(i['window']['message']['recipient_type'] for i in items);assert routes=={'component':64,'answerer':8}
 for item in items:
  w=item['window'];route=w['message']['recipient_type']
  for follow in w['recipient_followups']:
   html=response(follow,route,'following')
   from html import unescape
   expected=follow['defender']['raw'] if route=='answerer' else follow['action']['claim']
   assert expected in unescape(html)
 ids=[r['item_id'] for r in event_selection()]
 for n in [1,2]:
  rows=validate_rows(csv_read(HERE/f'review/rater_{n}_event006_v2.csv'),ids)
  assert all(not v for r in rows for k,v in r.items() if k!='item_id')
  for k,v in provenance_expected().items():assert read(HERE/f'review/rater_{n}_provenance_TEMPLATE.json')[k]==v
 worksheet=csv_read(HERE/'AUTHOR_EVENT_ANALYSIS.csv');assert {r['item_id'] for r in worksheet}==set(ids) and len(worksheet)==72
 for r in worksheet:
  q={'text':r['incoming_exact_claim'],'locator':json.loads(r['incoming_locator'])};check(q)
  for span in json.loads(r['incoming_exact_spans']):assert q['text'][span['start']:span['end']]==span['text']
 for g in read(HERE/'tables/READER_CONTENT.json')['groups']:
  assert {c['condition'] for c in g['cells']}=={'C3','C5','A1'}
  for c in g['cells']:
   e=next(e for e in es if e['episode_id']==c['episode_id']);assert c['alias_map']==[{'neutral':a['neutral'],'alias':a['alias']} for a in e['actors']]
   for z in c['answer_turns']:
    check({'locator':z['locator'],'text':e['turns'][z['turn']-1]['defender']['raw']});assert z['parsed']==e['turns'][z['turn']-1]['defender']['parsed']
 for path,value in read(HERE/'EVIDENCE_CUTOFF.json')['source_hashes'].items():assert sha(ROOT/path)==value,path
 result={'status':'passed','original_quotes':len(old),'new_reader_quotation_checks':len(new),'selected_records':len(recs),'episodes':len(es),'fixed_events':len(items),'routes':dict(routes),'author_worksheet_rows':len(worksheet),'human_ratings':0,'blank_forms':2,'prior006_bound_hashes_unchanged':True,'scientific_validation':'not established by software checks; independent human ratings and controlled inference remain pending'}
 write(HERE/'reports/VERIFICATION.json',result);print(result)
if __name__=='__main__':run()
