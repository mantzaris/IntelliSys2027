"""Native-token CPU check and measured planning bound; never loads a GPU model."""
import gzip
import json
from pathlib import Path
from collections import Counter
import numpy as np
from transformers import AutoTokenizer
from rep_sensitivity.models import LocalModel
from rep_sensitivity.root_diagnostic import plan, materialize_prompt
from rep_sensitivity.schema import digest
from rep_sensitivity.storage import immutable_json, utcnow

config = json.loads(Path('configs/root-diagnostic-v1.json').read_text())
pairs, jobs, excluded = plan(config, config['source_run'])
counter = object.__new__(LocalModel); counter.alias = config['model']
counter.tokenizer = AutoTokenizer.from_pretrained(Path('artifacts/models/qwen3_path.txt').read_text().strip(), trust_remote_code=False)
lengths = []; residuals = []; target_counts = Counter(); correctness = Counter(); inputs = []
for job in jobs:
    prompt = materialize_prompt(job, counter.token_ids); lengths.append(job['input_token_count'])
    if job['padding_reference'] is not None: residuals.append(job['padding_token_residual'])
    inputs.append({'trial': job['trial'], 'prompt_sha256': digest(prompt), 'tokens': job['input_token_count'],
        'fixed_incoming_sha256': job['incoming_sha256'], 'historical_manager_request_hashes': job['historical_manager_request_hashes']})
    if job['trial']['organization'] == 'lossless' and job['trial']['arm'].startswith('objective'):
        from rep_sensitivity.generation import oracle
        truth = oracle(job['world'])
        claim = next(r.claim for r in job['reports'] if r.claim.key in job['selected_keys'])
        target_counts['correct_choice' if claim.candidate_identifier == truth['answer'] else 'other_candidate'] += 1
        target_counts['feasible' if truth['candidates'][claim.candidate_identifier]['feasible'] else 'infeasible'] += 1
        target_counts[claim.candidate_identifier] += 1
timings = []
for p in (Path('artifacts/runs/validation-v7/qwen3/calls')).glob('*.json.gz'):
    with gzip.open(p, 'rt') as f: call = json.load(f)
    if call['stage'] == 'root': timings.append(call['response']['allocated_inference_seconds'])
projection = float(np.quantile(timings, .95))*len(jobs)/3600
if max(lengths)+config['max_output_tokens'] > config['max_context_tokens']: raise RuntimeError('Context overflow')
if projection > config['maximum_additional_inference_hours']: raise RuntimeError('Measured planning bound exceeds one hour')
source = digest({p.name: p.read_text() for p in Path('src/rep_sensitivity').glob('*.py')})
record = {'utc': utcnow(), 'config_sha256': digest(config), 'source_sha256': source,
    'base_pairs': len(pairs), 'trajectories': len(jobs), 'calls': len(jobs), 'exclusions': excluded,
    'prompt_tokens_min_max': [min(lengths), max(lengths)], 'neutral_residual_min_max': [min(residuals), max(residuals)],
    'objective_target_inventory': dict(target_counts), 'input_inventory_sha256': digest(inputs),
    'validation_root_calls_measured': len(timings), 'validation_root_mean_allocated_seconds': float(np.mean(timings)),
    'validation_root_p95_allocated_seconds': float(np.quantile(timings, .95)),
    'projected_allocated_hours_using_mean': float(np.mean(timings))*len(jobs)/3600,
    'projected_allocated_hours_using_p95': projection,
    'caution': 'Projection from measured validation batch-wall allocations; different prompt lengths/batching can change runtime. Excludes model reload and I/O; not measured diagnostic runtime or GPU kernel time.',
    'gpu_inference_calls': 0}
path = Path('records/preflight')/('root-diagnostic-v1-'+digest([config, source])[:12]+'.json')
immutable_json(path, record)
immutable_json(Path('artifacts/designs/root-diagnostic-v1')/(digest(inputs)+'.json'), inputs)
print(json.dumps({'record': str(path), **record}))
