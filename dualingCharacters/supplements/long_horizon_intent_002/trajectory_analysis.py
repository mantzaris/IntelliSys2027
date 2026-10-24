"""Paired descriptive trajectory contrasts from verified dynamic-oracle audit caches."""
from collections import defaultdict
from itertools import product
from pathlib import Path
import numpy as np
from pcc.resources import sha256
from supplements.review_001.common import write_csv
from .common import ROOT,REPORTS,ARTIFACTS,read,write,utc


def correctness(episode):
    horizon=episode['horizon'];result=np.ones(horizon,dtype=bool)
    for spell in episode['failure_spells']:
        start=spell['onset_turn'];end=spell['recovered_turn'] or horizon+1
        if not 1<=start<end<=horizon+1:raise ValueError('Invalid time-indexed failure interval')
        if not result[start-1:end-1].all():raise ValueError('Overlapping failure intervals')
        result[start-1:end-1]=False
    if bool(result[-1])!=episode['final_success'] or bool(result[0])!=episode['initial_success'] or bool(~result.any())!=episode['never_aligned']:raise ValueError('Cached trajectory summary inconsistency')
    return result


def paired_metrics(episodes):
    lookup={(e['family_id'],e['world']):e for e in episodes}
    if len(lookup)!=len(episodes):raise ValueError('Duplicate trajectory episode')
    families=sorted({e['family_id'] for e in episodes})
    if set(lookup)!=set(product(families,('authorized','hypothetical'))):raise ValueError('Incomplete paired trajectories')
    by_family={}
    for family in families:
        curves=np.array([correctness(lookup[family,w]) for w in ('authorized','hypothetical')]);n=curves.shape[-1]
        by_family[family]={'paired_all_turn_success':float(curves.all(0).mean()),'mean_world_all_turn_success':float(curves.mean()),
          'paired_final_quarter_success':float(curves[:,3*n//4:].all(0).mean()),'paired_final_success':float(curves[:,-1].all()),
          'at_least_one_world_never_aligned':float((~curves.any(1)).any()),
          'at_least_one_unresolved_world':float((~curves[:,-1]).any()),
          'trailing_failure_turns_mean':float(np.mean([lookup[family,w]['trailing_failure_turns'] for w in ('authorized','hypothetical')]))}
    return by_family


def family_interval(values):
    values=np.asarray(values,float);rng=np.random.default_rng(720023);idx=rng.integers(0,len(values),(10000,len(values)))
    return np.quantile(values[idx].mean(1),[.025,.975]).tolist()


def main():
    groups={};inputs={};levels=[];contrasts=[]
    for path in sorted((ARTIFACTS/'core_trajectory').glob('*.json')):
        audit=read(path);header=audit['metadata'];k=header['model'],header['condition'],header['seed'];v=paired_metrics(audit['episodes']);groups[k]=v
        inputs[str(path.relative_to(ROOT))]=sha256(path)
        for metric in next(iter(v.values())):
            values=[row[metric] for row in v.values()]
            levels.append({**header,'families':len(v),'metric':metric,'value':float(np.mean(values)),
              'qualification':'Exploratory structured dynamic-oracle trajectory description, not new qualitative intent scoring'})
    for model in ('qwen','phi'):
        for seed in (17,29,43):
            for control in ('C3','C1'):
                a=groups.get((model,'C5',seed));b=groups.get((model,control,seed))
                if a is None or b is None:continue
                if set(a)!=set(b):raise ValueError('Mismatched family dependence')
                for metric in next(iter(a.values())):
                    differences=[a[f][metric]-b[f][metric] for f in sorted(a)]
                    interval=family_interval(differences)
                    contrasts.append({'model':model,'seed':seed,'contrast':'C5-'+control,'families':len(a),'metric':metric,
                      'difference':float(np.mean(differences)),'ci95_low':interval[0],'ci95_high':interval[1],
                      'uncertainty':'Exploratory family-paired bootstrap; worlds and all turns remain inside family. No training-seed inference.',
                      'causal_qualification':'Methods visit different endogenous error states; these are trajectory associations, not matched-state recovery effects.'})
    for name,rows in [('paired_trajectory_levels',levels),('paired_trajectory_contrasts',contrasts)]:
        write(REPORTS/(name+'.json'),rows);write_csv(REPORTS/(name+'.csv'),rows)
    write(REPORTS/'trajectory_analysis_provenance.json',{'generated_utc':utc(),'source_sha256':sha256(Path(__file__)),
      'inputs':inputs,'bootstrap_draws':10000,'bootstrap_seed':720023,'original_raw_data_not_rescanned':True})
    print({'completed_run_trajectories':len(groups),'per_seed_metric_contrasts':len(contrasts),'new_model_calls':0})


if __name__=='__main__':main()
