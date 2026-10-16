"""Exploratory replication analysis of COMPLETE original validation only.

No main-test outcomes are read. Reuses the pilot's raw-call annotation and cluster
estimator, with explicit model separation and three-policy denominators.
"""
from collections import defaultdict
from pathlib import Path
import json
from rep_sensitivity.pilot_interpretation import annotated_pilot, paired_effect, paired_world_rows, FAILURE_LABELS, write_csv
from rep_sensitivity.targeted_analysis import clustered_interval
from rep_sensitivity.analysis import bootstrap
from rep_sensitivity.schema import digest
from rep_sensitivity.storage import utcnow


def compare(rows, after, before='single', metric='correct'):
    translated=[{**r,'condition':'single' if r['condition']==before else 'treatment'}
                for r in rows if r['condition'] in (before,after)]
    return paired_effect(translated,'treatment',metric)


def analyze(source='artifacts/runs/validation-v7', output='results/validation-repetition-v1'):
    source=Path(source);output=Path(output);output.mkdir(parents=True,exist_ok=True)
    manifest,rows,calls=annotated_pilot(source)
    comparisons=[];pairs=[];interactions=[];failures=[];absolute=[];retention=[]
    for model in manifest['config']['models']:
        for kind in ('schedule','workflow'):
            base=[r for r in rows if r['model']==model and r['kind']==kind]
            strata={r['pair_id']:(r['family'],r['decision_changed']) for r in base}
            for policies in (['ordinary','checklist','scope'],['ordinary','checklist'],['ordinary'],['checklist'],['scope']):
                policy='+'.join(policies)
                group=[r for r in base if r['policy'] in policies]
                effects={}
                for org in ('flat','hierarchical'):
                    selected=[r for r in group if r['organization']==org]
                    for after,before in (('exact','single'),('paraphrase','single'),('exact','paraphrase')):
                        result=compare(selected,after,before)
                        comparisons.append({'model':model,'kind':kind,'policy':policy,'organization':org,
                            'contrast':after+' - '+before,**result})
                        effects[org,after,before]=result['base_effects']
                for after,before in (('exact','single'),('paraphrase','single'),('exact','paraphrase')):
                    hi=effects['hierarchical',after,before];flat=effects['flat',after,before]
                    values={p:hi[p]-flat[p] for p in hi}
                    interactions.append({'model':model,'kind':kind,'policy':policy,'contrast':after+' - '+before,
                        'definition':'(hierarchical treatment-baseline) - (flat treatment-baseline), accuracy scale',
                        **clustered_interval(values,strata),'base_effects':values})
            for org in ('flat','hierarchical'):
                selected=[r for r in base if r['organization']==org]
                for condition in ('single','exact','paraphrase'):
                    rs=[r for r in selected if r['condition']==condition]
                    absolute.append({'model':model,'kind':kind,'organization':org,'policy':'equal ordinary/checklist/scope',
                        'condition':condition,'base_pairs':len({r['pair_id'] for r in rs}),'trajectories':len(rs),
                        'calls':sum(r['calls'] for r in rs),'correct':sum(r['correct'] for r in rs),
                        'accuracy':sum(r['correct'] for r in rs)/len(rs),
                        **{k:sum(r[k] for r in rs) for k in ('invalid_selection','input_tokens','output_tokens','inference_seconds_allocated','operational_failure')},
                        'allocated_seconds_per_correct':sum(r['inference_seconds_allocated'] for r in rs)/sum(r['correct'] for r in rs) if any(r['correct'] for r in rs) else None})
                    failures.append({'model':model,'kind':kind,'organization':org,'condition':condition,
                        'policy':'equal ordinary/checklist/scope','base_pairs':len({r['pair_id'] for r in rs}),'trajectories':len(rs),
                        **{k:sum(r[k] for r in rs) for k in (*FAILURE_LABELS,'any_truncation')}})
                if org=='hierarchical':
                    for metric in ('necessary_retention','objective_retention','visible_truth_sufficient'):
                        for after in ('exact','paraphrase'):
                            retention.append({'model':model,'kind':kind,'organization':org,'metric':metric,
                                'policy':'equal ordinary/checklist/scope','contrast':after+' - single',**compare(selected,after,metric=metric)})
                paired=paired_world_rows(selected)
                for changed in (False,True):
                    rs=[r for r in paired if r['decision_changed']==changed]
                    for after,before in (('exact','single'),('paraphrase','single'),('exact','paraphrase')):
                        result=compare(rs,after,before)
                        pairs.append({'model':model,'kind':kind,'organization':org,'decision_changed':changed,
                            'policy':'equal ordinary/checklist/scope','contrast':after+' - '+before,'metric':'both worlds correct',
                            **result,'trajectories':2*result['trajectories']})
    change_interactions=[]
    for model in manifest['config']['models']:
        for kind in ('schedule','workflow'):
            for org in ('flat','hierarchical'):
                for contrast in ('exact - single','paraphrase - single','exact - paraphrase'):
                    values={p:v for row in pairs if (row['model'],row['kind'],row['organization'],row['contrast'])==(model,kind,org,contrast) for p,v in row['base_effects'].items()}
                    strata={row['pair_id']:(row['family'],row['decision_changed']) for row in rows if row['model']==model and row['kind']==kind}
                    change_interactions.append({'model':model,'kind':kind,'organization':org,'contrast':contrast,
                        'definition':'consequential minus harmless repetition effect on BOTH-world correctness',
                        **bootstrap(values,strata,difference=True),'base_effects':values})
    result={'status':'completed_exploratory_validation_reanalysis','complete':True,'analyzed_utc':utcnow(),
        'independent_base_pairs':len({r['pair_id'] for r in rows}),'trajectories':len(rows),'accepted_calls':len(calls),
        'source_manifest_sha256':digest(manifest),'source_scores_sha256':digest({str(p.relative_to(source)):digest(json.loads(p.read_text())) for p in sorted(source.glob('*/scores/*.json'))}),
        'analysis_source_sha256':digest(Path(__file__).read_text()),
        'annotation_source_sha256':digest(Path('src/rep_sensitivity/pilot_interpretation.py').read_text()),
        'interpretation':'New offline analysis of previously completed original validation; no new GPU calls and no original main outcomes inspected. Validation is not fresh confirmation of a post-pilot hypothesis.',
        'aggregation':'Models separate. Equal base means over paired worlds, policies and stochastic repetitions. Whole-base bootstrap stratified by mutation family and decision-change status, 10000 draws, seed 20271015. Raw effects are accuracy proportions; multiply by 100 for percentage points. Malformed completed outputs remain errors.',
        'denominators':'Absolute rows count all stated trajectories. Pair-success rows require BOTH worlds correct; trajectory counts include both worlds in both arms. Failure labels overlap and refer to all trajectories. Retention is emitted complete keyed propositions, not private reasoning. Costs are allocated batch wall time, not kernel time or money.',
        'absolute':absolute,'comparisons':comparisons,'hierarchy_interactions':interactions,'paired_world':pairs,
        'failure_locations':failures,'retention':retention,'consequential_minus_harmless':change_interactions}
    (output/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    for key in ('absolute','comparisons','hierarchy_interactions','paired_world','failure_locations','retention'):
        write_csv(output/(key+'.csv'),[{k:v for k,v in r.items() if not isinstance(v,dict)} for r in result[key]])
    detail=Path('artifacts/analyses/validation-repetition-v1');detail.mkdir(parents=True,exist_ok=True)
    (detail/'annotated-trajectories.json').write_text(json.dumps(rows)+'\n')
    focus=[r for r in comparisons if r['kind']=='schedule' and r['organization']=='hierarchical' and r['policy']=='ordinary+checklist']
    print(json.dumps({'new_gpu_calls':0,'base_pairs':result['independent_base_pairs'],'trajectories':len(rows),
        'pilot_matched_validation':[{k:v for k,v in r.items() if k not in ('base_effects','leave_one_base_out')} for r in focus]}))
    return result

if __name__=='__main__':analyze()
