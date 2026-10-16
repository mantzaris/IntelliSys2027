"""Reproduce and diagnose the old pilot; all new mechanism analyses exploratory."""
from collections import defaultdict,Counter
import csv
import gzip
import json
from pathlib import Path
import math
from rep_sensitivity.analysis import load_complete,bootstrap,average
from rep_sensitivity.reports import thaw,repeat
from rep_sensitivity.mechanism import relevance,transport_metrics,necessary_keys
from rep_sensitivity.metrics import parse
from rep_sensitivity.graphs import partition
from rep_sensitivity.schema import digest,canonical
from rep_sensitivity.targeted_analysis import clustered_interval

SOURCE=Path('artifacts/runs/pilot-v7');OUT=Path('results/pilot-mechanism-v1');OUT.mkdir(parents=True,exist_ok=True)
manifest,rows,incomplete=load_complete(SOURCE)
if incomplete or len(rows)!=manifest['trajectories']:raise RuntimeError('Pilot is incomplete')
pairs={p['pair_id']:p for p in json.loads((SOURCE/'pairs.json').read_text())}
corpus=json.loads((SOURCE/'frozen-reports.json').read_text())
calls={};annotated=[];necessity={}
for row in rows:
    p=pairs[row['pair_id']];world=p['worlds'][row['world']]
    originals=thaw(corpus[p['pair_id']]['reports'][row['world']])
    reports=repeat(originals,corpus[p['pair_id']]['selected'],row['condition'],p['split'])
    selected=next(r for r in originals if canonical([r.claim.task_identifier,r.claim.candidate_identifier,r.claim.entity_identifier])==corpus[p['pair_id']]['selected'])
    parsed={};raw={}
    for key in row['request_hashes']:
        if key not in calls:calls[key]=json.loads(gzip.decompress((SOURCE/row['model']/'calls'/(key+'.json.gz')).read_bytes()))
        c=calls[key];obj,status=parse(c['response']['text'],world['tie_order']+['NONE'],manager=c['stage']!='root')
        if c['response']['finish_reason']=='length':obj=None
        parsed[c['stage']]=obj;raw[c['stage']]=c
    owner=next(i for i,rs in enumerate(partition(reports,p['seed'])) if any(r.identifier==selected.identifier for r in rs))
    rel=relevance(world,originals,selected)
    a={**row,'selected_report':selected.identifier,'selected_scope':selected.claim.key,'selected_value':selected.claim.asserted_value,
       'selected_task':rel['task'],'selected_decisive':rel['boolean_counterfactual_decisive'],
       'selected_candidate_feasible':rel['candidate_feasible'],'selected_favorable_infeasible':rel['objective_favoring_infeasible_candidate'],
       'selected_correct':True,'selected_original_position':originals.index(selected),'selected_branch':owner,
       'branch_loads':list(map(len,partition(reports,p['seed']))),
       'jobs':len(world.get('jobs',[])),'critical_scope_count':rel['critical_scope_count'],
       'all_outputs_valid':not row['operational_failure'],
       'root_truncated':raw['root']['response']['finish_reason']=='length'}
    if row['organization']=='hierarchical':
        coord=(p['pair_id'],row['world'])
        if coord not in necessity:necessity[coord]=necessary_keys(world,originals)
        a.update(transport_metrics(world,reports,[parsed.get('manager0'),parsed.get('manager1')],row['correct'],selected.claim.key,necessity[coord]))
    else:a.update(critical_retention=None,necessary_retention=None,selected_retained=None,visible_truth_sufficient=True,root_error_despite_sufficient_visible_truth=not row['correct'])
    annotated.append(a)

