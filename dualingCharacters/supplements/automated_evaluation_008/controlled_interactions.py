"""Existing compatibility primary response distribution, over every reserved opportunity."""
from collections import defaultdict,Counter
import numpy as np
from .common import *
from .analysis import interval_family
from supplements.evidence_validation_006.compatibility_design import load_scenarios,actors
from supplements.behavior_characterization_004.records import action_features
from supplements.behavior_characterization_004.peers import reconstruct

def main():
 design=read(ROOT/'supplements/evidence_validation_006/compatibility/DESIGN.json');scenarios={(s.family_id,s.world):s for s in load_scenarios(design)};run=ROOT/'artifacts/runs'/design['run_id'];rows=[];compliance=[];hashes={}
 for arm in design['arms']:
  ap=run/(arm+'_characters.jsonl');tp=run/(arm+'.jsonl');hashes[str(ap.relative_to(ROOT))]=sha(ap);hashes[str(tp.relative_to(ROOT))]=sha(tp)
  actions={};turns=defaultdict(list)
  for line,r in stream(ap):actions[r['family_id'],r['world'],r['turn']]=(line,r)
  for line,r in stream(tp):turns[r['family_id'],r['world']].append(r)
  for key,tt in sorted(turns.items()):
   family,world=key;cast=actors(int(family.split('-')[-1]),arm);aliases=[a.alias for a in cast];features=[];previous=None;raw={}
   for t in tt:
    a=actions.get((*key,t['turn']))
    if a:
     line,r=a;feature=action_features(r,t,previous,scenarios[key],aliases,len(features)+1,aliases.index(r['actor']));features.append(feature);raw[feature['ordinal']]=(line,r)
     compliance.append({'arm':arm,'family_id':family,'world':world,'opportunity':feature['ordinal'],'actor':r['actor'],'role':r['role'],'valid_typed_action':feature['valid'] and feature['goal'] is not None,'typed_owned_goal':feature['valid'] and feature['goal']==(r['assigned_slot'],r['owned_option']),'channel':feature['channel'],'qualification':'Post-run descriptive manipulation-compliance check; typed values do not prove textual agreement.'})
    previous=t
   messages,checks=reconstruct({'actions':features},6);assert all(c['queue_matches'] for c in checks);by={m['ordinal']:m for m in messages};ff={f['ordinal']:f for f in features}
   for f in features:
    if not f['communication_slot']:continue
    m=by.get(f['ordinal']);category='no_peer_message'
    if m:
     if m['recipient_type']=='invalid':category='invalid_recipient'
     elif not m['delivered']:category='not_delivered'
     elif m['recipient_type']=='answerer':category='answerer_directed'
     elif m['next_recipient_opportunity'] is None:category='missing_recipient_opportunity'
     elif m['visible'] is not True:category='visibility_not_confirmed'
     else:category='component_'+m['next_response']
    before=ff.get(m['previous_recipient_opportunity']) if m else None;after=ff.get(m['next_recipient_opportunity']) if m else None
    rows.append({'arm':arm,'family_id':family,'world':world,'opportunity':f['ordinal'],'category':category,'selected_kind':f['kind'],'selected_claim':f['claim'],'delivered':m['delivered'] if m else False,'visible':m['visible'] if m else None,'recipient_type':m['recipient_type'] if m else None,'previous_relation':m['previous_response'] if m else None,'next_relation':m['next_response'] if m else None,'prior_claim':before['claim'] if before else None,'next_claim':after['claim'] if after else None,'claim_unchanged_from_prior':before['claim']==after['claim'] if before and after else None,'next_mentions_sender':m['next_mentions_sender'] if m else None,'raw_file':str(ap.relative_to(ROOT)),'raw_record':raw[f['ordinal']][0],'raw_sha256':sha(ap)})
 assert len(rows)==256 and all(sum(r['arm']==a for r in rows)==128 for a in design['arms'])
 write(HERE/'tables/COMPATIBILITY_INTERACTION_EVENTS.json',rows);write(HERE/'tables/COMPATIBILITY_COMPLIANCE.json',compliance)
 categories=sorted({r['category'] for r in rows});summary=[]
 for category in categories:
  by=defaultdict(lambda:defaultdict(list))
  for r in rows:by[r['family_id']][r['arm']].append(int(r['category']==category))
  values=[np.mean(v['incompatible'])-np.mean(v['compatible']) for f,v in sorted(by.items())]
  summary.append({'category':category,'compatible_count':sum(r['category']==category and r['arm']=='compatible' for r in rows),'incompatible_count':sum(r['category']==category and r['arm']=='incompatible' for r in rows),'allocated_reserved_per_arm':128,'families':16,'difference_rate':float(np.mean(values)),'family_interval':interval_family(values,600017),'qualification':'Incompatible minus compatible. API typed-response categories, not semantic endorsement or causal influence.'})
 write(HERE/'tables/COMPATIBILITY_PRIMARY_RESPONSE.json',summary);csv_write(HERE/'tables/COMPATIBILITY_PRIMARY_RESPONSE.csv',summary)
 transitions=[]
 for arm in design['arms']:
  counts=Counter((r['previous_relation'],r['next_relation']) for r in rows if r['arm']==arm and r['recipient_type']=='component' and r['visible'] is True)
  for (before,after),n in sorted(counts.items(),key=str):transitions.append({'arm':arm,'before_relation':before,'after_relation':after,'count':n})
 csv_write(HERE/'tables/COMPATIBILITY_TYPED_TRANSITIONS.csv',transitions)
 write(HERE/'reports/COMPATIBILITY_INTERACTION_AUDIT.json',{'source_hashes':hashes,'reserved_events':256,'episodes':64,'families':16,'all_inbox_reconstructions_match':True,'endpoint_source':'evidence_validation_006/compatibility/README.md: primary next-recipient-action distribution','postrun_added_check':'Typed motive adherence, explicitly descriptive; no change to frozen outcomes or models.'})
 print(summary)
if __name__=='__main__':main()
