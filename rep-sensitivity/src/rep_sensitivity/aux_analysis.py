"""Offline, cluster-paired analysis of supporting controls and live assignments."""
from collections import defaultdict
import csv
import gzip
import json
from pathlib import Path
from .analysis import average,bootstrap
from .schema import digest
from .metrics import parse

OPTIONAL_METRICS=('unique_clause_retained','false_assertion_adopted','false_assertion_emitted','superseded_assertions_emitted',
                 'choice_matches_superseded_when_distinct','superseded_choice_with_historical_assertion',
                 'epistemically_appropriate_choice','root_supported_correct','unsupported_truth_hit',
                 'delivered_claims','required_claims','root_resource_displacement','worker_incorrect_claims',
                 'worker_unknown_scope_assertions','worker_unsupported_source_assertions')

COMPARISONS={
    'packaging':[('high_overlap','low_overlap')],
    'deduplication':[('similarity_removal','exact_removal'),('scope_consolidation','similarity_removal')],
    'branch_placement':[('different_branch','same_branch')],
    'copy_branch_placement':[('different_branch','same_branch')],
    'access':[('summaries_and_reports','summaries_only')],
    'call_count':[('global_reviewers','partition_managers')],
    'length':[('evidential_repetition','neutral_padding')],
    'ancestry':[('withheld','authentic'),('corrupted_relationships','authentic')],
    'instruction':[('scope_without_ancestry','ordinary_without_ancestry')],
    'corruption':[(policy+'_'+case,policy+'_all_correct_with_world')
                  for policy in ('ordinary','checklist','scope')
                  for case in ('false_favorable_with_world','false_objection_with_world')]+
                 [('scope_'+case,'checklist_'+case) for case in ('all_correct_with_world','false_favorable_with_world','false_objection_with_world')],
    'unique_clause':[('decisive_high','decisive_low'),('harmless_high','harmless_low')],
    'version_admission':[('current_and_superseded','current_only')],
    'dose':[('two','one'),('four','one'),('eight','one')],
    'live':[(a,'nonoverlap_added') for a in ('exact_overlap_fixed','near_overlap_fixed','exact_overlap_added','near_overlap_added')]
}