by_cell=defaultdict(dict)
for r in annotated:by_cell[tuple(r[k] for k in ('pair_id','world','organization','policy','repetition'))][r['condition']]=r
paired=[];unchanged_branch=[]
for key,arms in by_cell.items():
    for condition in ('exact','paraphrase'):
        a,b=arms[condition],arms['single']
        row={k:a[k] for k in ('pair_id','kind','family','world','organization','policy','repetition','selected_task','selected_decisive','selected_favorable_infeasible','jobs','decision_changed')}
        row.update(condition=condition,trial=a['trial_id'],baseline_trial=b['trial_id'],
                   accuracy_change=int(a['correct'])-int(b['correct']),
                   same_choice=a['choice']==b['choice'],output_validity_change=int(a['all_outputs_valid'])-int(b['all_outputs_valid']))
        for metric in ('critical_retention','necessary_retention','selected_retained','visible_truth_sufficient','root_error_despite_sufficient_visible_truth'):
            row[metric+'_change']=float(a[metric])-float(b[metric]) if a[metric] is not None and b[metric] is not None else None
        row['confidence_change_same_choice']=a['choice_confidence']-b['choice_confidence'] if row['same_choice'] and a['choice_confidence'] is not None and b['choice_confidence'] is not None else None
        for metric in ('brier','log_loss'):
            row[metric+'_change']=a[metric]-b[metric] if a.get(metric) is not None and b.get(metric) is not None else None
        paired.append(row)
        if a['organization']=='hierarchical':
            stage='manager'+str(1-a['selected_branch'])
            ra=next(calls[k] for k in a['request_hashes'] if calls[k]['stage']==stage)
            rb=next(calls[k] for k in b['request_hashes'] if calls[k]['stage']==stage)
            def findings(call):
                obj,_=parse(call['response']['text'],[],manager=True)
                return canonical([sorted(canonical([k,type(v).__name__,v]) for k,v,refs in obj['assertions']),sorted(obj['unresolved'])]) if obj else None
            unchanged_branch.append({'pair_id':a['pair_id'],'kind':a['kind'],'condition':condition,'policy':a['policy'],
               'identical_prompt':ra['prompt']==rb['prompt'],'identical_seed':ra['seed']==rb['seed'],
               'identical_response':ra['response']['text']==rb['response']['text'],
               'identical_findings':findings(ra)==findings(rb)})

estimates=[]
dimensions=[('overall',()),('policy',('policy',)),('family',('family',)),('repeated_task',('selected_task',)),
            ('decisiveness',('selected_decisive',)),('favorable_infeasible',('selected_favorable_infeasible',)),('difficulty',('jobs',))]
for dimension,extra in dimensions:
    groups=defaultdict(list)
    for r in paired:groups[tuple(r[k] for k in ('kind','organization','condition',*extra))].append(r)
    for key,rs in sorted(groups.items()):
        strata={r['pair_id']:(r['family'],r['decision_changed']) for r in rs}
        for metric in ('accuracy_change','critical_retention_change','necessary_retention_change','selected_retained_change','output_validity_change','visible_truth_sufficient_change','confidence_change_same_choice','brier_change','log_loss_change'):
            clusters=defaultdict(list)
            for r in rs:
                if r[metric] is not None:clusters[r['pair_id']].append(r[metric])
            estimates.append({'dimension':dimension,**dict(zip(('kind','organization','condition',*extra),key)),
                'metric':metric,'paired_cell_denominator':sum(map(len,clusters.values())),
                **clustered_interval({p:average(v) for p,v in clusters.items()},strata)})

# Predeclared deterministic trace selection: per family, extrema of base-average
# paired accuracy changes, then a hash-selected exactly unchanged base if present.
by_base=defaultdict(list)
for r in paired:by_base[r['pair_id']].append(r)
trace_ids=[]
for family in sorted({p['evaluation']['family'] for p in pairs.values()}):
    ids=[p for p in by_base if pairs[p]['evaluation']['family']==family]
    means={p:average(r['accuracy_change'] for r in by_base[p]) for p in ids}
    for label,pid in [('largest_improvement',max(ids,key=lambda p:(means[p],digest(p)))),
                      ('largest_deterioration',min(ids,key=lambda p:(means[p],digest(p))))]:
        trace_ids.append((label,pid))
    unchanged=[p for p in ids if all(r['accuracy_change']==0 for r in by_base[p])]
    if unchanged:trace_ids.append(('unchanged',min(unchanged,key=digest)))
