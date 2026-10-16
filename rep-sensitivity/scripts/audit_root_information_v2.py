"""Pre-outcome strict visible-information and selective-movement supplement.

Leaves the frozen inference/scoring implementation and v1 supplement intact.
"""
from collections import Counter, defaultdict
from pathlib import Path
import json
from rep_sensitivity.analysis import average, bootstrap
from rep_sensitivity.root_diagnostic import plan
from rep_sensitivity.schema import digest
if __package__:
    from .visible_information_v2 import visible_state, assess_choice
else:
    from visible_information_v2 import visible_state, assess_choice


def paired(rows, after, before='F'):
    cells=defaultdict(dict)
    for r in rows:cells[r['pair_id'],r['world'],r['repetition']][r['arm']]=r
    differences=defaultdict(list);matched=[]
    for (pid,wi,rep),arms in cells.items():
        if after not in arms or before not in arms:continue
        a,b=arms[before],arms[after];matched.append((a,b))
        differences[pid].append(int(b['world_correct'])-int(a['world_correct']))
    values={p:average(v) for p,v in differences.items()}
    if not values:return None
    # Additional descriptive uncertainty only. Original family/change-stratified
    # intervals remain withheld because those six strata contain one base each.
    result=bootstrap(values,{p:'six-base diagnostic' for p in values},replicates=10000)
    changes=Counter()
    for a,b in matched:
        target=b['selected_candidate']
        if target:
            changes['toward_target']+=a['choice']!=target and b['choice']==target
            changes['away_from_target']+=a['choice']==target and b['choice']!=target
            changes['target_unchanged']+=(a['choice']==target)==(b['choice']==target)
    return {'contrast':after+' - '+before,**result,'baseline_accuracy':average(a['world_correct'] for a,b in matched),
        'repeated_accuracy':average(b['world_correct'] for a,b in matched),
        'matched_contexts':len(matched),'trajectories':2*len(matched),'calls':2*len(matched),
        'improvements':sum(b['world_correct']>a['world_correct'] for a,b in matched),
        'regressions':sum(b['world_correct']<a['world_correct'] for a,b in matched),
        'unchanged':sum(b['world_correct']==a['world_correct'] for a,b in matched),
        'base_effects':values,'leave_one_base_out':{p:average(v for q,v in values.items() if q!=p) for p in values},
        'movement':dict(changes),'movement_denominator':sum(b['selected_candidate'] is not None for a,b in matched)}


