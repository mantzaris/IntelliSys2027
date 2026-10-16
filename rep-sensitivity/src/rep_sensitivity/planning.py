"""Measured resource projections and descriptive precision, never a power claim."""
from collections import defaultdict
import json
import math
from pathlib import Path
import statistics
from .analysis import load_complete,repetition_values,policy_difference,average
from .schema import digest


def prospective_precision(values,strata,total_primary_clusters,difference=False):
    groups=defaultdict(list)
    for pid,value in values.items():groups[strata[pid]].append(value)
    if not groups:return {'available':False,'reason':'Contrast absent from measured protocol'}
    if any(len(vals)<2 for vals in groups.values()):
        return {'available':False,'reason':'Fewer than two measured clusters in a stratum'}
    # H4 uses consequential clusters only; other contrasts use both classes.
    consequence_classes={s[-1] for s in groups}
    expected_strata=3*len(consequence_classes)
    if len(groups)!=expected_strata:
        return {'available':False,'reason':'Incomplete mutation-family/consequence coverage'}
    per_stratum=total_primary_clusters/6
    variances={s:statistics.variance(vals) for s,vals in groups.items()}
    if difference:
        if consequence_classes!={False,True}:
            return {'available':False,'reason':'Both change classes required for difference-in-differences'}
        weights={s:(1/3 if s[-1] else -1/3) for s in groups}
    else:weights={s:1/len(groups) for s in groups}
    variance=sum(weights[s]**2*variances[s]/per_stratum for s in groups)
    degenerate=all(v==0 for v in variances.values())
    return {'available':True,'measured_clusters':len(values),'target_primary_clusters':total_primary_clusters,
            'target_clusters_used':per_stratum*len(groups),'standard_error_approximation':math.sqrt(variance),
            'normal_95_percent_halfwidth_approximation':1.96*math.sqrt(variance),
            'empirical_zero_variance':degenerate,
            'precision_identified':not degenerate,
            'caution':'Small development/validation strata can substantially underestimate variability; zero observed variation does not establish precision.'}


def project(source,target_config):
    manifest,rows,incomplete=load_complete(source)
    targets={}
    for alias in target_config['models']:
        observed=[r for r in rows if r['model']==alias]
        cells=defaultdict(list)
        for r in observed:cells[(r['kind'],r['organization'],r['policy'],r['condition'])].append(r)
        forecasts=[];missing=[]
        for kind in ('schedule','workflow'):
            for org in target_config['organizations']:
                for policy in target_config['policies']:
                    for condition in target_config['repetition_conditions']:
                        key=(kind,org,policy,condition)
                        sample=cells.get(key,[])
                        if not sample:missing.append(key);continue
                        n=(target_config['base_pairs']//2)*len(target_config['worlds'])*target_config['stochastic_repetitions']
                        forecasts.append({'kind':kind,'organization':org,'policy':policy,'condition':condition,
                            'measured_trajectories':len(sample),'projected_trajectories':n,
                            'mean_measured_input_tokens':average(r['input_tokens'] for r in sample),
                            'mean_measured_output_tokens':average(r['output_tokens'] for r in sample),
                            'mean_measured_allocated_seconds':average(r['inference_seconds_allocated'] for r in sample),
                            'projected_allocated_seconds':n*average(r['inference_seconds_allocated'] for r in sample)})
        primary=[r for r in observed if r['kind']=='schedule']
        strata={r['pair_id']:(r['family'],r['decision_changed']) for r in primary}
        contrasts={'H1_exact':repetition_values(primary,'exact'),'H1_paraphrase':repetition_values(primary,'paraphrase'),
                   'H2':repetition_values(primary,pair_failure=True),'H3':repetition_values(primary,interaction=True),
                   'H4_error':policy_difference(primary,lambda r:1-int(r['correct']),lambda r:r['decision_changed'] and r['condition']!='single'),
                   'H4_retention':policy_difference(primary,
                       lambda r:r['changed_scope_retained']/r['changed_scope_denominator'] if r['changed_scope_retained'] is not None and r['changed_scope_denominator'] else None,
                       lambda r:r['decision_changed'] and r['organization']=='hierarchical')}
        targets[alias]={'resource_cells':forecasts,'unmeasured_cells':missing,
                        'projected_inference_hours':sum(c['projected_allocated_seconds'] for c in forecasts)/3600 if not missing else None,
                        'precision':{name:prospective_precision(vals,strata,target_config['base_pairs']//2,name=='H2')
                                     for name,vals in contrasts.items()}}
    all_models_measured=all(v['projected_inference_hours'] is not None for v in targets.values())
    return {'source_suite':manifest['config']['name'],'source_manifest_sha256':digest(manifest),
            'source_complete':len(rows)==manifest['trajectories'] and not incomplete,
            'source_rows':len(rows),'target_config_sha256':digest(target_config),'target_base_pairs':target_config['base_pairs'],
            'target_primary_clusters':target_config['base_pairs']//2,'models':targets,
            'projected_total_inference_hours':sum(v['projected_inference_hours'] for v in targets.values()) if all_models_measured else None,
            'assumptions':['Same batching and inference settings; extrapolation is not measured main-run time.',
                           'Reserved templates/structures may change lengths and latency.',
                           'Excludes model loading, checkpoint I/O, supporting controls, live workers and retries.',
                           'Never substitute an unmeasured model or policy with an assumed token rate.'],
            'interpretation':'Prospective resource and precision approximations, not achieved precision or statistical power.'}


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('target');p.add_argument('output');a=p.parse_args()
    result=project(a.source,json.loads(Path(a.target).read_text()))
    destination=Path(a.output);destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('source_suite','source_complete','target_base_pairs','projected_total_inference_hours')}))