trace=[];packets=[];lookup={r['trial_id']:r for r in annotated}
def selection_hash(row):
    # Preserve the trace selection established before adding calibration effects.
    return digest({k:v for k,v in row.items() if k not in ('brier_change','log_loss_change')})
for label,pid in trace_ids:
    candidates=by_base[pid]
    chosen=(max(candidates,key=lambda r:(r['accuracy_change'],selection_hash(r))) if label=='largest_improvement' else
            min(candidates,key=lambda r:(r['accuracy_change'],selection_hash(r))) if label=='largest_deterioration' else min(candidates,key=selection_hash))
    a,b=lookup[chosen['trial']],lookup[chosen['baseline_trial']]
    trace.append({'selection':label,'pair_id':pid,'family':a['family'],'kind':a['kind'],
                  'base_mean_accuracy_change':average(r['accuracy_change'] for r in candidates),
                  'observed_improvement':chosen['accuracy_change']>0,'observed_deterioration':chosen['accuracy_change']<0,
                  'condition':a['condition'],'organization':a['organization'],'policy':a['policy'],'world':a['world'],
                  'baseline_trial':b['trial_id'],'repeated_trial':a['trial_id'],'selected_task':a['selected_task'],
                  'selected_decisive':a['selected_decisive'],'oracle_choice':a['oracle_choice'],
                  'baseline_choice':b['choice'],'repeated_choice':a['choice'],
                  'baseline_critical_retention':b['critical_retention'],'repeated_critical_retention':a['critical_retention'],
                  'baseline_necessary_retention':b['necessary_retention'],'repeated_necessary_retention':a['necessary_retention'],
                  'baseline_visible_truth_sufficient':b['visible_truth_sufficient'],'repeated_visible_truth_sufficient':a['visible_truth_sufficient']})
    packets.append({'selection':trace[-1],'world':pairs[pid]['worlds'][a['world']],
                    'reports':corpus[pid]['reports'][a['world']],
                    'baseline':[calls[k] for k in b['request_hashes']],
                    'repeated':[calls[k] for k in a['request_hashes']]})
Path('artifacts/analyses/pilot-mechanism-v1').mkdir(parents=True,exist_ok=True)
Path('artifacts/analyses/pilot-mechanism-v1/trace-packets.json').write_text(json.dumps(packets,indent=2)+'\n')

inventory=[]
for kind in ('schedule','workflow'):
    singles=[r for r in annotated if r['kind']==kind and r['condition']=='single' and r['organization']=='flat' and r['policy']=='ordinary' and r['repetition']==0]
    inventory.append({'kind':kind,'base_pairs':len({r['pair_id'] for r in singles}),'worlds':len(singles),
       'correct_selected_reports':sum(r['selected_correct'] for r in singles),'decisive_boolean_selected':sum(r['selected_decisive'] for r in singles),
       'favorable_objective_on_infeasible_candidate':sum(r['selected_favorable_infeasible'] for r in singles),
       'selected_tasks':dict(Counter(r['selected_task'] for r in singles))})
paths=[]
for key in sorted({(r['kind'],r['organization'],r['policy'],r['condition']) for r in annotated}):
    rs=[r for r in annotated if tuple(r[k] for k in ('kind','organization','policy','condition'))==key]
    paths.append({**dict(zip(('kind','organization','policy','condition'),key)),'trajectories':len(rs),
                  'errors':sum(not r['correct'] for r in rs),'operational_failures':sum(r['operational_failure'] for r in rs),
                  'critical_scope_denominator':sum(r.get('critical_denominator',0) for r in rs),
                  **{m:sum(r.get(m,0) for r in rs) for m in ('critical_retained','critical_missing','critical_altered_or_conflicted','root_error_despite_sufficient_visible_truth','necessary_scope_denominator','necessary_retained','objective_denominator','objectives_retained')},
                  'visible_truth_sufficient':sum(r['visible_truth_sufficient'] for r in rs)})

