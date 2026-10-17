"""Whole-base exploratory estimates and all-case transitions; no interim tuning."""
from collections import defaultdict, Counter
from itertools import product
from pathlib import Path
import gzip
import json
import numpy as np
from .schema import digest
from .storage import utcnow


def mean(values):
    values=list(values)
    return sum(values)/len(values) if values else None


def cluster_estimate(values):
    keys=sorted(values);v=[values[k] for k in keys]
    if not v:
        return {'base_pairs':0,'estimate':None,'lower':None,'upper':None,'base_effects':{}}
    # For four bases, enumerate all 4**4 cluster resamples instead of presenting
    # simulation noise as precision. This still has only FOUR independent units.
    samples=[mean(draw) for draw in product(v,repeat=len(v))]
    return {'base_pairs':len(v),'estimate':mean(v),'lower':float(np.quantile(samples,.025)),
            'upper':float(np.quantile(samples,.975)),'base_effects':values,
            'leave_one_base_out':{k:mean(x for kk,x in values.items() if kk!=k) for k in keys}}


def transitions(sequence):
    rows={r['round']:r for r in sequence};first=rows[1];out={}
    for before,after in ((1,2),(2,3)):
        a,b=rows[before],rows[after];valid=not a['operational_failure'] and not b['operational_failure']
        out[f'{before}_to_{after}']={'both_valid':valid,'correct_to_incorrect':valid and a['correct'] and not b['correct'],
            'incorrect_to_correct':valid and not a['correct'] and b['correct'],
            'correctness_score_regression_including_failures':a['correct'] and not b['correct'],
            'correctness_score_correction_including_failures':not a['correct'] and b['correct'],
            'both_correct':a['correct'] and b['correct'],'both_incorrect':not a['correct'] and not b['correct'],
            'answer_changed':a['choice']!=b['choice'] if valid else None,
            'operational_failure_in_transition':not valid}
    initially_wrong=not first['operational_failure'] and not first['correct']
    out['initially_wrong_valid']=initially_wrong
    for r in (2,3):
        current=rows[r]
        out[f'initial_wrong_followup_valid_round_{r}']=initially_wrong and not current['operational_failure']
        out[f'initial_wrong_choice_persists_and_still_wrong_round_{r}']=(
            current['choice']==first['choice'] and not current['correct']) if initially_wrong and not current['operational_failure'] else None
    valid_update=not rows[2]['operational_failure'] and not rows[3]['operational_failure']
    changed_truth=rows[2]['oracle_choice']!=rows[3]['oracle_choice']
    out['consequential_update']=changed_truth
    out['correct_update_response_or_stability']=rows[2]['correct'] and rows[3]['correct']
    out['retained_obsolete_correct_choice']=(valid_update and changed_truth and rows[2]['correct'] and rows[3]['choice']==rows[2]['choice'])
    return out


def contrast(rows, before, after, cell_fields, label):
    cells=defaultdict(dict)
    for r in rows:cells[tuple(r[f] for f in cell_fields)][r['arm']]=r
    paired=[c for c in cells.values() if before in c and after in c]
    if len(paired)!=len(cells):raise ValueError('Incomplete paired analysis')
    contrasts=[]
    for metric in ('correct','invalid_selection','selected_target','operational_failure','input_tokens','inference_seconds_allocated'):
        base=defaultdict(list)
        for c in paired:
            base[c[before]['pair_id']].append(c[after][metric]-c[before][metric])
        contrasts.append({'contrast':label,'metric':metric,'before':before,'after':after,
            'trajectories_per_arm':len(paired),'calls_both_arms':2*len(paired),
            'before_mean':mean(c[before][metric] for c in paired),'after_mean':mean(c[after][metric] for c in paired),
            'increases':sum(c[after][metric]>c[before][metric] for c in paired),
            'decreases':sum(c[after][metric]<c[before][metric] for c in paired),
            'unchanged':sum(c[after][metric]==c[before][metric] for c in paired),
            **cluster_estimate({k:mean(v) for k,v in base.items()})})
    return contrasts


