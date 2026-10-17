"""CPU/native-token preflight; freeze before any new responses exist."""
import argparse
from pathlib import Path
import gzip
import json
import numpy as np
from transformers import AutoTokenizer
from rep_sensitivity.adjacent_explorations import build_cases, inventory, feedback_prompt, consensus_prompt, length_control
from rep_sensitivity.models import LocalModel
from rep_sensitivity.schema import digest
from rep_sensitivity.storage import immutable_json, utcnow


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--freeze',action='store_true');a=parser.parse_args()
    config=json.loads(Path('configs/adjacent-explorations-v1.json').read_text());config['status']='frozen'
    cases=build_cases(config);inputs=inventory(config,cases);config['input_inventory_sha256']=digest(inputs)
    model=object.__new__(LocalModel);model.alias=config['model']
    model.tokenizer=AutoTokenizer.from_pretrained(Path('artifacts/models/qwen3_path.txt').read_text().strip(),trust_remote_code=False)
    metadata=json.loads(Path('records/models/qwen3.json').read_text())
    config.update(model_revision=metadata['revision'],tokenizer_revision=metadata['revision'],
                  chat_template_sha256=digest(model.tokenizer.chat_template),chat_template_date='2026-10-16',
                  reasoning_mode='disabled',precision='bfloat16',quantization=None)
    lengths=[];padding=[];identity_lengths=[]
    for c in cases:
        # Maximum ordinary public feedback: all three required assessments.
        # This fixture is CPU-only; no task answer is inserted into a model call.
        example={'previous_round':2,'evidence_version':'1','parse_status':'valid','choice':c['worlds']['initial']['tie_order'][0],
            'candidate_assessments':[{'candidate':cid,'all_mandatory_pass':False,'objective':999} for cid in c['worlds']['initial']['tie_order']]}
        for u in ('consequential','harmless'):
            for r in (1,2,3):
                for context in (None,example if r>1 else None):
                    lengths.append(len(model.token_ids(feedback_prompt(c,u,r,context))))
                if r>1:
                    p,residual=length_control(c,u,r,example,model.token_ids);lengths.append(len(model.token_ids(p)));padding.append(residual)
        for w in (0,1):
            row={'pair_id':c['pair_id'],'world':w}
            for arm in config['consensus_arms']:
                n=len(model.token_ids(consensus_prompt(c,w,arm)[0]));lengths.append(n);row[arm]=n
            identity_lengths.append(row)
    if max(lengths)+config['max_output_tokens']>config['max_context_tokens']:
        raise ValueError('Context overflow; no truncation is permitted')
    batches={}
    for p in Path('artifacts/runs/validation-v7/qwen3/calls').glob('*.json.gz'):
        c=json.loads(gzip.decompress(p.read_bytes()));r=c['response'];key=r['started_utc'],r['batch_size']
        v=batches.setdefault(key,{'stages':set(),'seconds':r['batch_wall_seconds'],'tokens':[]})
        v['stages'].add(c['stage']);v['tokens'].append(r['input_tokens'])
    sample=[v for (_,n),v in batches.items() if n==32 and v['stages']=={'root'}]
    prior=json.loads(Path('records/preflight/objective-confirmation-v1-58ce4852da8d.json').read_text())
    load=next(v['planned_load_seconds'] for v in prior['models'] if v['model']=='qwen3')
    preservation=json.loads(Path('records/freezes/numerical-preservation-v1.json').read_text())
    # New full-report prompts may exceed historical summary-only prompts. Use
    # their maximum token ratio (at least 1.2), not a hypothetical token rate.
    reference_max=max(t for v in sample for t in v['tokens'])
    multiplier=max(1.2,max(lengths)/reference_max)
    batch_p95=float(np.quantile([v['seconds'] for v in sample],.95))*multiplier
    batch_mean=float(np.mean([v['seconds'] for v in sample]))*multiplier
    projection={mode:{'calls':calls,'batches':sizes,'mean_seconds_with_loading':len(sizes)*batch_mean+load,
                      'planning_p95_seconds_with_loading':len(sizes)*batch_p95+load}
                for mode,calls,sizes in [('both',104,[24,24,24,32]),('feedback_only',72,[24,24,24])]}
    protected=prior['projected_total_seconds_p95']+preservation['projected_seconds_p95_including_load']
    for mode,p in projection.items():
        p['minimum_remaining_seconds']=int(np.ceil(p['planning_p95_seconds_with_loading']+60))
        p['prospectively_feasible']=p['minimum_remaining_seconds']<=900 and protected+p['minimum_remaining_seconds']+60<=7200
    if not projection['feedback_only']['prospectively_feasible']:
        raise ValueError('Neither design fits protected planning allowance; do not freeze a runnable design')
    config['allocation_rule']={'priority':['both','feedback_only'],'projections':projection,
        'margin_seconds':60,'selection':'Before any new calls, use actual remaining shared allowance. Require all protected completions. Choose first feasible mode; otherwise do not launch. Never choose by responses.'}
    analysis={'version':'adjacent-analysis-v1','status':'prospective_exploratory','independent_unit':'original development base pair',
        'model_averaging':'one model only','source_count_metric':'not identified by the existing public output contract; no belief inference from answer flips',
        'feedback_primary':['round-3 accuracy: feedback minus fresh','round-3 accuracy: feedback minus length_control'],
        'consensus_primary':['different_relays minus same_worker','authority_labels minus different_relays'],
        'secondary':['per-round accuracy','correct-to-wrong and wrong-to-correct transitions','both round 2 and round 3 correct by update type',
                     'initially wrong choice persisting while still wrong at round 2 or 3, conditional denominator explicit',
                     'selection of repeated candidate','feasibility errors','response contract failures','full-scope emitted fidelity','tokens and allocated batch time'],
        'malformed':'Completed malformed/truncated outputs are errors, retained without resampling; no valid-decision transition inferred from missing choices.',
        'intervals':'All four case effects and leave-one-base-out means. Optional exact four-base cluster bootstrap, descriptive only; no confirmatory p-values.',
        'trace_selection':'All cases and choices; full representative raw traces from the smallest lexical base ID in each edit family, chosen before responses.',
        'interpretation':'Prior public conclusions differ from repeated task facts. No hierarchy causal claim, internal-belief claim, or independent-observation claim.'}
    source={p.name:p.read_text() for p in Path('src/rep_sensitivity').glob('*.py')}
    record={'utc':utcnow(),'base_pairs':4,'pair_ids':[c['pair_id'] for c in cases],'source_sha256':digest(source),
        'config_sha256':digest(config),'analysis_sha256':digest(analysis),'input_inventory_sha256':digest(inputs),
        'model_revision':metadata['revision'],'model_metadata_sha256':digest(metadata),
        'scripts_sha256':{name:digest(Path('scripts',name).read_text()) for name in
            ('prepare_adjacent_explorations.py','run_adjacent_explorations.py','analyze_adjacent_explorations.py','build_adjacent_supplement.py')},
        'native_prompt_token_range': [min(lengths),max(lengths)],'feedback_padding_residual_range':[min(padding),max(padding)],
        'identity_token_lengths':identity_lengths,'measured_reference_root_batches':len(sample),'reference_batch_size':32,
        'reference_prompt_max_tokens':reference_max,'prompt_length_timing_multiplier':multiplier,
        'projection':projection,'protected_planning_seconds':protected,'shared_cap_seconds':7200,'additional_seconds_consumed':0,
        'trace_bases':sorted(min(c['pair_id'] for c in cases if c['family']==f) for f in ('numeric','identity')),
        'source_pair_ids_reused_not_independent_confirmation':True,
        'limitation':'Historical batch timings scaled conservatively for prompt length; not a measured future runtime or formal prediction interval. Actual generated feedback lengths logged; no input truncation.',
        'case_inventory':[{'pair_id':c['pair_id'],'index':c['index'],'family':c['family'],'reverse':c['reverse'],
            'answers':{k:v['answer'] for k,v in c['truth'].items()},'target_candidate':c['target_candidate'],'edits':c['edits']} for c in cases]}
    if a.freeze:
        if list(Path('artifacts/runs/adjacent-explorations-v1').glob('*/calls/*')):raise ValueError('Cannot freeze after responses')
        immutable_json(Path('configs/frozen/adjacent-explorations-v1.json'),config)
        immutable_json(Path('configs/frozen/adjacent-analysis-v1.json'),analysis)
        immutable_json(Path('records/freezes/adjacent-explorations-v1.json'),record)
        immutable_json(Path('artifacts/designs/adjacent-explorations-v1/inputs.json'),inputs)
    else:
        Path('records/preflight/adjacent-explorations-v1.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({k:v for k,v in record.items() if k not in ('identity_token_lengths','case_inventory')},indent=2))


if __name__=='__main__':main()
