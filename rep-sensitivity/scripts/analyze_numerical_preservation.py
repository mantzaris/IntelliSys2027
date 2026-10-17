"""All-or-complete six-base diagnostic; no outcome-based allocation."""
from collections import defaultdict, Counter
from pathlib import Path
import json
from rep_sensitivity.analysis import bootstrap, average
from rep_sensitivity.objective_preservation import plan
from rep_sensitivity.schema import digest
from rep_sensitivity.storage import utcnow
from visible_information_v2 import visible_state, assess_choice


def analyze():
    root=Path('artifacts/runs/numerical-preservation-v1')
    if not (root/'manifest.json').exists():return None
    manifest=json.loads((root/'manifest.json').read_text());config=manifest['config'];folder=root/config['model']
    rows=[r for p in sorted((folder/'scores').glob('*.json')) for r in json.loads(p.read_text())]
    if len(rows)!=manifest['trajectories']:return None
    hashes={h for r in rows for h in r['request_hashes']}
    if len(hashes)!=manifest['calls'] or not all((folder/'calls'/(h+'.json.gz')).exists() for h in hashes):return None
    pairs,jobs=plan(config);by_trial={j['trial']['trial_id']:j for j in jobs}
    loss={p['pair_id']:any(j['source_objective_loss'] for j in jobs if j['pair']==p and j['trial']['arm']=='A') for p in pairs}
    for r in rows:
        j=by_trial[r['trial_id']];state=visible_state(j['world'],j['reports'],j['summaries'])
        candidate=j['pair']['evaluation']['oracle'][r['world']]['candidates'].get(r['choice'])
        r.update(visible_status=state['status'],**assess_choice(state,r['choice'],r['operational_failure']),
                 feasible_but_not_preferred=bool(candidate and candidate['feasible'] and not r['correct']),sampling_loss_stratum=loss[r['pair_id']])
    analysis=json.loads(Path('configs/frozen/numerical-preservation-analysis-v1.json').read_text())
    contrasts=[];absolute=[];paired_world=[]
    for population in ('all','source_loss','source_intact'):
        rs=[r for r in rows if population=='all' or r['sampling_loss_stratum']==(population=='source_loss')]
        if not rs:continue
        for arm in ('A','B','C','D'):
            group=[r for r in rs if r['arm']==arm]
            absolute.append({'population':population,'arm':arm,'model':config['model'],'task':'schedule','policy':'ordinary',
                'base_pairs':len({r['pair_id'] for r in group}),'trajectories':len(group),'calls':len(group),
                **{k:sum(r[k] for r in group) for k in ('correct','invalid_selection','feasible_but_not_preferred','operational_failure',
                    'input_tokens','output_tokens','inference_seconds_allocated')},'accuracy':average(r['correct'] for r in group),
                'sufficient_visible_count':sum(r['agreement_with_unique_supported_decision'] is not None for r in group),
                'unique_supported_agreement_count':sum(r['agreement_with_unique_supported_decision'] is True for r in group),
                'visible_status_counts':dict(Counter(r['visible_status'] for r in group))})
        cells=defaultdict(dict)
        for r in rs:cells[r['pair_id'],r['world']][r['arm']]=r
        for changed in (False,True):
            bases={r['pair_id'] for r in rs if r['decision_changed']==changed}
            for arm in 'ABCD':
                success={pid:all(cells[pid,wi][arm]['correct'] for wi in (0,1)) for pid in bases}
                paired_world.append({'population':population,'decision_changed':changed,'arm':arm,
                    'base_pairs':len(bases),'trajectories':2*len(bases),'both_worlds_correct':sum(success.values()),
                    'both_worlds_accuracy':average(success.values()),'base_success':success,
                    'definition':'Correct responsiveness for consequential pairs; correct stability for harmless pairs. Both answers must match their world oracle.'})
        for name,terms in analysis['contrasts'].items():
            for metric in ('correct','invalid_selection','feasible_but_not_preferred','input_tokens','inference_seconds_allocated'):
                grouped=defaultdict(list)
                for (pid,wi),arms in cells.items():
                    if set(arms)!=set('ABCD'):raise ValueError('Incomplete paired world')
                    grouped[pid].append(sum(w*arms[a][metric] for a,w in terms.items()))
                values={pid:average(v) for pid,v in grouped.items()}
                # Six-base diagnostic: descriptive unstratified intervals; within
                # the prespecified loss strata use their own whole-base units.
                estimate=bootstrap(values,{pid:('diagnostic',) for pid in values},seed=20271017)
                binary={}
                if len(terms)==2 and metric in ('correct','invalid_selection','feasible_but_not_preferred'):
                    before=next(a for a,w in terms.items() if w==-1);after=next(a for a,w in terms.items() if w==1)
                    binary={'increases':sum(v[after][metric]>v[before][metric] for v in cells.values()),
                        'decreases':sum(v[after][metric]<v[before][metric] for v in cells.values()),
                        'unchanged':sum(v[after][metric]==v[before][metric] for v in cells.values())}
                contrasts.append({'population':population,'contrast':name,'metric':metric,'terms':terms,**estimate,**binary,
                    'trajectories':len(cells)*len(terms),'base_effects':values,
                    'leave_one_base_out':{pid:average(v for k,v in values.items() if k!=pid) for pid in values}})
    result={'complete':True,'status':'exploratory_cached_summary_replay','utc':utcnow(),'model':config['model'],
        'base_pairs':len(pairs),'trajectories':len(rows),'physical_calls':len(hashes),'source_manifest_sha256':digest(manifest),
        'analysis_source_sha256':digest(Path(__file__).read_text()),'analysis_config_sha256':digest(analysis),
        'interpretation':analysis['interpretation'],'absolute':absolute,'contrasts':contrasts,'paired_world':paired_world,
        'accepted_call_inventory_sha256':digest(sorted(hashes))}
    out=Path('results/numerical-preservation-v1');out.mkdir(parents=True,exist_ok=True)
    (out/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    detail=Path('artifacts/analyses/numerical-preservation-v1');detail.mkdir(parents=True,exist_ok=True)
    (detail/'trajectories.json').write_text(json.dumps(rows)+'\n')
    print(json.dumps({'complete':True,'base_pairs':len(pairs),'root_calls':len(hashes)}));return result


if __name__=='__main__':analyze()
