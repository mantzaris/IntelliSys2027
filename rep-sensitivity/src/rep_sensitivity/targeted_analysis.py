"""Cluster-paired targeted effects; no search for a favored effect direction."""
from collections import defaultdict
import csv
import json
from pathlib import Path
import statistics
from .analysis import bootstrap,average
from .schema import digest
from .targeted_audit import inventory

METRICS=('correct','necessary_retention','unrepeated_necessary_retention','critical_retention','selected_retained',
         'unique_clause_retained','visible_truth_sufficient','root_error_despite_sufficient_visible_truth',
         'false_assertion_emitted','false_assertion_adopted','superseded_assertions_emitted',
         'operational_failure','invalid_selection','scope_transfer_count','incompatible_scope_merge_count',
         'unconsolidated_equivalent_count','summary_scope_transfer_count','summary_incompatible_scope_merge_count',
         'summary_unconsolidated_equivalent_count','brier','log_loss')


def clustered_interval(values,strata,replicates=10000):
    result=bootstrap(values,strata,replicates=replicates)
    groups=defaultdict(int)
    for pid in values:groups[strata[pid]]+=1
    singleton=any(n<2 for n in groups.values())
    result['interval_available']=not singleton
    if singleton:result.update(lower=None,upper=None,degenerate_bootstrap=None)
    return result


def comparison_terms():
    terms={
      'P1':{'hier_A4':1,'hier_common4':-1},
      'P2':{'hier_common4':1,'hier_F':-1},
      'P3':{'hier_common4':1,'hier_F':-1,'bypass_common4':-1,'bypass_F':1},
      'decisive_repetition':{'hier_A4':1,'hier_F':-1},
      'nondecisive_repetition':{'hier_B4':1,'hier_F':-1},
      'favorable_infeasible_repetition':{'hier_C4':1,'hier_F':-1},
      'uniform_repetition':{'hier_E4':1,'hier_F':-1},
      'uniform_minus_selective':{'hier_E4':1,'hier_common4':-1},
      'false_repetition':{'false_visible4':1,'false_visible1':-1},
      'false_injection':{'false_visible1':1,'false_visible_correct_control':-1},
      'dedup_exact':{'dedup_exact':1,'near_decisive_high4':-1},
      'dedup_similarity_minus_exact':{'dedup_similarity':1,'dedup_exact':-1},
      'scope_policy_minus_similarity':{'dedup_scope_policy':1,'dedup_similarity':-1},
      'scope_minus_checklist':{'scope_common4':1,'checklist_common4':-1},
      'copies_across_branches':{'copies_across_branches4':1,'hier_common4':-1},
      'superseded_repetition':{'superseded4':1,'superseded1':-1}}
    for architecture in ('flat','bypass','lossless','global'):
        terms[architecture+'_repetition']={architecture+'_common4':1,architecture+'_F':-1}
        terms['hierarchy_interaction_'+architecture]={'hier_common4':1,'hier_F':-1,architecture+'_common4':-1,architecture+'_F':1}
    for dose in (2,4,8,16):
        repeated='hier_common4' if dose==4 else 'dose'+str(dose)
        terms['dose_'+str(dose)]={repeated:1,'hier_F':-1}
        terms['evidence_minus_neutral_'+str(dose)]={repeated:1,'neutral'+str(dose):-1}
        if dose in (4,16):terms['end_minus_adjacent_'+str(dose)]={'end'+str(dose):1,repeated:-1}
    for importance in ('decisive','harmless'):
        for dose in (1,4):terms['overlap_'+importance+str(dose)]={'near_'+importance+'_high'+str(dose):1,'near_'+importance+'_low'+str(dose):-1}
        terms['repetition_overlap_'+importance]={'near_'+importance+'_high4':1,'near_'+importance+'_high1':-1,
                                               'near_'+importance+'_low4':-1,'near_'+importance+'_low1':1}
    terms['repetition_overlap_relevance']={**terms['repetition_overlap_decisive'],
                                          **{k:-v for k,v in terms['repetition_overlap_harmless'].items()}}
    terms['numeric_repetition_overlap']={'numeric_high4':1,'numeric_high1':-1,'numeric_low4':-1,'numeric_low1':1}
    return terms


