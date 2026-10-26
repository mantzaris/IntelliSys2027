"""Outcome-independent matched selection, exact local records and public judge inputs."""
from collections import defaultdict
import copy,re
from .common import *
from supplements.dialogue_interpretation_005.extraction import locator,source_text_loc,validate_pair
from supplements.behavior_characterization_004.records import action_features,memory_before
from supplements.behavior_characterization_004.peers import reconstruct
from supplements.evidence_validation_006.events import window
from supplements.dialogue_interpretation_005.blinding import anonymize,substitutions
from pcc.environment import make_family
from pcc.characters import cast

def selection():
 old=read(ROOT/'supplements/dialogue_interpretation_005/EVIDENCE_CUTOFF.json')['bound_dialogue_runs']
 families=set.intersection(*(set(b['family_ids']) for b in old.values()))
 chosen=sorted(families,key=lambda f:rank('auto008-family-v1:'+f))[:30]
 result=[]
 for f in chosen:
  for world in ['authorized','hypothetical']:
   for seed in [17,29,43]:
    for stratum,ops in [('direct',[2,3,5,6,8,9,11,12]),('communication',[1,4,7,10])]:
     op=min(ops,key=lambda n:rank(f'auto008-op-v1:{f}:{world}:{seed}:{stratum}:{n}'))
     for c in ['C3','C5','A1']:
      result.append({'item_id':'AE8-'+rank(f'{f}|{world}|{seed}|{c}|{stratum}|{op}')[:14],'family_id':f,'world':world,'seed':seed,'condition':c,'stratum':stratum,'opportunity':op,'run_id':f'main-qwen-{c.lower()}-{seed}-r0-collect'})
 assert len(result)==1080
 write(HERE/'inputs/BROAD_SELECTION.json',{'rule':'auto008-family-v1 / auto008-op-v1; hash ranking without outcomes','family_order':chosen,'items':result,'runs':old})
 return result,old

def extract_episodes(rows,bindings):
 cache=ART/'broad_episodes.json.gz';stamp=ART/'broad_cache.json';selection_hash=sha(HERE/'inputs/BROAD_SELECTION.json')
 if cache.exists() and stamp.exists():
  m=read(stamp)
  if m['selection_sha256']==selection_hash and sha(cache)==m['sha256']:return json.loads(gzip.decompress(cache.read_bytes()))
 result=[]
 for run_id,b in bindings.items():
  needed={(r['family_id'],r['world']) for r in rows if r['run_id']==run_id};turns=defaultdict(list);actions=defaultdict(list);files={}
  for path,h in b['raw_files'].items():
   if '_summary' in path or '_interventions' in path:continue
   assert sha(ROOT/path)==h,path
   kind='action' if '_characters' in path else 'turn';files[kind]=(path,h)
   for line,row in stream(ROOT/path):
    if (row['family_id'],row['world']) in needed:(actions if kind=='action' else turns)[row['family_id'],row['world']].append((line,row))
  condition=next(r['condition'] for r in rows if r['run_id']==run_id);seed=next(r['seed'] for r in rows if r['run_id']==run_id)
  for (family,world),chronological in sorted(turns.items()):
   assert [r['turn'] for _,r in chronological]==list(range(1,17))
   scenario=next(s for s in make_family('train',int(family.split('-')[-1]),16) if s.world==world)
   actors=cast(condition,family,seed);aliases=[a.alias for a in actors]
   e={'episode_id':'AE8E-'+rank(f'{run_id}|{family}|{world}')[:14],'case_id':f'{family}|{seed}','condition':condition,'seed':seed,'family_id':family,'world':world,'run_id':run_id,'available':True,'actors':[{'alias':a.alias,'neutral':f'Speaker {i+1}','role':a.role,'slot':a.slot,'owned_option':a.owned_option} for i,a in enumerate(actors)],'turns':[],'features':[],'source_bank':{},'model_revision':b['model_revision']}
   byturn={a['turn']:(line,a) for line,a in actions[family,world]};assert sorted(byturn)==b['schedule'];previous=None
   for line,row in chronological:
    turn=row['turn'];body=json.loads(row['prompt'][1]['content']);path,h=files['turn'];assert row['target']==scenario.truth_at(turn).target(scenario.spec)
    user=next(m for m in body['sources'] if m['index']==body['latest_user_index']);assert user['text']==scenario.messages[turn-1].text
    e['catalog']=body['catalog'];t={'turn':turn,'event_kind':scenario.events[turn-1].kind,'user':dict(user,locator=source_text_loc(path,h,line,body,user['index'])),'defender':{'parsed':row['generation']['parsed'],'raw':row['generation']['raw'],'locator':locator(path,h,line,['generation','raw']),'metrics':row['metrics']},'defender_observation':body,'analyst_only_target':row['target'],'action':None}
    if turn in byturn:
     aline,a=byturn[turn];ap,ah=files['action'];obs=json.loads(a['prompt'][1]['content']);feature=action_features(a,row,previous,scenario,aliases,len(e['features'])+1,aliases.index(a['actor']));e['features'].append(feature)
     t['action']={k:a.get(k) for k in ['actor','kind','slot','value','source','target','claim','applied','rejected_reason','communication_slot']}
     t['action'].update(opportunity=feature['ordinal'],neutral_speaker=f'Speaker {aliases.index(a["actor"])+1}',observation=obs,memory_before=obs['memory'],memory_before_answer=body['memory'],claim_locator=locator(ap,ah,aline,['claim']),locator=locator(ap,ah,aline,[]),generated_claim=(a['generation'].get('parsed') or {}).get('claim',''),truncated=feature['claim_truncated'])
    e['turns'].append(t);previous=row
   e['messages'],checks=reconstruct({'actions':e['features']},6);assert all(c['queue_matches'] for c in checks)
   result.append(e)
  print('Extracted',run_id,len(needed),'matched episodes',flush=True)
 validate_pair(result);assert len(result)==540
 ART.mkdir(exist_ok=True,parents=True);cache.write_bytes(gzip.compress(json.dumps(result,separators=(',',':')).encode(),mtime=0));write(stamp,{'selection_sha256':selection_hash,'sha256':sha(cache),'episodes':len(result)})
 return result

