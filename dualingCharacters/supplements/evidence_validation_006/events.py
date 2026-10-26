"""Fixed opportunity selection and evidence windows, independent of action outcome."""
import copy,re
from .common import *
from supplements.dialogue_interpretation_005.blinding import reviewer_episode,anonymize,substitutions

MESSAGE_FACTS={'ordinal','turn','sender','recipient','recipient_type','communication_slot','structurally_valid','delivered','visible','observed_at_ordinal','visibility_status','answerer_note_visible','previous_recipient_opportunity','next_recipient_opportunity','second_recipient_opportunity','claim_truncated','generated_characters','delivered_characters'}

def episode_id(e):return 'EV6E-'+rank('episode006|'+e['episode_id'])[:12]
def item_id(e,op):return 'EV6-'+rank('event006|'+e['episode_id']+'|'+str(op))[:12]

def select(es,cases):
 by={(e['case_id'],e['world'],e['condition']):e for e in es}
 rows=[]
 for case in cases:
  triplet=[by.get((case['case_id'],case['anchor_world'],c)) for c in ['C3','C5','A1']]
  actual=[e for e in triplet if e and e['available']]
  assert actual,'No schedule evidence for planned triplet'
  for actor_index in (0,1):
   schedules=[]
   for e in actual:
    schedules.append({t['action']['opportunity']:t['turn'] for t in e['turns'] if t['action'] and t['action']['communication_slot'] and t['action']['neutral_speaker']==f'Speaker {actor_index+1}'})
   assert all(s==schedules[0] for s in schedules),'Mismatched scheduled opportunities'
   possible=schedules[0];assert len(possible)==2
   op=min(possible,key=lambda n:rank(f'event006-v1|{case["case_id"]}|{actor_index}|{n}'))
   for condition,e in zip(['C3','C5','A1'],triplet):
    rows.append({'item_id':item_id(e,op) if e else 'MISSING-'+rank(f'{case["case_id"]}|{condition}|{op}')[:12],
     'case_id':case['case_id'],'condition':condition,'seed':case['seed'],'family_id':case['family_id'],'world':case['anchor_world'],
     'actor_index':actor_index,'opportunity':op,'turn':possible[op],'available':bool(e and e['available']),
     'episode_id':e['episode_id'] if e else None,'review_episode_id':episode_id(e) if e else None,
     'old_window_id':e.get('old_window_id') if e else None,
     'rule_hash':rank(f'event006-v1|{case["case_id"]}|{actor_index}|{op}')})
 return rows

def window(e,op):
 selected=action(e,op);a=selected['action'];message=next((m for m in e['messages'] if m['ordinal']==op),None)
 if message and message['recipient_type']=='component':
  previous=action(e,message['previous_recipient_opportunity']) if message['previous_recipient_opportunity'] else None
  follow=[action(e,message[k]) for k in ('next_recipient_opportunity','second_recipient_opportunity') if message[k]]
 elif message and message['recipient_type']=='answerer':
  previous=e['turns'][selected['turn']-2] if selected['turn']>1 else None
  follow=e['turns'][selected['turn']-1:selected['turn']+1]
 else:previous=None;follow=[]
 end=max([selected['turn']]+[t['turn'] for t in follow])
 authority=[t for t in e['turns'][:end] if t['event_kind']!='filler']
 return {'selected':selected,'message':{k:v for k,v in message.items() if k in MESSAGE_FACTS} if message else None,
         'recipient_previous':previous,'recipient_followups':follow,'authority':authority,
         'status':'no_peer_message' if not message else message['visibility_status'],
         'note':'Last recipient opportunity and first two later opportunities are fixed mechanically, without a semantic relevance filter. Full context allows additional inspection.'}

def safe_episode(e):
 out=reviewer_episode(e);out['item_id']=episode_id(e)
 out['messages']=[{k:v for k,v in m.items() if k in MESSAGE_FACTS} for m in out['messages']]
 # Exclude automatic candidate/semantic fields, roles, mappings, and original review IDs.
 out['identity_note']='Stable speaker aliases substitute identifying names consistently. Other quoted wording is unchanged. Actor count, style and routing may reveal a condition. Analyst truth is separate.'
 return out

def run():
 es=episodes();cases=read(OLD/'SELECTION.json')['cases'];rows=select(es,cases)
 assert len(rows)==72 and len({r['item_id'] for r in rows})==72
 target=HERE/'EVENT_SELECTION.json'
 value={'selection_rule':'event006-v1; lowest SHA256 within each scheduled actor, common reserved opportunities; no action outcome used',
        'source_selection_sha256':sha(OLD/'SELECTION.json'),'items':rows}
 if target.exists():assert read(target)==value,'Existing event identity must be preserved'
 else:write(target,value)
 safe=[];index={e['episode_id']:e for e in es}
 for r in rows:
  if not r['available']:
   safe.append({'item_id':r['item_id'],'available':False,'status':'missing_cell'});continue
  e=index[r['episode_id']];w=anonymize(window(e,r['opportunity']),substitutions(e))
  safe.append({'item_id':r['item_id'],'review_episode_id':r['review_episode_id'],'available':True,'opportunity':r['opportunity'],'window':w})
 safe.sort(key=lambda r:rank('event006-review-order|'+r['item_id']))
 out=WORK/'reviewer_build';out.mkdir(parents=True,exist_ok=True)
 write(out/'items.json',safe)
 write(out/'episodes.json',sorted([safe_episode(e) for e in es if e['anchor']],key=lambda e:rank('event006-episode-order|'+e['item_id'])))
 csv_write(HERE/'tables/EVENT_MECHANICAL_STATUS.csv',[{**{k:r[k] for k in ('item_id','condition','seed','case_id','opportunity')},
  'kind':window(index[r['episode_id']],r['opportunity'])['selected']['action']['kind'],
  'route':(window(index[r['episode_id']],r['opportunity'])['message'] or {}).get('recipient_type','no_peer_message'),
  'status':window(index[r['episode_id']],r['opportunity'])['status']} for r in rows])
 print('Fixed 72 opportunities; 36 linked full episodes. No semantic judgments or human ratings generated.')
if __name__=='__main__':run()