def analyze(directory='artifacts/runs/adjacent-explorations-v1',output='results/adjacent-explorations-v1'):
    directory=Path(directory);manifest_path=directory/'manifest.json'
    if not manifest_path.exists():return None
    manifest=json.loads(manifest_path.read_text());model=manifest['config']['model'];folder=directory/model
    rows=[r for p in sorted((folder/'scores').glob('*.json')) for r in json.loads(p.read_text())]
    result={'utc':utcnow(),'model':model,'status':'exploratory_reused_development','source_manifest_sha256':digest(manifest),
        'analysis_source_sha256':digest(Path(__file__).read_text()),'base_pairs':manifest['base_pairs'],
        'complete':len(rows)==manifest['calls'],'planned_calls':manifest['calls'],'experiments':{},
        'inference_limit':'Four development base clusters shared by both experiments. Descriptive intervals only; no confirmatory p-values or internal-belief inference.'}
    representatives=[]
    for experiment,expected in [('feedback',72),('consensus',manifest['consensus_calls'])]:
        selected=[r for r in rows if r['experiment']==experiment]
        if expected==0:
            result['experiments'][experiment]={'status':'not_launched_by_frozen_budget_rule','complete':False};continue
        if len(selected)!=expected:
            result['experiments'][experiment]={'status':'pending_or_incomplete','complete':False,'accepted_score_rows':len(selected)};continue
        hashes={h for r in selected for h in r['request_hashes']}
        if len(hashes)!=expected or not all((folder/'calls'/(h+'.json.gz')).exists() for h in hashes):
            raise ValueError('Complete analysis requires unique accepted raw calls')
        groups=defaultdict(list)
        for r in selected:groups[(r['arm'],r['round'] if experiment=='feedback' else 1)].append(r)
        absolute=[]
        for (arm,round_number),rs in sorted(groups.items()):
            fields={k:sum(r['representation'][k] for r in rs) for k in rs[0]['representation']}
            absolute.append({'arm':arm,'round':round_number,'base_pairs':len({r['pair_id'] for r in rs}),'trajectories':len(rs),
                'correct':sum(r['correct'] for r in rs),'accuracy':mean(r['correct'] for r in rs),
                **{k:sum(r[k] for r in rs) for k in ('invalid_selection','feasible_but_suboptimal','operational_failure','selected_target',
                                                   'input_tokens','output_tokens','inference_seconds_allocated')},
                'emitted_field_counts':fields})
        comparisons=[];sequences=[]
        if experiment=='feedback':
            for r in (2,3):
                for update in ('both','consequential','harmless'):
                    subset=[x for x in selected if x['round']==r and (update=='both' or x['world']==update)]
                    for before,after in [('fresh','feedback'),('length_control','feedback'),('fresh','length_control')]:
                        comparisons+=contrast(subset,before,after,('pair_id','world'),f'round_{r}/{update}/{after}_minus_{before}')
            histories=defaultdict(list)
            for r in selected:histories[r['pair_id'],r['world'],r['arm']].append(r)
            for (pid,update,arm),rs in sorted(histories.items()):
                sequences.append({'pair_id':pid,'update':update,'arm':arm,
                    'choices':[r['choice'] for r in sorted(rs,key=lambda x:x['round'])],
                    'correct':[r['correct'] for r in sorted(rs,key=lambda x:x['round'])],
                    'oracle_choices':[r['oracle_choice'] for r in sorted(rs,key=lambda x:x['round'])],**transitions(rs)})
        else:
            for before,after in [('same_worker','different_relays'),('different_relays','authority_labels'),
                                 ('single','same_worker'),('single','different_relays'),('single','authority_labels')]:
                comparisons+=contrast(selected,before,after,('pair_id','world'),f'{after}_minus_{before}')
        trace_bases={min(r['pair_id'] for r in selected if r['family']==f) for f in ('numeric','identity')}
        for r in selected:
            if r['pair_id'] not in trace_bases:continue
            h=r['request_hashes'][0];call=json.loads(gzip.decompress((folder/'calls'/(h+'.json.gz')).read_bytes()))
            representatives.append({'trial':call['trial'],'request_hash':h,'raw_relative_path':str(folder/'calls'/(h+'.json.gz')),
                'prompt_sha256':digest(call['prompt']),'response_sha256':digest(call['response']),
                'choice':r['choice'],'oracle_choice':r['oracle_choice'],'correct':r['correct'],'parse_status':r['parse_status']})
        result['experiments'][experiment]={'status':'complete','complete':True,'base_pairs':4,'calls':len(hashes),
            'absolute':absolute,'contrasts':comparisons,'decision_sequences':sequences,
            'all_case_decisions':[{k:r[k] for k in ('pair_id','family','arm','world','round','choice','oracle_choice','correct',
                'invalid_selection','operational_failure','selected_target','input_tokens','output_tokens','inference_seconds_allocated')} for r in selected],
            'padding_residual_counts':dict(Counter(str(r.get('padding_token_residual')) for r in selected)),
            'accepted_inventory_sha256':digest(sorted(hashes))}
    # Never emit outcome estimates for an incomplete experimental unit.
    out=Path(output);out.mkdir(parents=True,exist_ok=True)
    (out/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    (out/'representative-trace-index.json').write_text(json.dumps(representatives,indent=2)+'\n')
    print(json.dumps({'adjacent_complete':result['complete'],'experiments':{k:v['status'] for k,v in result['experiments'].items()}}))
    return result