def event_input(e,row,population):
 op=row['opportunity'];w=window(e,op);selected=w['selected'];a=selected['action'];message=w['message'];route=message['recipient_type'] if message else 'answerer' if a['kind'] in ['edit','recollect','propose'] else 'none'
 previous=w['recipient_previous'];follow=w['recipient_followups']
 if not message and route=='answerer':previous=e['turns'][selected['turn']-2] if selected['turn']>1 else None;follow=e['turns'][selected['turn']-1:selected['turn']+1]
 def text(t):return '' if not t else t['defender']['raw'] if route=='answerer' else t['action']['claim']
 recipient_obs=(follow[0]['defender_observation'] if route=='answerer' else follow[0]['action']['observation']) if follow and route!='none' else None
 blocks={'selected':a['claim'] or '', 'recipient_previous':text(previous),'first_followup':text(follow[0]) if follow else '', 'second_followup':text(follow[1]) if len(follow)>1 else ''}
 end=follow[-1]['turn'] if follow else selected['turn'];authority=[]
 for t in e['turns'][:end]:
  if t['event_kind']!='filler':
   ref='user_'+str(t['user']['index']);blocks[ref]=t['user']['text'];authority.append({'ref':ref,'turn':t['turn'],'source_id':t['user']['index']})
 visible=[]
 if recipient_obs:
  for s in recipient_obs['sources']:
   ref='visible_'+str(s['index']);blocks[ref]=s['text'];visible.append({'ref':ref,'source_id':s['index'],'author':s['author']})
  blocks['recipient_observed_notes']=json.dumps(recipient_obs['memory'].get('notes',[]),ensure_ascii=False)
  blocks['recipient_observed_inbox']=json.dumps(recipient_obs.get('inbox',[]),ensure_ascii=False)
 # Separate delivered source field from an audit-only source integer omitted by note transport.
 delivered_source=a['source'] if route=='component' and message and message['delivered'] else None
 mapping=substitutions(e);catalog=dict(zip(e['catalog']['fields'],e['catalog']['options']))
 public={'catalog':catalog,'field_descriptions':e['catalog']['field_descriptions'],'blocks':blocks,'selected_speaker':a['neutral_speaker'],'recipient':mapping.get(message['recipient'],message['recipient']) if message else 'Answerer' if route=='answerer' else None,'route':route,'selected_turn':selected['turn'],'recipient_previous_turn':previous['turn'] if previous else None,'first_followup_turn':follow[0]['turn'] if follow else None,'second_followup_turn':follow[1]['turn'] if len(follow)>1 else None,'authority_transcript_analyst_context':authority,'recipient_visible_sources':visible,'selected_visible_to_recipient':message['visible'] if message else (a['applied'] if route=='answerer' else False),'delivered':message['delivered'] if message else a['applied'],'delivered_numeric_source_field':delivered_source,'first_followup_recorded':bool(follow),'delivered_text_truncated':a['truncated'],'chronology_note':'User sources are original attributed statements. Authority transcript may include evidence absent from recipient observation; never infer recipient knowledge from analyst-only availability. Followups are chronological opportunities, not selected for relevance.'}
 public=anonymize(public,mapping)
 truth=dict(zip(e['catalog']['fields'],selected['analyst_only_target']['state']))
 mechanics={'typed_kind':a['kind'],'typed_slot':a['slot'],'typed_value':a['value'],'audit_source':a['source'],'audit_source_visible_sender':a['source'] in {s['index'] for s in a['observation']['sources']},'audit_source_visible_recipient':a['source'] in {s['index'] for s in recipient_obs['sources']} if recipient_obs else None,'applied':a['applied'],'rejected_reason':a['rejected_reason'],'memory_before':a['memory_before'],'memory_after_action':a['memory_before_answer'],'following_answer':selected['defender']['parsed'],'following_metrics':selected['defender']['metrics'],'route':route,'delivered':public['delivered'],'visible':public['selected_visible_to_recipient'],'claim_exact_repeat':previous['action']['claim']==follow[0]['action']['claim'] if previous and follow and route=='component' else None,'typed_repeat':(previous['action']['slot'],previous['action']['value'])==(follow[0]['action']['slot'],follow[0]['action']['value']) if previous and follow and route=='component' else None,'user_events_between':[{k:t[k] for k in ['turn','event_kind','user']} for t in e['turns'] if follow and selected['turn']<t['turn']<=follow[0]['turn'] and t['event_kind']!='filler']}
 return {'item_id':row['item_id'],'population':population,'public':public,'metadata':{'api_kind':a['kind'],'typed_slot':a['slot'],'typed_value':a['value']},'private':{'authorized':truth,'identity':row,'mechanical':mechanics,'source_locator':a['claim_locator'],'full_generated_claim':a['generated_claim'],'neutral_alias_mapping':mapping}}