def audit(directory='artifacts/runs/root-diagnostic-v1', output='results/root-diagnostic-v1/visible-information-v2.json'):
    directory=Path(directory);manifest=json.loads((directory/'manifest.json').read_text());config=manifest['config']
    _,jobs,_=plan(config,config['source_run']);by_trial={j['trial']['trial_id']:j for j in jobs}
    rows=[r for p in sorted((directory/config['model']/'scores').glob('*.json')) for r in json.loads(p.read_text())]
    if len(rows)!=manifest['trajectories']:raise ValueError('Wait for the complete diagnostic')
    records=[]
    for row in rows:
        j=by_trial[row['trial_id']];state=visible_state(j['world'],j['reports'],j['summaries'])
        reference=visible_state(j['world'],j['reports'],j['fixed_summaries'])
        if state!=reference:raise ValueError('Repetition changed the input information state')
        selected={r.claim.candidate_identifier for r in j['reports'] if r.claim.key in row['selected_keys']}
        target=next(iter(selected)) if len(selected)==1 and row['arm']!='neutral' else None
        records.append({'trial_id':row['trial_id'],'pair_id':row['pair_id'],'world':row['world'],'repetition':row['repetition'],
            'model':row['model'],'kind':'schedule','policy':'ordinary','transport':row['organization'],'arm':row['arm'],
            'choice':row['choice'],'selected_candidate':target,'world_correct':row['correct'],
            'world_oracle':row['oracle_choice'],'invalid_selection':row['invalid_selection'],
            'feasible_suboptimal':row['strictly_suboptimal_objective'],'tie_break_error':row['tie_break_error'],
            'output_failure':row['operational_failure'],'state':state,**assess_choice(state,row['choice'],row['operational_failure']),
            **{k:row[k] for k in ('input_tokens','output_tokens','inference_seconds_allocated')}})
    groups=defaultdict(list)
    for r in records:groups[r['transport'],r['arm']].append(r)
    aggregate=[]
    for (org,arm),rs in sorted(groups.items()):
        unique=[r for r in rs if r['state']['unique_supported_decision']]
        aggregate.append({'transport':org,'arm':arm,'model':config['model'],'kind':'schedule','policy':'ordinary',
            'trajectories':len(rs),'calls':len(rs),'base_pairs':len({r['pair_id'] for r in rs}),
            'world_correct':sum(r['world_correct'] for r in rs),'accuracy':average(r['world_correct'] for r in rs),
            'information_status_counts':dict(Counter(r['state']['status'] for r in rs)),
            'unique_supported_decisions':len(unique),'agrees_with_unique_decision':sum(r['agreement_with_unique_supported_decision'] for r in unique),
            'unique_agreement_rate':average(r['agreement_with_unique_supported_decision'] for r in unique) if unique else None,
            'lucky_world_correct_without_unique_support':sum(r['world_correct'] and not r['state']['unique_supported_decision'] for r in rs),
            **{k:sum(r[k] for r in rs) for k in ('invalid_selection','feasible_suboptimal','tie_break_error','output_failure','sufficient_information_violated','input_tokens','output_tokens','inference_seconds_allocated')},
            'allocated_seconds_per_correct':sum(r['inference_seconds_allocated'] for r in rs)/sum(r['world_correct'] for r in rs) if any(r['world_correct'] for r in rs) else None})
    effects=[]
    for org in ('frozen_summaries','lossless'):
        rs=[r for r in records if r['transport']==org]
        for a,b in [(a,'F') for a in ('objective0','objective1','objective2','constraint','uniform_objectives','neutral','end')]+[
            ('uniform_objectives','objective0'),('uniform_objectives','objective1'),('uniform_objectives','objective2')]:
            result=paired(rs,a,b)
            if result:effects.append({'transport':org,'model':config['model'],'kind':'schedule','policy':'ordinary',**result})
    result={'complete':True,'analysis_version':'root-information-v2','status':'exploratory_six_base_diagnostic',
        'source_manifest_sha256':digest(manifest),'source_scores_sha256':digest(rows),
        'analysis_source_sha256':digest(Path(__file__).read_text()),'scorer_source_sha256':digest(Path('scripts/visible_information_v2.py').read_text()),
        'independent_base_pairs':len({r['pair_id'] for r in records}),'trajectories':len(records),
        'design':'Both selective repetition of EACH candidate objective in turn and balanced repetition of ALL candidate objectives. Four total presentations of each selected assertion; no paraphrase arm. Incoming distinct assertions fixed within each transport. Lossless transport is a separate idealized preservation intervention, not recovery from hidden truth.',
        'inference':'Additional unstratified whole-base 95% percentile intervals (10000 draws; seed 20271015) are descriptive with six clusters. Frozen family/change-stratified intervals remain unavailable. No confirmatory claims or p-values.',
        'denominators':'World accuracy and failures use all trajectories including malformed outputs. Unique-agreement uses only sufficient-consistent inputs. Possible under some completion is distinct from justified under every completion. Contradictory or ill-typed inputs have no strict consistent completion; relaxed possibilities are separately labeled and never silently substituted for truth.',
        'semantics':'Report-level conjunction and integer nonnegative scheduling objectives with public tie order; no hidden candidate starts, oracle values or evidence repair. Unknown scope keys do not bind other entities. Citation errors are logged separately. The abstraction cannot infer correlations among unseen world fields.',
        'aggregate':aggregate,'effects':effects}
    Path(output).write_text(json.dumps(result,indent=2)+'\n')
    detail=Path('artifacts/analyses/root-information-v2');detail.mkdir(parents=True,exist_ok=True)
    (detail/'trajectories.json').write_text(json.dumps(records,indent=2)+'\n')
    return result

if __name__=='__main__':print(json.dumps(audit()))
