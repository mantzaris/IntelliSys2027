"""Unchanged compatibility experiment: deterministic outcomes and declared semantic sample."""
from collections import defaultdict,Counter
import copy,csv
import numpy as np
from .common import *
from .analysis import interval_family
from .sampling import event_input
from supplements.evidence_validation_006.compatibility_design import load_scenarios,actors
from supplements.behavior_characterization_004.records import action_features
from supplements.behavior_characterization_004.peers import reconstruct
from supplements.dialogue_interpretation_005.extraction import locator,source_text_loc

def selection():
 d=read(ROOT/'supplements/evidence_validation_006/compatibility/DESIGN.json');result=[]
 for n in range(16):
  family=f'dialogue005-compat-{n:04d}';world=min(['authorized','hypothetical'],key=lambda w:rank(f'auto008-compat-world:{family}:{w}'))
  op=min([1,4,7,10],key=lambda o:rank(f'auto008-compat-op:{family}:{o}'))
  for arm in d['arms']:result.append({'item_id':'AC8-'+rank(f'{family}:{world}:{arm}:{op}')[:14],'family_id':family,'world':world,'seed':17,'condition':arm,'stratum':'communication','opportunity':op,'run_id':d['run_id']})
 write(HERE/'inputs/COMPATIBILITY_SEMANTIC_SELECTION.json',result);return result

