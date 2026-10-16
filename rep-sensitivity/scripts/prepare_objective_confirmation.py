"""Outcome-blind candidate allocation and preflight input inventory."""
from pathlib import Path
import json
from collections import Counter
from rep_sensitivity.objective_confirmation import prepare
from rep_sensitivity.schema import digest
from rep_sensitivity.storage import immutable_json,utcnow
if __package__:
    from .check_fresh_pair_separation import select
else:
    from check_fresh_pair_separation import select

selection=select()
config=json.loads(Path('configs/objective-confirmation-v1.json').read_text())
config.update(pair_indices=[p['index'] for p in selection['selected']],pair_ids=[p['pair_id'] for p in selection['selected']])
Path('configs/objective-confirmation-v1.json').write_text(json.dumps(config,indent=2)+'\n')
manifest,plans=prepare(config)
meta=Counter()
for pair,models in plans:
    for j in models['qwen3']:
        if j['trial']['arm']!='single':continue
        truth=pair['evaluation']['oracle'][j['trial']['world']];target=j['audit']['target_candidate']
        meta['target_correct_choice']+=target==truth['answer'];meta['target_infeasible']+=not truth['candidates'][target]['feasible']
        meta['target_raw_lowest_objective']+=truth['candidates'][target]['objective']==min(c['objective'] for c in truth['candidates'].values())
record={'utc':utcnow(),'selection':selection,'manifest':manifest,'target_contexts':48,'target_roles':dict(meta),
        'main_outcomes_inspected':False,'new_confirmation_responses':0,
        'validation_analysis_available':'results/validation-repetition-v1/analysis.json; no condition or allocation chosen by favorable outcome'}
immutable_json('records/planning/objective-confirmation-v1-candidate.json',record)
print(json.dumps({'bases':manifest['base_pairs'],'trajectories':manifest['trajectories'],'logical_calls':manifest['logical_calls'],'target_roles':dict(meta)}))
