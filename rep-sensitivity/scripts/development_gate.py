"""Fixed development gate; never changes prompts, thresholds, or held-out data."""
import argparse
import json
from pathlib import Path
from rep_sensitivity.replay import run
from rep_sensitivity.storage import immutable_json

p=argparse.ArgumentParser();p.add_argument('--model',choices=['nemo','qwen3','mistral24','phi4'],required=True)
p.add_argument('--pilot',action='store_true');a=p.parse_args()
def config(name):return json.loads(Path('configs',name+'.json').read_text())
def rows(name):
    return [r for p in Path('artifacts/runs',name,a.model,'scores').glob('*.json') for r in json.loads(p.read_text())]

name='competence-'+a.model+'-v7'
model=run(config(name),a.model)
records=rows(name)
assert len(records)==96
rates={kind:sum(r['correct'] for r in records if r['kind']==kind)/sum(r['kind']==kind for r in records)
       for kind in ('schedule','workflow')}
passed=all(value>=0.85 for value in rates.values())
decision={'suite':name,'accuracy':rates,'threshold':0.85,'passed':passed,
          'rule':'Both task populations meet the unchanged point-estimate development threshold; not a power or robustness claim.'}
immutable_json(Path('records/gates')/(name+'.json'),decision)
print(json.dumps(decision),flush=True)
if not passed:raise SystemExit('Competence gate not met; no pilot launch for this model')
smoke='summary-smoke-'+a.model+'-v7'
run(config(smoke),a.model,model=model)
records=rows(smoke)
valid=len(records)==12 and not any(r['operational_failure'] for r in records)
immutable_json(Path('records/gates')/(smoke+'.json'),{'suite':smoke,'trajectories':len(records),'contract_valid':valid})
if not valid:raise SystemExit('Summary contract check failed; pilot remains blocked')
if a.pilot:
    if a.model!='qwen3':raise ValueError('The prespecified one-model pilot uses Qwen3')
    run(config('pilot-v7'),a.model,model=model)
