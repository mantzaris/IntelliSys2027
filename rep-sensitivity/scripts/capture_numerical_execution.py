"""Timing/count-only snapshot: never evaluates unfinished held-out responses."""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import gzip,json
from rep_sensitivity.schema import digest
try:
    from .run_objective_confirmation import prior_seconds
    from .authorized_gpu_budget import authorized_cap
except ImportError:
    from run_objective_confirmation import prior_seconds
    from authorized_gpu_budget import authorized_cap
from rep_sensitivity.reports import thaw
from rep_sensitivity.controls import unique_clause_control


def unique_completed_clusters(events):
    """A resumed run may announce a cached cluster again; count each base once."""
    unique={}
    for event in events:
        if event['event']!='cluster_complete':continue
        key=event['pair_id']
        if key in unique and event['trajectories']!=unique[key]['trajectories']:
            raise RuntimeError('Conflicting completed-cluster sizes')
        unique.setdefault(key,event)  # Keep the actual first completion timestamp.
    return sorted(unique.values(),key=lambda event:event['utc'])


def pending_counts():
    config=json.loads(Path('configs/frozen/supporting-v7.json').read_text())
    source=Path(config['source_corpus']);pairs=json.loads((source/'pairs.json').read_text())
    corpus=json.loads((source/'frozen-reports.json').read_text());controls=0
    # Eligibility comes from the frozen task design, never model responses.
    for pair in pairs:
        if pair['index'] not in config['pair_indices']:continue
        for wi,world in enumerate(pair['worlds']):
            reports=thaw(corpus[pair['pair_id']]['reports'][wi])
            for contrast,arms in config['contrasts'].items():
                for arm in arms:
                    if contrast=='version_admission' and not (pair['evaluation']['family']=='version' and world.get('version')==2):continue
                    if contrast=='unique_clause' and unique_clause_control(world,reports,pair['split'],arm,pair['seed'])[0] is None:continue
                    if contrast=='corruption' and 'all_correct' not in arm:
                        wanted='false_objection' in arm
                        if not any(type(r.claim.asserted_value) is bool and r.claim.asserted_value==wanted for r in reports):continue
                    controls+=config['stochastic_repetitions']
    return [
        {'stage':'original supporting','models':['qwen3','phi4'],'base_pairs_shared':12,'trajectories_per_model':controls,'calls_per_model':3*controls},
        {'stage':'original live','models':['qwen3','phi4'],'base_pairs_shared':12,'trajectories_per_model':120,'maximum_calls_per_model':792},
        {'stage':'frozen root diagnostic','model':'qwen3','base_pairs':6,'trajectories':192,'calls':192},
        {'stage':'mechanism development','model':'qwen3','base_pairs':24,'trajectories':514,'physical_calls':1116,'logical_calls':1446},
        {'stage':'fresh verification diagnostic','model':'qwen3','base_pairs':6,'trajectories':30,'maximum_physical_calls':72},
        {'stage':'fresh mechanism validation','model':'qwen3','base_pairs':24,'trajectories':336,'physical_calls':624},
        {'stage':'conditional mechanism confirmation','model':'qwen3','base_pairs_options':[24,48],'trajectories_options':[288,576],
         'physical_calls_options':[576,1152],'condition':'unchanged fresh-validation gate; not launched if gate/budget fails'},
        {'stage':'original Phi-4 main','model':'phi4','base_pairs':192,'trajectories':13824,'calls':27648},
        {'stage':'objective confirmation','models':['phi4','qwen3'],'base_pairs_shared':24,'trajectories_total':480,'physical_calls_total':1056},
        {'stage':'numerical preservation','model':'qwen3','base_pairs':6,'trajectories':48,'calls':48,'condition':'last priority; sufficient remaining cumulative allowance'}]


