"""Frozen model-specific analysis; incomplete clusters/models never confirmed."""
from collections import defaultdict
from pathlib import Path
import gzip,json
from rep_sensitivity.analysis import average,bootstrap
from rep_sensitivity.generation import oracle
from rep_sensitivity.pilot_interpretation import paired_effect,paired_world_rows,write_csv
from rep_sensitivity.targeted_analysis import cluster_values,clustered_interval
from rep_sensitivity.schema import digest


def two_arm(rows,after,before,metric='correct'):
    translated=[{**r,'condition':'single' if r['arm']==before else 'repeated'} for r in rows if r['arm'] in (before,after)]
    return paired_effect(translated,'repeated',metric)


def analyze(directory='artifacts/runs/objective-confirmation-v1',output='results/objective-confirmation-v1'):
    directory=Path(directory);output=Path(output);output.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((directory/'manifest.json').read_text());config=manifest['config']
    analysis=json.loads(Path(config['analysis']).read_text())
    pairs={p['pair_id']:p for p in json.loads((directory/'pairs.json').read_text())}
    results=[];incomplete=[]
    for model in config['models']:
        rows=[r for p in sorted((directory/model/'scores').glob('*.json')) for r in json.loads(p.read_text())]
        if len(rows)!=manifest['per_model_trajectories'][model] or {r['pair_id'] for r in rows}!=set(config['pair_ids']):
            incomplete.append({'model':model,'scored_trajectories':len(rows),'complete_pairs':len({r['pair_id'] for r in rows})});continue
        if len({r['trial_id'] for r in rows})!=len(rows):raise ValueError('Duplicate completed trajectory')
        for r in rows:
            truth=oracle(pairs[r['pair_id']]['worlds'][r['world']]);choice=truth['candidates'].get(r['choice'])
            r['feasible_suboptimal']=bool(choice and choice['feasible'] and choice['objective']>truth['candidates'][truth['answer']]['objective'])
            r['objective_retention']=r['objectives_retained']/r['objective_denominator']
        strata={r['pair_id']:(r['family'],r['decision_changed']) for r in rows}
        calls={}
        for p in sorted((directory/model/'calls').glob('*.json.gz')):
            call=json.loads(gzip.decompress(p.read_bytes()))
            if digest({k:call[k] for k in ('prompt','settings','trial','stage')})!=call['request_hash']:raise ValueError('Accepted request hash changed')
            calls[call['request_hash']]=call
        referenced={h for r in rows for h in r['request_hashes']}
        if referenced!=set(calls):raise ValueError('Missing or unscored accepted calls: wait for complete mirror/audit')
        metrics=('correct','invalid_selection','feasible_suboptimal','necessary_retention','critical_retention','objective_retention',
                 'selected_retained','scope_transfer_count','incompatible_scope_merge_count','operational_failure','brier','log_loss')
        absolute=[]
        for arm in sorted({r['arm'] for r in rows}):
            rs=[r for r in rows if r['arm']==arm];refs={h for r in rs for h in r['request_hashes']}
            absolute.append({'model':model,'kind':'schedule','policy':'ordinary','organization':'hierarchical','arm':arm,
                'base_pairs':len(pairs),'trajectories':len(rs),'logical_calls':sum(r['calls'] for r in rs),'physical_calls_touched':len(refs),
                'correct_count':sum(r['correct'] for r in rs),
                'metrics':{m:{'mean':average(r[m] for r in rs if r.get(m) is not None),'denominator':sum(r.get(m) is not None for r in rs)} for m in metrics},
                **{k:sum(r[k] for r in rs) for k in ('input_tokens','output_tokens','inference_seconds_allocated')},
                'allocated_seconds_per_correct':sum(r['inference_seconds_allocated'] for r in rs)/sum(r['correct'] for r in rs) if any(r['correct'] for r in rs) else None})
        contrasts=[]
        terms={**analysis['primary_contrasts'],**analysis['secondary_contrasts']}
        for name,weights in terms.items():
            values,cells=cluster_values(rows,weights,'correct')
            entry={'contrast':name,'primary':name in analysis['primary_contrasts'],'metric':'correct',
                'model':model,'kind':'schedule','policy':'ordinary','organization':'hierarchical',
                'terms':weights,'component_accuracies':{a:next(x for x in absolute if x['arm']==a)['metrics']['correct']['mean'] for a in weights},
                'matched_contexts':cells,'trajectories':cells*len(weights),
                **clustered_interval(values,strata),'base_effects':values,
                'leave_one_base_out':{p:average(v for q,v in values.items() if q!=p) for p in values}}
            if len(weights)==2:
                after=next(a for a,v in weights.items() if v==1);before=next(a for a,v in weights.items() if v==-1)
                entry.update(two_arm(rows,after,before))
            else:entry['corrections_regressions']='Not a binary paired contrast; component two-arm comparisons reported separately'
            contrasts.append(entry)
        paired=[]
        transformed=[{**r,'condition':r['arm']} for r in rows]
        pair_rows=paired_world_rows(transformed)
        for changed in (False,True):
            selected=[r for r in pair_rows if r['decision_changed']==changed]
            for arm in ('selective_exact','selective_paraphrase','balanced_exact','balanced_paraphrase'):
                x=two_arm(selected,arm,'single')
                paired.append({'model':model,'kind':'schedule','policy':'ordinary','decision_changed':changed,'contrast':arm+' - single',
                    'metric':'both worlds correct',**x,'trajectories':2*x['trajectories']})
        pair_interactions=[]
        for arm in ('selective_exact','selective_paraphrase','balanced_exact','balanced_paraphrase'):
            x=two_arm(pair_rows,arm,'single');values=x['base_effects']
            pair_interactions.append({'contrast':arm+' - single; consequential minus harmless pair-success effect',
                **bootstrap(values,strata,difference=True),'base_effects':values})
        accepted=[c['response'] for c in calls.values()]
        result={'complete':True,'status':'prespecified_fresh_confirmation','model':model,'independent_base_pairs':len(pairs),
            'trajectories':len(rows),'physical_calls':len(calls),'logical_calls':sum(r['calls'] for r in rows),
            'source_manifest_sha256':digest(manifest),'source_scores_sha256':digest(rows),'analysis_manifest_sha256':digest(analysis),
            'analysis_source_sha256':digest(Path(__file__).read_text()),'source_implementation_sha256':digest(json.loads((directory/'implementation.json').read_text())),
            'absolute':absolute,'contrasts':contrasts,'paired_world':paired,'consequential_minus_harmless':pair_interactions,
            'physical_resources':{k:sum(r[k] for r in accepted) for k in ('input_tokens','output_tokens','allocated_inference_seconds')},
            'physical_resources_note':'Each accepted call counted once; arm-level logical costs include shared manager calls. These are measured batch-wall allocations, not GPU kernel time or money.',
            'limits':analysis['limitations'],'missingness':analysis['missingness']}
        destination=output/model;destination.mkdir(exist_ok=True);(destination/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
        write_csv(destination/'contrasts.csv',[{k:v for k,v in row.items() if not isinstance(v,dict)} for row in contrasts])
        results.append(result)
    result={'complete':not incomplete,'status':'complete' if not incomplete else 'incomplete_prespecified_design',
        'model_results':results,'incomplete_models':incomplete,'independent_base_pairs':manifest['base_pairs'],
        'source_manifest_sha256':digest(manifest),'analysis_source_sha256':digest(Path(__file__).read_text())}
    (output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n');return result

if __name__=='__main__':
    r=analyze();print(json.dumps({'complete':r['complete'],'complete_models':[m['model'] for m in r['model_results']],'incomplete_models':r['incomplete_models']}))
