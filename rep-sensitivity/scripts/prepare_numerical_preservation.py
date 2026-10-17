"""Freeze the new diagnostic after CPU/native-token and measured-time checks."""
from pathlib import Path
from collections import defaultdict
import gzip
import json
import subprocess
import numpy as np
from transformers import AutoTokenizer
from rep_sensitivity.models import LocalModel
from rep_sensitivity.objective_preservation import plan,input_inventory
from rep_sensitivity.schema import digest
from rep_sensitivity.storage import immutable_json,utcnow


def main():
    # Reuse an already fixed development subset, not an outcome-selected sample.
    old=json.loads(Path('configs/frozen/root-diagnostic-v1.json').read_text())
    config={k:old[k] for k in ('source_run','pair_indices','model','worlds','stochastic_repetitions','temperature','top_p',
                              'max_output_tokens','batch_size','guided_decoding','enforce_eager','gpu_memory_utilization')}
    config.update(name='numerical-preservation-v1',status='frozen',max_context_tokens=12288,ordering_seed=2026101701,
        maximum_gpu_wall_seconds=900,shared_gpu_wall_seconds_cap=7200,
        budget_journal='artifacts/runs/objective-confirmation-execution/budget.jsonl',
        run_after='original Phi-4, all existing extensions and both models of objective-confirmation-v1',
        interpretation='Exploratory fresh root replay conditional on fixed cached managers from the original upstream single/exact treatments. Repair uses branch-visible worker objectives only. No fresh end-to-end hierarchy or causal-mediation identification.')
    pairs,jobs=plan(config);inventory=input_inventory(jobs);config['input_inventory_sha256']=digest(inventory)
    counter=object.__new__(LocalModel);counter.alias='qwen3'
    counter.tokenizer=AutoTokenizer.from_pretrained(Path('artifacts/models/qwen3_path.txt').read_text().strip(),trust_remote_code=False)
    lengths=[len(counter.token_ids(j['prompt'])) for j in jobs]
    if max(lengths)+config['max_output_tokens']>config['max_context_tokens']:raise RuntimeError('Context overflow')
    batches={}
    for path in Path('artifacts/runs/validation-v7/qwen3/calls').glob('*.json.gz'):
        c=json.loads(gzip.decompress(path.read_bytes()));r=c['response'];key=r['started_utc'],r['batch_size']
        entry=batches.setdefault(key,{'stages':set(),'seconds':r['batch_wall_seconds'],'tokens':[]})
        entry['stages'].add(c['stage']);entry['tokens'].append(r['input_tokens'])
    # Unlike mixed first-stage batches, these contain root calls exclusively.
    sample=[v for (utc,n),v in batches.items() if v['stages']=={'root'} and n>=32]
    if not sample:raise RuntimeError('No measured root-only batch large enough')
    number=(len(jobs)+31)//32
    prior=json.loads(Path('records/preflight/objective-confirmation-v1-58ce4852da8d.json').read_text())
    loading=next(v['planned_load_seconds'] for v in prior['models'] if v['model']=='qwen3')
    mean=number*float(np.mean([v['seconds'] for v in sample]))+loading
    p95=number*float(np.quantile([v['seconds'] for v in sample],.95))+loading
    config['minimum_remaining_seconds_to_start']=int(np.ceil(p95+60))
    if p95+60>config['maximum_gpu_wall_seconds'] or prior['projected_total_seconds_p95']+p95+60>7200:
        raise RuntimeError('Focused diagnostic does not fit protected confirmation planning allowance')
    analysis={'version':'numerical-preservation-analysis-v1','status':'prospective_exploratory',
        'arms':{'A':'ordinary delivery, upstream single','B':'ordinary delivery, upstream exact',
                'C':'objective-repaired delivery, upstream single','D':'objective-repaired delivery, upstream exact'},
        'primary_outcome':'Exact world decision correctness; malformed completed outputs remain errors.',
        'contrasts':{'ordinary_repetition':{'B':1,'A':-1},'preserved_repetition':{'D':1,'C':-1},
                     'repair_without_repetition':{'C':1,'A':-1},'repair_with_repetition':{'D':1,'B':-1},
                     'repetition_by_preservation':{'D':1,'C':-1,'B':-1,'A':1}},
        'primary_contrast':'repetition_by_preservation',
        'estimator':'Equal base means of paired worlds. Whole-base unstratified 10000-draw percentile intervals, seed 20271017, descriptive only with six bases. Report all and prespecified source-loss/intact strata; six family/change cells cannot support stratified uncertainty.',
        'sampling':'Same six IDs as already frozen root diagnostic; no new outcome selection. Source-loss stratum means at least one ordinary/no-repetition world has an unpreserved objective; others intact. Do not choose by root decisions.',
        'stopping':'All 48 root calls once or cumulative/time cap. No sample extension; partial run stays incomplete. No automatic retry of completed wrong/malformed outputs.',
        'interpretation':config['interpretation'],
        'secondary':'World accuracy separate from strict visible sufficiency and agreement; feasibility and suboptimality; both-world success; costs, field edits, base effects, corrections/regressions. Token/position changes introduced by repair are recorded, not presumed controlled.',
        'fresh_confirmation_limit':'Existing 24-pair confirmation tests objective repetition but does not cross objective-only repair. It cannot confirm this diagnostic interaction.'}
    source={p.name:p.read_text() for p in Path('src/rep_sensitivity').glob('*.py')}
    record={'utc':utcnow(),'source_sha256':digest(source),'config_sha256':digest(config),'analysis_sha256':digest(analysis),
        'pair_ids':[p['pair_id'] for p in pairs],'pair_indices':config['pair_indices'],'base_pairs':len(pairs),'new_root_calls':len(jobs),
        'historical_manager_calls':len({h for j in jobs for h in j['source_manager_request_hashes']}),
        'input_inventory_sha256':digest(inventory),'native_prompt_token_range':[min(lengths),max(lengths)],
        'model_revision':json.loads(Path('records/models/qwen3.json').read_text())['revision'],
        'measured_reference_pure_root_batches':len(sample),'reference_batch_size':32,'planned_batches':[32,len(jobs)-32],
        'reference_prompt_token_range':[min(t for v in sample for t in v['tokens']),max(t for v in sample for t in v['tokens'])],
        'projected_seconds_mean_including_load':mean,'projected_seconds_p95_including_load':p95,
        'protected_confirmation_p95_seconds':prior['projected_total_seconds_p95'],
        'planned_total_seconds_p95_with_buffer':prior['projected_total_seconds_p95']+p95+60,
        'actual_new_gpu_seconds':0,'cap_is_cumulative':True,
        'source_loss_base_pairs':[p['pair_id'] for p in pairs if any(j['source_objective_loss'] for j in jobs if j['pair']==p and j['trial']['arm']=='A')],
        'arm_token_lengths':{a:[lengths[i] for i,j in enumerate(jobs) if j['trial']['arm']==a] for a in 'ABCD'},
        'per_context_edits':[{k:j[k] for k in ('trial','repair_edits','source_objective_loss')} for j in jobs],
        'timing_limit':'Projection uses measured 32-request root-only batch time even for final 16 calls. Loading allowance from prior run. New source prompts are longer; timing is uncertain and the hard shared cap controls actual allocation.'}
    immutable_json(Path('configs/frozen/numerical-preservation-v1.json'),config)
    immutable_json(Path('configs/frozen/numerical-preservation-analysis-v1.json'),analysis)
    immutable_json(Path('records/freezes/numerical-preservation-v1.json'),record)
    immutable_json(Path('artifacts/designs/numerical-preservation-v1/input-inventory.json'),inventory)
    print(json.dumps({k:v for k,v in record.items() if k not in ('arm_token_lengths','per_context_edits')}))


if __name__=='__main__':main()
