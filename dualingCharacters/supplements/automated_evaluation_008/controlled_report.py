"""Denominator-explicit presentation of frozen controlled outcomes; no new causal endpoint."""
from .common import *
from collections import Counter

def main():
 episodes=read(HERE/'tables/COMPATIBILITY_EPISODES.json');rows=[]
 for arm in ['compatible','incompatible']:
  for world in ['all','authorized','hypothetical']:
   z=[r for r in episodes if r['arm']==arm and (world=='all' or r['world']==world)];total=lambda k:sum(r[k] for r in z)
   rows.append({'arm':arm,'world':world,'conversations':len(z),'successes':total('success'),'wrong_final_commitments':total('wrong_final_commitments'),'decisive_field_correct':total('switch_value_correct'),'interventions':total('opportunities'),'preferred_option_adoption':total('preferred_adoption_after_action'),'immediate_state_changes':total('memory_state_changes'),'note_changes':total('note_changes'),'repeated_typed_goals':total('typed_repeat'),'eligible_direct_goal_transitions':total('typed_repeat_eligible'),'incorrect_commitment_turns':total('trajectory_wrong_commitments'),'answerer_turns':total('turns'),'valid_plan_turns':total('valid_plan_turns')})
 write(HERE/'tables/COMPATIBILITY_COUNTS.json',rows);csv_write(HERE/'tables/COMPATIBILITY_COUNTS.csv',rows)
 run=ROOT/'artifacts/runs/dialogue005-compat-17-v1';channels=[]
 for arm in ['compatible','incompatible']:
  counter=Counter()
  for line,r in stream(run/(arm+'_characters.jsonl')):
   counter[r['kind'],r['communication_slot'],r['applied']]+=1
  for (kind,comm,applied),n in sorted(counter.items()):channels.append({'arm':arm,'kind':kind,'communication_slot':comm,'applied':applied,'count':n,'allocated_opportunities':384})
 csv_write(HERE/'tables/COMPATIBILITY_CHANNELS.csv',channels)
 # Reproduction verifies the original pre-inference binding; never re-dates or enables it.
 binding=read(HERE/'reports/COMPATIBILITY_SEMANTIC_INPUT_BINDING.json')
 assert binding['selection_sha256']==sha(HERE/'inputs/COMPATIBILITY_SEMANTIC_SELECTION.json')
 assert binding['payload_sha256']==sha(HERE/'inputs/compatibility_semantic.json')
 for model in ['phi','qwen']:
  a=read(HERE/f'admissions/compatibility_judge_{model}.json')
  assert a['inputs_sha256']==binding['payload_sha256']
 print(rows)
if __name__=='__main__':main()
