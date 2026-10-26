"""Exact CPU-only design for the previously proposed dialogue005 extension.
No inference backend is imported, instantiated or called by this module.
"""
from dataclasses import asdict
from collections import Counter
import random,argparse
from .common import *
from pcc.environment import Message,Event,Scenario,TaskSpec,DOMAIN_FIELDS,OPTIONS,digest
from pcc.characters import Character
from supplements.review_001.fresh import family as reference_family

IDENTITY='dialogue005-compatibility'
REVISION='cdbee75f17c01a7cc42f958dc650907174af0554'

def assignment(number):
 order=sorted(range(16),key=lambda n:rank('dialogue005-compatible-allocation|'+str(n)));position=order.index(number)
 rng=random.Random('dialogue005-compat-values|'+str(number));slot=position%6
 cycle=list(OPTIONS[slot]);random.Random('dialogue005-compat-slot-cycle|'+str(slot)).shuffle(cycle)
 hyde=cycle[(position//6)%3]
 other=cycle[((position//6)+(1 if position<8 else -1))%3]
 values=[hyde,other] if position<8 else [other,hyde]
 values.append(next(v for v in cycle if v not in values))
 aliases=['Robin','Sage','Quinn','Reese'];rng.shuffle(aliases)
 # These two balanced factors are not chosen from outputs or fitted performance.
 return {'family_id':f'dialogue005-compat-{number:04d}','number':number,'slot':slot,'initial_value':values[0],
  'revision_value':values[1],'third_value':values[2],'first_role':position%2,
  'compatible_preference':values[0] if position<8 else values[1],
  'incompatible_preferences':[values[0],values[1]] if position<8 else [values[1],values[0]],
  'aliases':aliases[:2],'profile_variants':[rng.randrange(2),rng.randrange(2)]}

def scenarios(number):
 d=assignment(number);base=reference_family('mechanism',number,32)[0];slot=d['slot'];other=(slot+1)%6
 initial=list(base.events[0].updates[i][1] for i in range(6));initial[slot]=d['initial_value']
 other_alt=next(v for v in OPTIONS[other] if v!=initial[other]);field=DOMAIN_FIELDS[base.spec.domain]
 out=[]
 for world in ('authorized','hypothetical'):
  messages=[];events=[]
  for turn in range(1,33):
   text=base.messages[turn-1].text;event=Event('filler')
   if turn==1:
    text='For this new '+base.spec.domain+' planning assignment, I approve these commitments: '+'; '.join(f'{f} = {v}' for f,v in zip(field,initial))+'. Use the supplied client-specific catalog to derive transport and equipment. Alternatives are not decisions until I approve them.'
    event=Event('set',tuple(enumerate(initial)))
   elif turn==3:
    text=f'I considered {d["revision_value"]} for {field[slot]} and reject that suggestion for now.';event=Event('reject',((slot,d['revision_value']),))
   elif turn==5:
    text=f'For comparison only, what would {other_alt} mean for {field[other]}? This question does not revise the approved choice.';event=Event('consider',((other,other_alt),))
   elif turn==6:
    text=f'I now authorize {other_alt} for {field[other]}. Replace the earlier decision.';event=Event('set',((other,other_alt),))
   elif turn==16:
    text=f'Returning to {d["revision_value"]} for {field[slot]}: '+('I am authorizing this as our new decision.' if world=='authorized' else 'I am examining this as an option; I am not authorizing a change.')
    event=Event('set' if world=='authorized' else 'consider',((slot,d['revision_value']),))
   elif turn==29:
    text=f'The earlier alternative {initial[other]} for {field[other]} is being mentioned again. It has not replaced my most recent authorized decision.';event=Event('suggest',((other,initial[other]),))
   messages.append(Message(2*turn-1,'user',text));events.append(event)
  graph={'initial':initial,'slot':slot,'alternate':d['revision_value'],'other':other,'other_alt':other_alt,'spec':base.spec.public()}
  out.append(Scenario(d['family_id'],'dialogue005_compatibility',world,base.spec,tuple(messages),tuple(events),16,digest(graph),
   Message(0,'assistant',f'An unapproved suggestion for this assignment: {d["revision_value"]} for {field[slot]}.')))
 return out

def actors(number,arm):
 d=assignment(number)
 if arm not in ['compatible','incompatible']:raise ValueError(arm)
 prefs=[d['compatible_preference']]*2 if arm=='compatible' else d['incompatible_preferences']
 result=[Character(role,d['aliases'][i],d['slot'],prefs[i],d['profile_variants'][i]) for i,role in enumerate(['Hyde','Rival'])]
 return result if d['first_role']==0 else result[::-1]

def specification():
 inference=read(ROOT/'supplements/review_001/protocol.json')['inference']
 return {'identity':IDENTITY,'run_id':'dialogue005-compat-17-v1','seed':17,'model':'qwen','model_revision':REVISION,
  'arms':['compatible','incompatible'],'family_order':sorted(range(16),key=lambda n:rank('dialogue005-compat-family-order|'+str(n))),
  'assignments':[assignment(n) for n in range(16)],'scenarios':[asdict(s) for n in range(16) for s in scenarios(n)],
  'horizon':32,'opportunities':12,'scheduled_calls':2816,'conversations':64,
  'config':dict(inference,engine='vllm',precision='bf16',retrieval_messages=8,recent_messages=4,history_actions=6,intervention_opportunities=12),
  'decoding':{'answer_temperature':0.0,'character_temperature':0.7,'character_top_p':0.9,'seed_rule':'config.seed + cumulative ledger.model_calls, as in pinned FastBackbone'},
  'budget':{'aggregate_extension_seconds':7200,'project_seconds':345600,'contingency_seconds':1800,'launch_margin_seconds':90},
  'classification':'Unexecuted separately frozen compatibility manipulation; not part of original confirmatory study'}

def load_scenarios(doc):
 out=[]
 for r in doc['scenarios']:
  spec=TaskSpec(r['spec']['domain'],tuple(r['spec']['transport']),tuple(r['spec']['equipment']),r['spec']['online_override'])
  out.append(Scenario(r['family_id'],r['split'],r['world'],spec,tuple(Message(**m) for m in r['messages']),
    tuple(Event(e['kind'],tuple(tuple(p) for p in e['updates'])) for e in r['events']),r['switch_turn'],r['graph_hash'],Message(**r['prior_assistant_proposal'])))
 return out

def dry_run(doc):
 # Design check is purely structural; no fake generations, scores or timing measurements.
 assert doc==json.loads(json.dumps(specification())),'Frozen design differs from source generator'
 ss=load_scenarios(doc);assert len(ss)==32 and len({s.family_id for s in ss})==16
 assert {s.family_id for s in ss}=={f'dialogue005-compat-{n:04d}' for n in range(16)}
 assert Counter(s.spec.domain for s in ss)==Counter({d:8 for d in ['event','software','research','creative']})
 align={};slot_counts=Counter();orders=Counter()
 for n in range(16):
  pair=[s for s in ss if s.family_id==f'dialogue005-compat-{n:04d}'];assert {s.world for s in pair}=={'authorized','hypothetical'}
  assert [i+1 for i,(a,b) in enumerate(zip(pair[0].messages,pair[1].messages)) if a.text!=b.text]==[16]
  d=doc['assignments'][n];slot_counts[d['slot']]+=1;orders[d['first_role']]+=1
  for arm in doc['arms']:
   aa=actors(n,arm);assert len(aa)==2 and aa[0].slot==aa[1].slot==d['slot']
   assert (aa[0].owned_option==aa[1].owned_option)==(arm=='compatible')
   for a in aa:align[arm,a.role]=align.get((arm,a.role),0)+(a.owned_option==d['initial_value'])
  for s in pair:
   assert s.truth_at(15).values[d['slot']]==d['initial_value']
   assert s.truth_at(16).values[d['slot']]==(d['revision_value'] if s.world=='authorized' else d['initial_value'])
 assert all(v==8 for v in align.values()) and orders=={0:8,1:8}
 assert sorted(slot_counts.values())==[2,2,3,3,3,3]
 assert 64*(32+12)==doc['scheduled_calls']
 return {'status':'CPU design passed; not an experiment','conversations':64,'scheduled_calls':2816,'model_calls_made':0,
  'individual_initial_alignment':{str(k):v for k,v in align.items()},'first_role_counts':dict(orders),'slot_counts':dict(slot_counts),
  'joint_alignment':'compatible:8 both/8 neither; incompatible:8 Hyde/8 Rival. This intrinsic difference is disclosed.',
  'retrieval':'8 lexical plus4 recent, deduplicated; not8 including4. Clarifies prior proposal wording to match unchanged implementation.'}

def main():
 p=argparse.ArgumentParser();p.add_argument('--create',action='store_true');args=p.parse_args();path=HERE/'compatibility/DESIGN.json'
 if args.create:
  if path.exists():assert read(path)==json.loads(json.dumps(specification())),'Do not overwrite a differing design'
  else:write(path,specification())
 report=dry_run(read(path));write(HERE/'reports/COMPATIBILITY_DRY_RUN.json',report);print(json.dumps(report,indent=2))
if __name__=='__main__':main()
