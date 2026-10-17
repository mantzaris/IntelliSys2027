"""Analysis-only supplement: invalid fields may be decision-irrelevant.

Never changes frozen requests or primary world accuracy. Complete stage outputs
only; input-only diagnostics are available before new inference.
"""
from collections import defaultdict,Counter
from pathlib import Path
import gzip,json
from rep_sensitivity.root_diagnostic import plan as root_plan
from rep_sensitivity.objective_preservation import plan as repair_plan
from rep_sensitivity.schema import digest
from rep_sensitivity.storage import utcnow
from visible_information_v3 import visible_state,support_from_state,support_assessment


def group_rows(rows,keys):
    groups=defaultdict(list)
    for r in rows:groups[tuple(r[k] for k in keys)].append(r)
    result=[]
    for key,rs in sorted(groups.items()):
        result.append({**dict(zip(keys,key)),'base_pairs':len({r['pair_id'] for r in rs}),'trajectories':len(rs),
            **{k:sum(r[k] for r in rs) for k in ('correct','decision_determined_from_uncontested_facts',
                'determinate_despite_representation_errors','representation_errors_leave_decision_undetermined',
                'violates_uncontested_unique_decision')},
            'agreement_count':sum(r['agreement_with_uncontested_unique_decision'] is True for r in rs),
            'agreement_denominator':sum(r['agreement_with_uncontested_unique_decision'] is not None for r in rs)})
    return result


def main():
    analysis_hash=digest(Path(__file__).read_text());scorer_hash=digest(Path('scripts/visible_information_v3.py').read_text())
    # Complete historical development/validation only, from the verified raw
    # pipeline audit; strict v2 and world labels are retained alongside this view.
    path=Path('artifacts/analyses/numerical-pipeline-v1/fields.json')
    if path.exists():
        original=json.loads(path.read_text());rows=[]
        for row in original:
            if row['kind']!='schedule':continue
            support=support_from_state(row['visible_information'])
            rows.append({**{k:row[k] for k in ('suite','model','pair_id','policy','condition','correct')},**support,
                **support_assessment(support,row['choice'],row['operational_failure'])})
        out={'utc':utcnow(),'complete':True,'status':'exploratory_analysis_only_supplement','analysis_source_sha256':analysis_hash,
            'scorer_source_sha256':scorer_hash,'source_field_records_sha256':digest(original),
            'interpretation':'Representation errors remain errors. Decision support tests invariance across every admissible assignment to absent/ill-typed/disputed fields while keeping uncontested supplied values fixed; no evaluator repair. World accuracy is separate.',
            'groups':group_rows(rows,('suite','model','policy','condition'))}
        Path('results/numerical-pipeline-v1/visible-support-v3.json').write_text(json.dumps(out,indent=2)+'\n')
    inputs=[];finished=[]
    for suite,planner in [('root-diagnostic-v1',root_plan),('numerical-preservation-v1',repair_plan)]:
        config=json.loads(Path('configs/frozen',suite+'.json').read_text())
        planned=planner(config,config['source_run']) if suite.startswith('root-') else planner(config)
        pairs,jobs=planned[:2];by_id={j['trial']['trial_id']:j for j in jobs}
        for j in jobs:
            if suite.startswith('root-') and j['trial']['arm']!='F':continue
            state=visible_state(j['world'],j['reports'],j['summaries'])
            inputs.append({'suite':suite,'trial':j['trial'],'source_summary_sha256':digest(j['summaries']),
                           **support_from_state(state)})
        root=Path('artifacts/runs',suite);manifest=root/'manifest.json'
        if not manifest.exists():continue
        manifest=json.loads(manifest.read_text());folder=root/config['model']
        scores=[r for p in sorted((folder/'scores').glob('*.json')) for r in json.loads(p.read_text())]
        if len(scores)!=manifest['trajectories']:continue
        rows=[];missing=False
        for r in scores:
            j=by_id[r['trial_id']];path=folder/'calls'/(r['request_hashes'][-1]+'.json.gz')
            if not path.exists():missing=True;break
            call=json.loads(gzip.decompress(path.read_bytes()))
            # Read actual delivered JSON. Neutral root padding follows the JSON
            # and is explicitly non-evidential, so raw_decode keeps its boundary.
            payload,_=json.JSONDecoder().raw_decode(call['prompt'].split('\nINPUT\n',1)[1])
            support=support_from_state(visible_state(j['world'],j['reports'],payload['intermediate_summaries']))
            rows.append({**r,**support,**support_assessment(support,r['choice'],r['operational_failure']),
                         'actual_prompt_sha256':digest(call['prompt'])})
        if missing:continue
        result={'utc':utcnow(),'complete':True,'base_pairs':len(pairs),'trajectories':len(rows),'analysis_source_sha256':analysis_hash,
            'scorer_source_sha256':scorer_hash,'source_manifest_sha256':digest(manifest),'interpretation':'Supplement to strict v2; unchanged primary world correctness and requests.',
            'groups':group_rows(rows,('model','organization','arm'))}
        out=Path('results',suite);out.mkdir(parents=True,exist_ok=True)
        (out/'visible-support-v3.json').write_text(json.dumps(result,indent=2)+'\n')
        detail=Path('artifacts/analyses',suite+'-visible-support-v3');detail.mkdir(parents=True,exist_ok=True)
        (detail/'trajectories.json').write_text(json.dumps(rows)+'\n');finished.append(suite)
    preflight={'utc':utcnow(),'new_gpu_outputs_inspected':bool(finished),'analysis_source_sha256':analysis_hash,
        'scorer_source_sha256':scorer_hash,'contexts':inputs,
        'frozen_summary_baseline_counts':dict(Counter(r['decision_status'] for r in inputs if r['suite']=='root-diagnostic-v1' and r['trial']['organization']=='frozen_summaries'))}
    Path('records/preflight/visible-support-v3.json').write_text(json.dumps(preflight,indent=2)+'\n')
    print(json.dumps({'completed_new_stages':finished,'fixed_root_input_states':preflight['frozen_summary_baseline_counts']}))


if __name__=='__main__':main()