def summarize(directory,output,replicates=10000):
    directory,output=Path(directory),Path(output);output.mkdir(parents=True,exist_ok=True)
    config=json.loads((directory/'config.json').read_text())
    live=(directory/'pairs.json').exists()
    pair_meta={p['pair_id']:p['evaluation'] for p in json.loads((directory/'pairs.json').read_text())} if live else {}
    accepted=[];excluded=[]
    for model_dir in sorted(p for p in directory.iterdir() if p.is_dir() and (p/'scores').exists()):
        rows=[json.loads(p.read_text()) for p in sorted((model_dir/'scores').glob('*.json'))]
        by_pair=defaultdict(list)
        for r in rows:by_pair[r['pair_id']].append(r)
        if live:
            expected={pid:len(config['worlds'])*5*config['stochastic_repetitions'] for pid in pair_meta}
        else:
            expected={p.stem:json.loads(p.read_text())['trajectories'] for p in (model_dir/'manifests').glob('*.json')}
        for pid,n in expected.items():
            rs=by_pair.get(pid,[])
            if len(rs)!=n or len({r['trial_id'] for r in rs})!=n:
                excluded.append({'model':model_dir.name,'pair':pid,'expected':n,'found':len(rs)});continue
            for r in rs:
                if live:
                    meta=pair_meta[pid]
                    r.update(contrast='live',arm=r['allocation']+'_'+r['allowance'],kind=meta['kind'],family=meta['family'],decision_changed=meta['decision_changed'])
                    r['root_resource_displacement']=r['root_not_executed'] is not None
                if r.get('contrast')=='corruption' and 'injected_scope' in r.get('audit',{}):
                    calls=[json.loads(gzip.decompress((model_dir/'calls'/(key+'.json.gz')).read_bytes())) for key in r['request_hashes']]
                    response=next(c['response'] for c in calls if c['stage']=='root')
                    obj,status=parse(response['text'],[r['choice']] if r['choice'] is not None else [])
                    if response['finish_reason']=='length':obj=None
                    r.update(false_finding_metrics(obj,r['audit']['injected_scope'],r['audit']['true_value']))
                accepted.append(r)
    groups=defaultdict(list)
    for r in accepted:groups[(r['kind'],r['model'],r['contrast'],r['arm'])].append(r)
    summary=[]
    for (kind,model,contrast,arm),rs in sorted(groups.items()):
        correct=sum(r['correct'] for r in rs)
        row={'kind':kind,'model':model,'contrast':contrast,'arm':arm,'n':len(rs),
             'clusters':len({r['pair_id'] for r in rs}),'correct':correct,'accuracy':correct/len(rs),
             'operational_failure_rate':average(r['operational_failure'] for r in rs),
             'input_tokens':sum(r['input_tokens'] for r in rs),'output_tokens':sum(r['output_tokens'] for r in rs),
             'inference_seconds_allocated':sum(r['inference_seconds_allocated'] for r in rs),
             'calls_per_decision':sum(len(r['request_hashes']) for r in rs)/len(rs),
             'tokens_per_correct':sum(r['input_tokens']+r['output_tokens'] for r in rs)/correct if correct else None}
        for key in OPTIONAL_METRICS:
            available=[r[key] for r in rs if key in r and r[key] is not None]
            row[key+'_denominator']=len(available);row[key+'_mean']=average(available)
        summary.append(row)
    contrasts=[];metric_contrasts=[]
    for kind,model,contrast in sorted({(r['kind'],r['model'],r['contrast']) for r in accepted}):
        rs=[r for r in accepted if (r['kind'],r['model'],r['contrast'])==(kind,model,contrast)]
        for a,b in COMPARISONS[contrast]:
            cells=defaultdict(dict)
            for r in rs:cells[(r['pair_id'],r['world'],r['repetition'])][r['arm']]=1-int(r['correct'])
            paired=defaultdict(list)
            for (pid,wi,rep),arms in cells.items():
                if a in arms and b in arms:paired[pid].append(arms[a]-arms[b])
            values={pid:average(v) for pid,v in paired.items()}
            strata={r['pair_id']:tuple(r[field] for field in config.get('bootstrap_strata',['family','decision_changed'])) for r in rs}
            contrasts.append({'kind':kind,'model':model,'contrast':contrast,'difference':a+' - '+b,
                              **bootstrap(values,strata,replicates=replicates)})
            for metric in OPTIONAL_METRICS:
                observed=defaultdict(dict)
                for r in rs:
                    if r.get(metric) is not None:
                        observed[(r['pair_id'],r['world'],r['repetition'])][r['arm']]=r[metric]
                paired_metric=defaultdict(list)
                for (pid,wi,rep),arms in observed.items():
                    if a in arms and b in arms:paired_metric[pid].append(float(arms[a])-float(arms[b]))
                if paired_metric:
                    metric_contrasts.append({'kind':kind,'model':model,'contrast':contrast,'metric':metric,
                        'difference':a+' - '+b,'paired_cell_denominator':sum(map(len,paired_metric.values())),
                        **bootstrap({pid:average(v) for pid,v in paired_metric.items()},strata,replicates=replicates)})
        if contrast=='unique_clause':
            for metric in ('decision_error','unique_clause_retained'):
                values,denominator=unique_clause_interaction(rs,metric)
                if values:
                    metric_contrasts.append({'kind':kind,'model':model,'contrast':contrast,'metric':metric,
                        'difference':'(decisive_high - decisive_low) - (harmless_high - harmless_low)',
                        'paired_cell_denominator':denominator,
                        **bootstrap(values,strata,replicates=replicates)})
    for filename,rows in [('summary.csv',summary),('contrasts.csv',contrasts),('metric_contrasts.csv',metric_contrasts)]:
        if rows:
            with (output/filename).open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
    missing=sorted(set(config.get('models',[]))-{r['model'] for r in accepted})
    result={'suite':config['name'],'config_sha256':digest(config),'source_records_sha256':digest(accepted),
            'analyzed_trajectories':len(accepted),'excluded_incomplete_clusters':excluded,
            'missing_models':missing,'complete':bool(accepted) and not excluded and not missing,
            'bootstrap_strata':config.get('bootstrap_strata',['family','decision_changed']),
            'summary':summary,'contrasts':contrasts,'metric_contrasts':metric_contrasts,
            'analysis_source_sha256':digest(Path(__file__).read_text()),
            'false_finding_definition':'Adopted means an explicit false root finding with neither a contrary true assertion nor that scope listed as unresolved. Emission alone is separate; neither metric establishes hidden belief or a causal reasoning path.',
            'interpretation':'Exploratory paired base-cluster estimates; no confirmatory p-values. Optional metric contrasts use only cells observed in both arms; denominators are explicit.'}
    (output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def false_finding_metrics(obj,key,true_value):
    if obj is None:return {'false_assertion_emitted':None,'false_assertion_adopted':None}
    values=[v for k,v,refs in obj['assertions'] if k==key and type(v) is bool]
    emitted=(not true_value) in values
    return {'false_assertion_emitted':emitted,
            'false_assertion_adopted':emitted and true_value not in values and key not in obj['unresolved']}


def unique_clause_interaction(rows,metric):
    """Overlap effect on decisive versus harmless clauses, paired within worlds."""
    cells=defaultdict(dict)
    for r in rows:
        value=1-int(r['correct']) if metric=='decision_error' else r.get(metric)
        if value is not None:cells[(r['pair_id'],r['world'],r['repetition'])][r['arm']]=float(value)
    paired=defaultdict(list)
    for (pid,wi,rep),a in cells.items():
        if all(k in a for k in ('decisive_high','decisive_low','harmless_high','harmless_low')):
            paired[pid].append(a['decisive_high']-a['decisive_low']-a['harmless_high']+a['harmless_low'])
    return {pid:average(v) for pid,v in paired.items()},sum(map(len,paired.values()))


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('directory');p.add_argument('output');p.add_argument('--bootstrap',type=int,default=10000)
    a=p.parse_args();r=summarize(a.directory,a.output,a.bootstrap)
    print(json.dumps({'suite':r['suite'],'analyzed_trajectories':r['analyzed_trajectories'],'excluded_clusters':len(r['excluded_incomplete_clusters'])}))