old=json.loads(Path('results/pilot-v7/analysis.json').read_text());reproduced=json.loads(Path('artifacts/analyses/pilot-reproduction-20261016/analysis.json').read_text())
def numeric_diffs(a,b):
    if isinstance(a,dict):return [d for k in a if k!='analysis_settings' for d in numeric_diffs(a[k],b[k])]
    if isinstance(a,list):return [d for x,y in zip(a,b) for d in numeric_diffs(x,y)]
    return [abs(a-b)] if type(a) in (int,float) and type(b) in (int,float) else []
delta=max(numeric_diffs(old,reproduced),default=0)
if old['source_scores_sha256']!=reproduced['source_scores_sha256'] or delta>1e-12:raise RuntimeError('Pilot reproduction discrepancy')
result={'suite':'pilot-mechanism-v1','complete':True,'status':'completed_exploratory_pilot_diagnosis','amendment':'records/amendments/mechanism-v1.json',
        'independent_base_pairs':len(pairs),'trajectories':len(rows),'raw_calls':len(calls),'inventory':inventory,
        'reproduction':{'score_hash_identical':True,'maximum_numeric_difference':delta,'tolerance':1e-12,
                        'dependency_difference':{'recorded':old['analysis_settings']['dependencies'],'local':reproduced['analysis_settings']['dependencies']}},
        'source_manifest_sha256':digest(manifest),'source_scores_sha256':old['source_scores_sha256'],
        'audit_source_sha256':digest(Path(__file__).read_text()),'transport_scorer_sha256':digest(Path('src/rep_sensitivity/mechanism.py').read_text()),
        'denominators':{'effects':'Within matched world/policy/repetition cells, then equal base-cluster means. Family/change-stratified percentile bootstrap; small/degenerate intervals are not evidence of robustness.',
                        'critical_retention':'Unique mandatory Boolean scopes whose isolated truth-value flip changes the full-information decision; includes failed summaries as losses.',
                        'necessary_retention':'Unique scopes, including objectives, whose removal from full information makes the candidate choice underdetermined. Added exploratory distinction after the initial Boolean-only diagnostic, before new experiments.',
                        'root_error_despite_sufficient_visible_truth':'All trajectories; summary values alone imply exactly the oracle choice. This is an observable integration diagnostic, not faithful internal reasoning.',
                        'confidence':'Only matched cells with unchanged choice and two valid probability distributions; descriptive conditioning, not causal reliability.'},
        'estimates':estimates,'path_counts':paths,'trace_selection':trace,
        'unchanged_branch_audit':[{'kind':kind,'paired_manager_calls':len(rs),
             'identical_prompt_and_seed':sum(r['identical_prompt'] and r['identical_seed'] for r in rs),
             'different_findings_despite_identical_prompt_seed':sum(r['identical_prompt'] and r['identical_seed'] and not r['identical_findings'] for r in rs),
             'different_response_despite_identical_prompt_seed':sum(r['identical_prompt'] and r['identical_seed'] and not r['identical_response'] for r in rs)}
             for kind in ('schedule','workflow') for rs in [[r for r in unchanged_branch if r['kind']==kind]]],
        'trace_selection_rule':'Within each mutation family: maximum and minimum base-average accuracy change; one hash-selected base with zero changes in all cells if available. Extrema can equal zero; flags identify actual improvements/deteriorations.',
        'cautions':['All repeated primary reports are correct by construction; no pilot evidence about false-report repetition.',
                    'Counterfactual criticality is evaluator-only and does not establish causal mediation.',
                    'Ordering and branch assignment are frozen, not randomized independently of repetition; later controls are needed.']}
(OUT/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
for name,data in [('effects',estimates),('paths',paths),('trace_selection',trace)]:
    fields=list(dict.fromkeys(k for r in data for k in r))
    with (OUT/(name+'.csv')).open('w',newline='') as f:
        w=csv.DictWriter(f,fields,lineterminator='\n');w.writeheader();w.writerows(data)
print(json.dumps({'base_pairs':len(pairs),'trajectories':len(rows),'raw_calls':len(calls),'reproduction_max_difference':delta,'inventory':inventory,'selected_trace_comparisons':len(trace)}))
