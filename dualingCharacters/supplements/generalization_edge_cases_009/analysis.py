"""Frozen trajectory calculations. Actions/turns are not independent subjects."""
from collections import defaultdict,Counter
import csv,numpy as np
from pcc.environment import FIELDS,OPTIONS
from .common import *
from .scenarios import all_scenarios,metadata

def stream(p):
 with Path(p).open() as f:
  for i,line in enumerate(f,1):yield i,json.loads(line)
def field_correct(row,slot):
 p=row['generation'].get('parsed',{});plan=p.get('plan',[]);clarify=p.get('clarify',[]);truth=row['target']
 return bool(isinstance(plan,list) and len(plan)>slot and plan[slot]==truth['plan'][slot] and isinstance(clarify,list) and (FIELDS[slot] in clarify)==(FIELDS[slot] in truth['clarify']))
def recovery(bits,turns,event,hold=3):
 pairs=[(t,b) for t,b in zip(turns,bits) if t>=event]
 if not pairs:return {'status':'missing','latency':None}
 if all(b for t,b in pairs):return {'status':'never_wrong','latency':None}
 first_wrong=next(i for i,(t,b) in enumerate(pairs) if not b)
 # Sustained recovery starts AFTER an observed error; three consecutive later observations.
 for i in range(first_wrong+1,len(pairs)-hold+1):
  if all(b for t,b in pairs[i:i+hold]):return {'status':'recovered','latency':pairs[i][0]-pairs[first_wrong][0],'first_wrong_turn':pairs[first_wrong][0],'recovery_turn':pairs[i][0],'since_event':pairs[i][0]-event}
 return {'status':'unrecovered','latency':None,'first_wrong_turn':pairs[first_wrong][0]}
def eligible_goal(a):
 k=a.get('slot');v=a.get('value')
 return (k,v) if type(k)==int and 0<=k<6 and v in OPTIONS[k] else None
def action_metrics(actions,answers):
 counts=Counter(a.get('kind','missing') for a in actions);actors=defaultdict(list);repeated=eligible=0;exact=changed=notes=source_missing=source_disagree=0
 for a in actions:
  actors[a['actor']].append(a)
  before=json.loads(a['prompt'][-1]['content'])['memory'];after=json.loads(answers[a['turn']]['prompt'][-1]['content'])['memory']
  changed+=before['state']!=after['state'];notes+=before['notes']!=after['notes']
  source=a.get('source');sources=json.loads(a['prompt'][-1]['content'])['sources'];source_missing+=source is not None and source not in {s['index'] for s in sources}
  k=a.get('slot');source_disagree+=type(k)==int and 0<=k<6 and source!=answers[a['turn']]['target']['evidence'][k]
 for seq in actors.values():
  direct=[a for a in seq if a.get('applied') and a['kind'] in {'edit','recollect','propose'} and eligible_goal(a)]
  for first,second in zip(direct,direct[1:]):eligible+=1;repeated+=eligible_goal(first)==eligible_goal(second);exact+=first.get('claim')==second.get('claim')
 return {'opportunities':len(actions),**{k:counts[k] for k in ('edit','recollect','propose','peer','pass')},'other_kind':sum(v for k,v in counts.items() if k not in {'edit','recollect','propose','peer','pass'}),'applied':sum(a.get('applied',False) for a in actions),'communication_opportunities':sum(a['communication_slot'] for a in actions),'component_deliveries':sum(a['kind']=='peer' and a.get('applied') and a.get('target')!='Jekyll' for a in actions),'answerer_notes':sum(a['kind']=='peer' and a.get('applied') and a.get('target')=='Jekyll' for a in actions),'direct_state_changes':changed,'note_changes':notes,'repeat_n':repeated,'repeat_d':eligible,'exact_claim_repeat_n':exact,'cited_source_unavailable':source_missing,'canonical_source_disagreement':source_disagree}
def interval(values):
 if not values:return [None,None]
 x=np.asarray(values,float);rng=np.random.default_rng(900031);v=x[rng.integers(0,len(x),(10000,len(x)))].mean(1)
 return list(map(float,np.quantile(v,[.025,.975])))