def run():
 from supplements.results_clarity_007.common import episodes,event_selection
 fixed_es={e['episode_id']:e for e in episodes()};fixed=[event_input(fixed_es[r['episode_id']],r,'fixed72') for r in event_selection()];write(HERE/'inputs/fixed72.json',fixed)
 rows,bindings=selection();es=extract_episodes(rows,bindings);by={(e['run_id'],e['family_id'],e['world']):e for e in es}
 broad=[event_input(by[r['run_id'],r['family_id'],r['world']],r,'broad') for r in rows];write(HERE/'inputs/broad30.json',broad)
 selected=read(HERE/'inputs/BROAD_SELECTION.json');families15=set(selected['family_order'][:15]);write(HERE/'inputs/broad15.json',[r for r in broad if r['private']['identity']['family_id'] in families15])
 write(HERE/'reports/SAMPLING.json',{'fixed':72,'broad30':len(broad),'broad15':540,'unique_broad_families':30,'fixed_unique_families':len({r['private']['identity']['family_id'] for r in fixed}),'overlap_families':sorted(set(selected['family_order'])&{r['private']['identity']['family_id'] for r in fixed}),'direct_schedule_weight':8/12,'communication_schedule_weight':4/12,'paired_scripts_verified':True,'no_outcome_selection':True,'input_hashes':{n:sha(HERE/'inputs'/n) for n in ['fixed72.json','broad30.json','broad15.json','BROAD_SELECTION.json']}})
 print('Built fixed72 and matched1080-event master; no judge labels read')
if __name__=='__main__':run()
