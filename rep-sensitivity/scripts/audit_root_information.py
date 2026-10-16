"""Separate end-to-end truth from decisions warranted by fixed visible inputs.

Analysis supplement declared before any root-diagnostic inference. It does not
change requests, accepted scores, eligibility, or the frozen execution snapshot.
"""
from dataclasses import replace
import json
from pathlib import Path
from collections import defaultdict
from rep_sensitivity.information import possible_decisions
from rep_sensitivity.root_diagnostic import plan
from rep_sensitivity.schema import Report, digest


def visible_answer(world, required, summaries):
    scopes = {c.key: c for r in required for c in r.claims()}
    unresolved = {k for s in summaries if s['summary'] for k in s['summary']['unresolved'] if isinstance(k,str)}
    visible = []
    for s in summaries:
        if not s['summary']: continue
        for key, value, refs in s['summary']['assertions']:
            if key in scopes and key not in unresolved:
                visible.append(Report('emitted'+str(len(visible)), replace(scopes[key], asserted_value=value), ''))
    possible = possible_decisions(world, required, visible)
    return next(iter(possible)) if len(possible)==1 else 'INSUFFICIENT', sorted(possible)


def audit(directory='artifacts/runs/root-diagnostic-v1', output='results/root-diagnostic-v1/visible-information.json'):
    directory=Path(directory)
    manifest=json.loads((directory/'manifest.json').read_text()); config=manifest['config']
    _, jobs, _=plan(config, config['source_run']); by_trial={j['trial']['trial_id']:j for j in jobs}
    rows=[r for p in sorted((directory/config['model']/'scores').glob('*.json')) for r in json.loads(p.read_text())]
    if len(rows)!=manifest['trajectories']: raise ValueError('Complete diagnostic required')
    records=[]
    for row in rows:
        job=by_trial[row['trial_id']]
        expected, possible=visible_answer(job['world'],job['reports'],job['summaries'])
        records.append({'trial_id':row['trial_id'],'pair_id':row['pair_id'],'transport':row['organization'],'arm':row['arm'],
            'world_correct':row['correct'],'input_warranted_choice':expected,
            'correct_given_visible_information':row['choice']==expected and not row['operational_failure'],
            'visible_information_determines_choice':len(possible)==1,
            'visible_unique_choice_differs_from_world_truth':len(possible)==1 and expected!=row['oracle_choice']})
    groups=defaultdict(list)
    for row in records:groups[row['transport'],row['arm']].append(row)
    aggregate=[{'transport':org,'arm':arm,'trajectories':len(rs),'base_pairs':len({r['pair_id'] for r in rs}),
        **{k:sum(r[k] for r in rs) for k in ('world_correct','correct_given_visible_information',
              'visible_information_determines_choice','visible_unique_choice_differs_from_world_truth')}}
        for (org,arm),rs in sorted(groups.items())]
    result={'status':'completed_exploratory_input_availability_audit','source_manifest_sha256':digest(manifest),
        'source_scores_sha256':digest(rows),'analysis_source_sha256':digest(Path(__file__).read_text()),
        'denominator':'All completed root trajectories, including operational failures. These are separate outcomes; end-to-end world correctness is not evidence of warranted root reasoning.',
        'rule':'Enumerate answers compatible with visible scoped values only. If several remain, expected choice is INSUFFICIENT. Required scope definitions and tie order are public; hidden values are never filled from truth. A consistent but erroneous summary can warrant a different choice from the world oracle.',
        'aggregate':aggregate}
    Path(output).write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':print(json.dumps(audit()))
