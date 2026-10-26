"""Build a separately distributable blinded event package; never copy author readings."""
import re
from .common import *
from .package_inputs import archive
from .ratings import blank_forms

def scan(value,path='root'):
 forbidden={'condition','seed','role','sender_role','case_id','family_id','run_id','old_window_id','biography','interpretation','labels','strongest_supported','not_established','next_response','previous_response','semantic_response_status'}
 if isinstance(value,dict):
  assert not set(value)&forbidden, f'Reviewer metadata leak at {path}: {set(value)&forbidden}'
  for k,v in value.items():scan(v,path+'.'+k)
 elif isinstance(value,list):
  for i,v in enumerate(value):scan(v,path+f'[{i}]')
 elif isinstance(value,str):
  assert not re.search(r'\b(?:C3|C5|A1|Hyde|Rival|Jekyll|Traditionalist|Provocateur|DI5-[a-z0-9]+|D5E-[a-z0-9]+|main-qwen-[a-z0-9-]+)\b',value),f'Reviewer identity leak at {path}'
  assert '/home/' not in value and 'artifacts/runs/' not in value,f'Reviewer path leak at {path}'

def run():
 out=WORK/'reviewer_build'
 for name in ['RUBRIC.md','CALIBRATION.md']:(out/name).write_bytes((HERE/'review'/name).read_bytes())
 blank_forms();items=read(out/'items.json');eps=read(out/'episodes.json')
 scan(items);scan(eps)
 # Core reading word units approximate what is displayed, not duplicated collapsed JSON.
 effort=[]
 for r in items:
  if not r['available']:continue
  w=r['window'];texts=[t['user']['text'] for t in w['authority']]
  turns=[w['selected']]+([w['recipient_previous']] if w['recipient_previous'] else [])+w['recipient_followups']
  for t in turns:
   if t['action']:texts.append(t['action']['claim'])
   texts.append(json.dumps(t['defender']['parsed'],ensure_ascii=False))
  words=len(re.findall(r'\w+',' '.join(texts)));effort.append({'item_id':r['item_id'],'core_word_units':words,
    'minutes_at_200_words_plus3':words/200+3,'minutes_at_150_words_plus5':words/150+5})
 csv_write(HERE/'tables/REVIEW_WORKLOAD.csv',effort)
 report={'planned_items':len(items),'available_items':sum(r['available'] for r in items),'full_episode_contexts':len(eps),
   'word_units_sum':sum(r['core_word_units'] for r in effort),'word_units_range':[min(r['core_word_units'] for r in effort),max(r['core_word_units'] for r in effort)],
   'hours_per_rater_planning_range':[sum(r['minutes_at_200_words_plus3'] for r in effort)/60,sum(r['minutes_at_150_words_plus5'] for r in effort)/60],
   'assumptions':'200 words/min+3min annotation to150 words/min+5min per item; excludes breaks/calibration and deep full-episode checks. Not measured reviewer timing.',
   'human_ratings_received':0,'old_full_episode_packet_required':False}
 write(HERE/'reports/REVIEW_READINESS.json',report)
 (out/'START_HERE.md').write_text('# Independent fixed-event review\n\nOpen REVIEW.html offline, read RUBRIC.md and the disjoint CALIBRATION.md, and complete only your assigned rater CSV. Keep all72 rows. EPISODES.html supplies optional full context. Full-episode forms from earlier packets are not additionally required. Do not exchange labels before independent completion. Preserve your completed form and provenance; adjudication is separate. No AI judgments or condition key is included.\n')
 (out/'SELECTION_IDS.json').write_text(json.dumps({'items':[r['item_id'] for r in items],'rule':'Fixed scheduled opportunities; no outcome selection','selection_sha256':sha(HERE/'EVENT_SELECTION.json')},indent=2)+'\n')
 entries={str(p.relative_to(out)):p.read_bytes() for p in sorted(out.iterdir()) if p.is_file() and p.name!='PROTOCOL.md'}
 for name,data in entries.items():
  if name.endswith(('.json','.html','.md','.csv')):scan(data.decode())
 manifest=archive(HERE/'evidence/reviewer_events_v1.tar.gz',entries)
 manifest.update(item_count=72,episode_contexts=36,author_mapping_excluded=True,ai_interpretations_excluded=True,forms_blank=True)
 write(HERE/'evidence/REVIEWER_MANIFEST.json',manifest)
 print(report);print('Separate reviewer archive bytes:',manifest['bytes'])
if __name__=='__main__':run()