def csvwrite(path,rows):
 if not rows:return
 with path.open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def compute(run_root=None):
 run_root=Path(run_root) if run_root else ROOT/'artifacts/runs';allocation=read(HERE/'ALLOCATION.json');scenarios={(s.family_id,s.world):s for s in all_scenarios()};episodes=[];missing=[];provenance=[]
 for job in allocation['jobs']:
  folder=run_root/job['run_id'];status=read(folder/'status.json') if (folder/'status.json').exists() else {}
  for condition in job['conditions']:
   path=folder/(condition+'.jsonl');apath=folder/(condition+'_characters.jsonl');answers=defaultdict(dict);actions=defaultdict(list)
   if path.exists():
    for lineno,r in stream(path):
     key=(r['family_id'],r['world']);assert r['turn'] not in answers[key],'duplicate turn';answers[key][r['turn']]=r
     assert r['condition']==condition and r['seed']==job['seed']
     assert r['target']==scenarios[key].truth_at(r['turn']).target(scenarios[key].spec),'Time-indexed target mismatch'
    provenance.append({'file':str(path.relative_to(run_root)),'sha256':sha(path),'bytes':path.stat().st_size})
   if apath.exists():
    for lineno,r in stream(apath):actions[r['family_id'],r['world']].append(r)
    provenance.append({'file':str(apath.relative_to(run_root)),'sha256':sha(apath),'bytes':apath.stat().st_size})
   for key,s in scenarios.items():
    rows=answers[key];act=actions[key]
    if set(rows)!=set(range(1,33)) or len(act)!=12:
     missing.append({'run_id':job['run_id'],'condition':condition,'family_id':key[0],'world':key[1],'turns':len(rows),'opportunities':len(act)});continue
    m=metadata(s);k=m['slot'];bits=[field_correct(rows[t],k) for t in range(1,33)];rec=recovery(bits,list(range(1,33)),m['final_resolution_turn'])
    post=list(range(12,20 if m['pattern']=='ambiguity_resolution' else 33));active=[t for t in post if rows[t]['target']['plan'][k] is not None]
    collateral=0;wrong_commitments=0;unauthorized_revisions=0
    for t in active:
     plan=rows[t]['generation'].get('parsed',{}).get('plan',[]);previous=rows[t-1]['generation'].get('parsed',{}).get('plan',[])
     value=plan[k] if isinstance(plan,list) and len(plan)>k else None
     prior=previous[k] if isinstance(previous,list) and len(previous)>k else None
     wrong=value in OPTIONS[k] and value!=rows[t]['target']['plan'][k]
     wrong_commitments+=wrong;unauthorized_revisions+=wrong and value!=prior
    for t in range(25,33):
     plan=rows[t]['generation'].get('parsed',{}).get('plan',[]);plan=plan if isinstance(plan,list) else []
     collateral+=sum(j>=len(plan) or plan[j]!=rows[t]['target']['plan'][j] for j in range(6) if j!=k)
    ep={**m,'model':job['model'],'seed':job['seed'],'condition':condition,'run_id':job['run_id'],'final_correct':int(bits[-1]),'full_plan_success':int(rows[32]['metrics']['success']),'last8_correct':sum(bits[-8:]),'last8_denominator':8,'post_event_wrong':sum(not bits[t-1] for t in active),'post_event_denominator':len(active),'wrong_commitments':wrong_commitments,'unauthorized_revision_transitions':unauthorized_revisions,'collateral_wrong':collateral,'collateral_denominator':40,'clarification_correct':sum(rows[t]['metrics']['clarification_correct'] for t in range(12,33)),'clarification_denominator':21,'recovery_status':rec['status'],'recovery_latency':rec['latency'],'recovery_since_event':rec.get('since_event'),'final_decisive_source_visible':int(rows[32]['target']['evidence'][k] in rows[32]['visible_indices']),'trajectory':''.join('1' if b else '0' for b in bits),'input_tokens':sum(r['generation']['input_tokens'] for r in rows.values())+sum(a['generation']['input_tokens'] for a in act),'output_tokens':sum(r['generation']['output_tokens'] for r in rows.values())+sum(a['generation']['output_tokens'] for a in act),**action_metrics(act,rows)}
    episodes.append(ep)
 write(HERE/'tables/episodes.json',episodes);csvwrite(HERE/'tables/episodes.csv',episodes);write(HERE/'reports/MISSING_CELLS.json',missing);write(HERE/'reports/RAW_PROVENANCE.json',provenance)
 paired=[]
 for model in allocation['models']:
  for seed in allocation['seeds']:
   for fid in sorted({s.family_id for s in scenarios.values()}):
    group=[e for e in episodes if e['model']==model and e['seed']==seed and e['family_id']==fid]
    if len(group)!=6:continue # All three conditions/two worlds required for every comparison.
    for c in ('C3','C5','A1'):
     pair=[e for e in group if e['condition']==c];assert {e['world'] for e in pair}=={'authorized','hypothetical'}
     paired.append({'model':model,'seed':seed,'family_id':fid,'context':pair[0]['context'],'pattern':pair[0]['pattern'],'condition':c,'paired_success':int(all(e['final_correct'] for e in pair)),**{metric:sum(e[metric] for e in pair) for metric in ['last8_correct','last8_denominator','opportunities','edit','recollect','propose','peer','pass','direct_state_changes','repeat_n','repeat_d']}})
 write(HERE/'tables/families.json',paired);csvwrite(HERE/'tables/families.csv',paired)
 comparisons=[]
 for model in allocation['models']:
  for control in ('C3','A1'):
   rows=[r for r in paired if r['model']==model];fids=sorted({r['family_id'] for r in rows});diffs=[];trans=Counter()
   for f in fids:
    rr=[r for r in rows if r['family_id']==f];a={r['seed']:r['paired_success'] for r in rr if r['condition']=='C5'};b={r['seed']:r['paired_success'] for r in rr if r['condition']==control};assert a.keys()==b.keys()
    diffs.append(sum(a[s]-b[s] for s in a)/len(a))
    for s in a:trans[f'{a[s]}{b[s]}']+=1
   comparisons.append({'model':model,'comparison':'C5-'+control,'complete_unique_families':len(fids),'family_seed_pairs':sum(trans.values()),'difference':float(np.mean(diffs)) if diffs else None,'interval95_family_bootstrap':interval(diffs),'transitions':dict(trans),'qualification':'Families resampled with worlds, methods and repeated seeds retained; backbones fixed. Not population training-seed uncertainty.'})
 write(HERE/'tables/contrasts.json',comparisons);return episodes,paired,comparisons
if __name__=='__main__':
 import argparse;p=argparse.ArgumentParser();p.add_argument('--run-root');a=p.parse_args();compute(a.run_root)
