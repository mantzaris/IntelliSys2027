"""Descriptive opportunity audit: does the actor own the tested field?"""
from pcc.characters import cast
from .common import *
from .scenarios import all_scenarios,metadata
from .analysis import stream,csvwrite,eligible_goal

def main(run_root=None):
 root=Path(run_root) if run_root else ROOT/'artifacts/runs';sc={(s.family_id,s.world):s for s in all_scenarios()};rows=[]
 for job in read(HERE/'ALLOCATION.json')['jobs']:
  for c in job['conditions']:
   grouped={key:[] for key in sc}
   for line,r in stream(root/job['run_id']/(c+'_characters.jsonl')):grouped[r['family_id'],r['world']].append(r)
   for key,s in sc.items():
    m=metadata(s);k=m['slot'];actors=cast(c,s.family_id,job['seed']);acts=grouped[key];post=[r for r in acts if r['turn']>=12];direct=[r for r in post if r['kind'] in {'edit','recollect','propose'} and r['applied'] and eligible_goal(r)]
    targets=[r for r in direct if r['slot']==k];wrong=[r for r in targets if k not in s.truth_at(r['turn']).pending and r['value']!=s.truth_at(r['turn']).values[k]]
    away=[x for x in actors if x.slot==k and x.owned_option==s.truth_at(11).values[k] and s.truth_at(12).values[k]!=x.owned_option]
    insist=[r for r in post if r['actor'] in {x.alias for x in away} and eligible_goal(r) and r['value']==r['owned_option'] and r['slot']==r['assigned_slot']]
    rows.append({**m,'model':job['model'],'seed':job['seed'],'condition':c,'decisive_field_owned_by_actor':any(x.slot==k for x in actors),'post_event_opportunities':len(post),'post_event_valid_direct_actions':len(direct),'post_event_direct_actions_on_decisive_field':len(targets),'post_event_direct_wrong_definite_values':len(wrong),'actors_revised_away_from_owned_at12':len(away),'owned_goal_actions_after_revision_away':len(insist),'eligible_post_revision_actor_opportunities':sum(r['actor'] in {x.alias for x in away} for r in post)})
 csvwrite(HERE/'tables/decisive_field_exposure.csv',rows);write(HERE/'tables/decisive_field_exposure.json',rows)
 print({'unique_families':len({r['family_id'] for r in rows}),'families_with_owned_decisive_field':len({r['family_id'] for r in rows if r['decisive_field_owned_by_actor']})})
if __name__=='__main__':
 import argparse;p=argparse.ArgumentParser();p.add_argument('--run-root');a=p.parse_args();main(a.run_root)
