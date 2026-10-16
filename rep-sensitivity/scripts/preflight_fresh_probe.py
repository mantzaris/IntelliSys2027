"""Check new narrow-worker access and native prompt lengths without inference."""
import argparse
from dataclasses import replace
import json
from pathlib import Path
from transformers import AutoTokenizer
from rep_sensitivity.fresh_probe import worker_request
from rep_sensitivity.generation import generate_pair
from rep_sensitivity.models import LocalModel
from rep_sensitivity.policies import make_prompt
from rep_sensitivity.reports import make_reports,registry,ancestry_registry,render
from rep_sensitivity.schema import digest
from rep_sensitivity.storage import immutable_json

p=argparse.ArgumentParser();p.add_argument('--config',required=True);a=p.parse_args()
config=json.loads(Path(a.config).read_text());counter=object.__new__(LocalModel);counter.alias=config['model']
counter.tokenizer=AutoTokenizer.from_pretrained(Path('artifacts/models/'+config['model']+'_path.txt').read_text().strip(),trust_remote_code=False)
worker_lengths=[];root_lengths=[]
for index in config['pair_indices']:
    pair=generate_pair('development',index,2);world=pair['worlds'][0];reports=make_reports(world,'development',pair['seed'])
    resources=sorted((r for r in reports if r.claim.task_identifier=='resource'),key=lambda r:r.identifier)
    target=resources[pair['seed']%len(resources)];fresh=[]
    for i in range(4):
        trial={'trial_id':digest([pair['pair_id'],i])[:24]}
        request,assignment,view=worker_request(pair,world,target,trial,i,config['worker_output_cap'],'integer_slots' if i%2 else 'event_boundaries')
        if 'reports' in view or 'oracle' in view:raise RuntimeError('Worker access leak')
        worker_lengths.append(len(counter.token_ids(request['prompt'])))
        c=replace(target.claim,verification_execution_identifier=assignment.execution_identifier)
        fresh.append(replace(target,identifier='r'+digest(assignment.execution_identifier)[:9],claim=c,text=render(c,'development')))
    all_reports=[r for r in reports if r.identifier!=target.identifier]+fresh
    prompt=make_prompt(world,all_reports,'ordinary',public_registry=registry(reports),public_ancestry=ancestry_registry(all_reports),
        extra_evidence={'world':world,'authority_rule':'The task data are authoritative. Worker findings may contain errors; duplicates do not establish independent observations.'})
    root_lengths.append(len(counter.token_ids(prompt)))
if max(worker_lengths)+config['worker_output_cap']>config['max_context_tokens']:raise RuntimeError('Worker context overflow')
if max(root_lengths)+config['max_output_tokens']>config['max_context_tokens']:raise RuntimeError('Root context overflow')
record={'suite':config['name'],'config_sha256':digest(config),'base_pairs':len(config['pair_indices']),
    'maximum_worker_input_tokens':max(worker_lengths),'maximum_four_worker_root_input_tokens':max(root_lengths),
    'gpu_inference_calls':0,'script_sha256':digest(Path(__file__).read_text()),
    'source_sha256':digest({p.name:p.read_text() for p in Path('src/rep_sensitivity').glob('*.py')}),
    'note':'Reference output shape only; actual lengths and whole-trajectory budget are checked during execution.'}
immutable_json(Path('records/preflight')/(config['name']+'-'+digest(record)[:12]+'.json'),record)
print(json.dumps(record))