def extract():
 d=read(ROOT/'supplements/evidence_validation_006/compatibility/DESIGN.json');run=ROOT/'artifacts/runs'/d['run_id'];assert read(run/'completion.json')['fixed_grid_complete']
 scenarios={(s.family_id,s.world):s for s in load_scenarios(d)};selected=read(HERE/'inputs/COMPATIBILITY_SEMANTIC_SELECTION.json');inputs=[];summaries=[];familyrows=[];sources={}
 for arm in d['arms']:
  ap=run/(arm+'_characters.jsonl');tp=run/(arm+'.jsonl');ah=sha(ap);th=sha(tp);sources[str(ap.relative_to(ROOT))]=ah;sources[str(tp.relative_to(ROOT))]=th
  aa=defaultdict(list);tt=defaultdict(list)
  for line,r in stream(ap):aa[r['family_id'],r['world']].append((line,r))
  for line,r in stream(tp):tt[r['family_id'],r['world']].append((line,r))
  assert len(tt)==32 and sum(map(len,aa.values()))==384
  for key,turns in sorted(tt.items()):
   family,world=key;assert [r['turn'] for _,r in turns]==list(range(1,33));actions=aa[key];assert len(actions)==12
   scenario=scenarios[key];cast=actors(int(family.split('-')[-1]),arm);aliases=[a.alias for a in cast];last={};repeat=repeat_n=statechanges=notes=preferred=adoption_n=0
   for line,a in actions:
    typed=(a.get('slot'),a.get('value'));actor=a['actor']
    if actor in last and a['kind'] in ['edit','recollect','propose']:
     repeat+=typed==last[actor];repeat_n+=1
    if a['kind'] in ['edit','recollect','propose']:last[actor]=typed
    statechanges+=a['memory_before']['state']!=a['memory_after_action']['state'];notes+=a['memory_before']['notes']!=a['memory_after_action']['notes']
    plan=a['following_answer']['parsed'].get('plan',[]);slot=a['assigned_slot'];preferred+=len(plan)>slot and plan[slot]==a['owned_option'];adoption_n+=1
   final=turns[-1][1];trajectory_wrong=0;validplan=0
   for line,r in turns:
    assert r['target']==scenario.truth_at(r['turn']).target(scenario.spec)
    plan=r['generation']['parsed'].get('plan',[]);truth=r['target']['state']
    validplan+=isinstance(plan,list) and len(plan)==8
    trajectory_wrong+=not(isinstance(plan,list) and plan[:6]==truth)
   familyrows.append({'arm':arm,'family_id':family,'world':world,'success':int(final['metrics']['success']),'wrong_final_commitments':int(final['generation']['parsed'].get('plan',[])[:6]!=final['target']['state']),'trajectory_wrong_commitments':trajectory_wrong,'turns':32,'valid_plan_turns':validplan,'preferred_adoption_after_action':preferred,'opportunities':12,'memory_state_changes':statechanges,'note_changes':notes,'typed_repeat':repeat,'typed_repeat_eligible':repeat_n,'switch_value_correct':int(len(final['generation']['parsed'].get('plan',[]))==8 and final['generation']['parsed']['plan'][cast[0].slot]==final['target']['state'][cast[0].slot])})
   choice=[r for r in selected if r['family_id']==family and r['world']==world and r['condition']==arm]
   if not choice:continue
   e={'episode_id':'AC8E-'+rank(f'{arm}:{family}:{world}')[:14],'case_id':family,'condition':arm,'seed':17,'family_id':family,'world':world,'run_id':d['run_id'],'available':True,'actors':[{'alias':a.alias,'neutral':f'Speaker {i+1}','role':a.role,'slot':a.slot,'owned_option':a.owned_option} for i,a in enumerate(cast)],'turns':[],'features':[],'source_bank':{}}
   byturn={r['turn']:(line,r) for line,r in actions};previous=None
   for line,r in turns:
    turn=r['turn'];body=json.loads(r['prompt'][1]['content']);e['catalog']=body['catalog'];user=next(s for s in body['sources'] if s['index']==body['latest_user_index'])
    t={'turn':turn,'event_kind':scenario.events[turn-1].kind,'user':dict(user,locator=source_text_loc(str(tp.relative_to(ROOT)),th,line,body,user['index'])),'defender':{'parsed':r['generation']['parsed'],'raw':r['generation']['raw'],'locator':locator(str(tp.relative_to(ROOT)),th,line,['generation','raw']),'metrics':r['metrics']},'defender_observation':body,'analyst_only_target':r['target'],'action':None}
    if turn in byturn:
     aline,a=byturn[turn];obs=json.loads(a['prompt'][1]['content']);feature=action_features(a,r,previous,scenario,aliases,len(e['features'])+1,aliases.index(a['actor']));e['features'].append(feature)
     t['action']={k:a.get(k) for k in ['actor','kind','slot','value','source','target','claim','applied','rejected_reason','communication_slot']}
     t['action'].update(opportunity=feature['ordinal'],neutral_speaker=f'Speaker {aliases.index(a["actor"])+1}',observation=obs,memory_before=a['memory_before'],memory_before_answer=body['memory'],claim_locator=locator(str(ap.relative_to(ROOT)),ah,aline,['claim']),locator=locator(str(ap.relative_to(ROOT)),ah,aline,[]),generated_claim=(a['generation'].get('parsed') or {}).get('claim',''),truncated=feature['claim_truncated'])
    e['turns'].append(t);previous=r
   e['messages'],checks=reconstruct({'actions':e['features']},6);assert all(c['queue_matches'] for c in checks)
   inputs.append(event_input(e,choice[0],'compatibility'))
 assert len(inputs)==32
 write(HERE/'inputs/compatibility_semantic.json',inputs);write(HERE/'tables/COMPATIBILITY_EPISODES.json',familyrows);write(HERE/'tables/COMPATIBILITY_PROVENANCE.json',sources)
 metrics=['success','wrong_final_commitments','trajectory_wrong_commitments','preferred_adoption_after_action','memory_state_changes','note_changes','typed_repeat','switch_value_correct'];result=[]
 for metric in metrics:
  by=defaultdict(lambda:defaultdict(list))
  for r in familyrows:by[r['family_id']][r['arm']].append(r[metric])
  values=[np.mean(v['incompatible'])-np.mean(v['compatible']) for k,v in sorted(by.items())]
  result.append({'metric':metric,'compatible_sum':sum(r[metric] for r in familyrows if r['arm']=='compatible'),'incompatible_sum':sum(r[metric] for r in familyrows if r['arm']=='incompatible'),'conversations_per_arm':32,'families':16,'difference_per_conversation':float(np.mean(values)),'family_interval':interval_family(values,600017),'contrast':'incompatible minus compatible'})
 # Paired endpoint requires both worlds, never 64 independent subjects.
 paired={arm:{f:all(r['success'] for r in familyrows if r['family_id']==f and r['arm']==arm) for f in sorted(by)} for arm in d['arms']}
 values=[int(paired['incompatible'][f])-int(paired['compatible'][f]) for f in sorted(by)]
 result.append({'metric':'paired_success','compatible_sum':sum(paired['compatible'].values()),'incompatible_sum':sum(paired['incompatible'].values()),'families':16,'difference':float(np.mean(values)),'family_interval':interval_family(values,600017),'contrast':'incompatible minus compatible'})
 write(HERE/'tables/COMPATIBILITY_RESULTS.json',result);print(result)
if __name__=='__main__':
 import argparse;p=argparse.ArgumentParser();p.add_argument('--select',action='store_true');a=p.parse_args();selection() if a.select else extract()