def cluster_values(rows,terms,metric):
    cells=defaultdict(dict)
    for r in rows:
        value=r.get(metric)
        if value is None:continue
        for arm in [r['arm'],*r.get('aliases',[])]:cells[(r['pair_id'],r['world'],r['repetition'])][arm]=float(value)
    paired=defaultdict(list)
    for (pid,wi,rep),arms in cells.items():
        if set(terms)<=set(arms):paired[pid].append(sum(weight*arms[arm] for arm,weight in terms.items()))
    return {pid:average(values) for pid,values in paired.items()},sum(map(len,paired.values()))


def contrast_rows(rows,label):
    if not label.startswith('dose_'):return rows
    # Four presentations also appear in the broad core. Its dose-response
    # estimate must use the same world-0 subset as 2/8/16, not all core worlds.
    eligible={(r['pair_id'],r['world'],r['repetition']) for r in rows if r['arm']=='dose2'}
    return [r for r in rows if (r['pair_id'],r['world'],r['repetition']) in eligible]


def load(directory):
    directory=Path(directory);manifest=json.loads((directory/'manifest.json').read_text());config=manifest['config']
    scores=[];incomplete=[]
    for pid,n in manifest['per_pair_trajectories'].items():
        path=directory/config['model']/'scores'/(pid+'.json')
        rows=json.loads(path.read_text()) if path.exists() else []
        if len(rows)==n and len({r['trial_id'] for r in rows})==n:scores.extend(rows)
        else:incomplete.append({'pair_id':pid,'expected':n,'observed':len(rows)})
    return manifest,scores,incomplete