def capture():
    root=Path('artifacts/runs/main-v7/qwen3');events=[]
    for line in (root/'events.jsonl').read_text().splitlines():
        try:events.append(json.loads(line))
        except json.JSONDecodeError:pass
    clusters=unique_completed_clusters(events);accepted=[e for e in events if e['event']=='accepted']
    starts=[e for e in events if e['event']=='run_start'];start=datetime.fromisoformat(starts[0]['utc'])
    latest=datetime.fromisoformat(clusters[-1]['utc']);elapsed=(latest-start).total_seconds()
    recent_count=min(12,len(clusters)-1)
    recent_seconds=(latest-datetime.fromisoformat(clusters[-recent_count-1]['utc'])).total_seconds()
    engine_seconds=0;latest_response=None;seen_batches=set();inputs=0;outputs=0
    accepted_keys={e['request_hash'] for e in accepted}
    for h in sorted(accepted_keys):
        path=root/'calls'/(h+'.json.gz')
        c=json.loads(gzip.decompress(path.read_bytes()));r=c['response']
        engine_seconds+=r['allocated_inference_seconds'];inputs+=r['input_tokens'];outputs+=r['output_tokens']
        seen_batches.add((r['started_utc'],r['batch_size']))
        if latest_response is None or c['accepted_utc']>latest_response:latest_response=c['accepted_utc']
    starts_by_key=Counter(e['request_hash'] for e in events if e['event']=='started')
    budget=Path('artifacts/runs/objective-confirmation-execution/budget.jsonl')
    charges=[json.loads(x) for x in budget.read_text().splitlines()] if budget.exists() else []
    record={'utc':datetime.now(timezone.utc).isoformat(),'heldout_outcomes_inspected':False,
        'main_qwen3':{'completed_base_pairs':len(clusters),'planned_base_pairs':192,
          'completed_trajectories':sum(e['trajectories'] for e in clusters),'planned_trajectories':13824,
          'accepted_calls':len(accepted_keys),'planned_calls':27648,'remaining_calls':27648-len(accepted_keys),
          'latest_completed_trajectory_timestamp':clusters[-1]['utc'],'latest_accepted_call_timestamp':latest_response,
          'overall_trajectories_per_hour':sum(e['trajectories'] for e in clusters)/elapsed*3600,
          'recent_trajectories_per_hour':recent_count*72/recent_seconds*3600,'recent_window_complete_bases':recent_count,
          'projected_remaining_main_hours_overall':(192-len(clusters))*elapsed/len(clusters)/3600,
          'projected_remaining_main_hours_recent':(192-len(clusters))*recent_seconds/recent_count/3600,
          'accepted_allocated_inference_hours':engine_seconds/3600,'accepted_batches':len(seen_batches),
          'input_tokens':inputs,'output_tokens':outputs,
          'non_inference_elapsed_seconds_through_latest_acceptance':(datetime.fromisoformat(latest_response)-start).total_seconds()-engine_seconds,
          'model_load_seconds_this_run':sum(e.get('model_load_seconds',0) for e in starts),
          'batch_failures':sum(e['event']=='batch_failed' for e in events),
          'repeat_starts':sum(max(0,n-1) for n in starts_by_key.values()),
          'started_not_yet_accepted':len(set(starts_by_key)-accepted_keys),'settings':starts[-1]['settings']},
        'additional_budget':{'cumulative_cap_seconds':authorized_cap(),'charged_seconds':prior_seconds(charges),
          'remaining_seconds':authorized_cap()-prior_seconds(charges),'ledger_sha256':digest(charges),
          'planned_confirmation_p95_seconds':5716.4277032989075,
          'new_preservation_projection_seconds':json.loads(Path('records/freezes/numerical-preservation-v1.json').read_text())['projected_seconds_p95_including_load']},
        'timing_limits':'Allocated inference seconds sum measured accepted batch wall time. Non-inference elapsed combines checkpoint/serialization/scheduling gaps, not an independently measured idle or kernel-time metric. Active unaccepted batches are not failed calls. Loading can be zero in this run when the engine was reused. Recent throughput reflects a changing case mix.',
        'planned_following_stage_counts':pending_counts(),
        'queue_order':['Qwen3 original main/support/live','frozen root diagnostic','frozen mechanism development/fresh/validation/conditional confirmation',
                       'Phi-4 original main/support/live','objective confirmation Phi-4 then Qwen3','new numerical preservation if cumulative budget permits']}
    Path('records/execution/numerical-continuation-runtime-v4.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record))


if __name__=='__main__':capture()