def summarize(directory,output,replicates=10000):
    manifest,rows,incomplete=load(directory);output=Path(output);output.mkdir(parents=True,exist_ok=True)
    config=manifest['config'];summary=[];effects=[];paired=[]
    groups=defaultdict(list)
    for r in rows:groups[(r['kind'],r['arm'])].append(r)
    for (kind,arm),rs in sorted(groups.items()):
        n=len(rs);correct=sum(r['correct'] for r in rs)
        record={'kind':kind,'model':config['model'],'arm':arm,'n':n,'clusters':len({r['pair_id'] for r in rs}),
                'correct_count':correct,'accuracy':correct/n,
                'calls':sum(r['calls'] for r in rs),'input_tokens':sum(r['input_tokens'] for r in rs),
                'output_tokens':sum(r['output_tokens'] for r in rs),'inference_seconds':sum(r['inference_seconds_allocated'] for r in rs)}
        record['tokens_per_correct']=(record['input_tokens']+record['output_tokens'])/correct if correct else None
        for metric in METRICS:
            available=[r[metric] for r in rs if r.get(metric) is not None]
            record[metric+'_mean']=average(available);record[metric+'_denominator']=len(available)
        summary.append(record)
        units=defaultdict(dict)
        for r in rs:units[(r['pair_id'],r['repetition'],r['decision_changed'])][r['world']]=r['correct']
        for changed in (False,True):
            eligible=[(pid,all(worlds.values())) for (pid,rep,ch),worlds in units.items() if ch==changed and set(worlds)=={0,1}]
            paired.append({'kind':kind,'model':config['model'],'arm':arm,'decision_changed':changed,
                           'paired_cell_denominator':len(eligible),'clusters':len({p for p,_ in eligible}),
                           'both_worlds_correct':sum(ok for _,ok in eligible),'paired_accuracy':average(ok for _,ok in eligible)})
    for kind in sorted({r['kind'] for r in rows}):
        selected=[r for r in rows if r['kind']==kind];strata={r['pair_id']:(r['family'],r['decision_changed']) for r in selected}
        for label,terms in comparison_terms().items():
            for metric in METRICS:
                values,n=cluster_values(contrast_rows(selected,label),terms,metric)
                if not values:continue
                primary=(label,metric) in {('P1','correct'),('P2','unrepeated_necessary_retention'),('P3','correct')}
                effects.append({'kind':kind,'model':config['model'],'contrast':label,'metric':metric,
                    'primary':primary and config['phase']=='heldout' and kind=='schedule',
                    'paired_cell_denominator':n,**clustered_interval(values,strata,replicates=replicates)})
    result={'suite':config['name'],'phase':config['phase'],'amendment':config['amendment'],'model':config['model'],
            'complete':not incomplete and len(rows)==manifest['trajectories'],'planned_trajectories':manifest['trajectories'],
            'analyzed_trajectories':len(rows),'incomplete_clusters':incomplete,'independent_base_pairs':manifest['base_pairs'],
            'manifest_sha256':digest(manifest),'source_scores_sha256':digest(rows),
            'analysis_source_sha256':digest(Path(__file__).read_text()),
            'summary':summary,'contrasts':effects,'paired_correctness':paired,
            'physical_resource_inventory':inventory(directory,rows),
            'interpretation':'Positive correctness effects are beneficial; positive retention effects mean more explicit scoped information survived. Broader development/subgroup contrasts are exploratory. Confidence is not reliability.'}
    (output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    for name,data in [('summary',summary),('contrasts',effects),('paired_correctness',paired)]:
        if data:
            with (output/(name+'.csv')).open('w',newline='') as f:
                writer=csv.DictWriter(f,list(data[0]),lineterminator='\n');writer.writeheader();writer.writerows(data)
    return result


def planning(directory,rule):
    manifest,rows,incomplete=load(directory)
    if incomplete:raise RuntimeError('Incomplete extension validation')
    primary=[r for r in rows if r['kind']=='schedule']
    baseline=[r for r in primary if r['arm']=='flat_F']
    accuracy=average(r['correct'] for r in baseline)
    specs={'P1':('correct',comparison_terms()['P1']),
           'P2':('unrepeated_necessary_retention',comparison_terms()['P2']),
           'P3':('correct',comparison_terms()['P3'])}
    precision={};measured_hours=sum(r['inference_seconds_allocated'] for r in rows if r['arm']!='flat_F')/3600
    for n in rule['heldout']['candidate_base_pairs']:
        values={}
        for name,(metric,terms) in specs.items():
            effects,_=cluster_values(primary,terms,metric)
            groups=defaultdict(list)
            strata={r['pair_id']:(r['family'],r['decision_changed']) for r in primary}
            for pid,val in effects.items():groups[strata[pid]].append(val)
            variances=[statistics.variance(v) for v in groups.values() if len(v)>=2]
            identified=len(variances)==6 and any(v>0 for v in variances)
            halfwidth=1.96*(sum(variances)/(36*(n/12)))**.5 if len(variances)==6 else None
            values[name]={'halfwidth_approximation':halfwidth,'variation_observed':identified,'measured_clusters':len(effects)}
        precision[str(n)]={'primary':values,'projected_inference_hours':measured_hours*n/manifest['base_pairs']}
    sufficient=all(v['variation_observed'] and v['halfwidth_approximation']<=rule['precision_target_halfwidth'] for v in precision['24']['primary'].values())
    selected=24 if sufficient or precision['48']['projected_inference_hours']>rule['heldout_inference_hour_planning_bound'] else 48
    return {'source_manifest_sha256':digest(manifest),'baseline_primary_accuracy':accuracy,'baseline_denominator':len(baseline),
            'selected_base_pairs':selected,'projections':precision,
            'eligible_to_launch':accuracy>=.85 and precision[str(selected)]['projected_inference_hours']<=rule['heldout_inference_hour_planning_bound'],
            'caution':'Approximate validation precision is not power; zero observed variance does not establish precision. Allocation ignores effect direction and significance.'}


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('directory');p.add_argument('output');a=p.parse_args()
    r=summarize(a.directory,a.output);print(json.dumps({k:r[k] for k in ('suite','complete','analyzed_trajectories')}))
