"""Small durable inventories and measured runtime summaries; no inferred experiments."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import statistics
from rep_sensitivity.resources import measure_telemetry

parser=argparse.ArgumentParser();parser.add_argument('directory');a=parser.parse_args()
root=Path(a.directory)
manifest=json.loads((root/'manifest.json').read_text()) if (root/'manifest.json').exists() else None
config=manifest['config'] if manifest else json.loads((root/'config.json').read_text())
kind='replay' if manifest and 'manager_calls' in manifest else 'live' if manifest else 'controls'
planned={}
for model in config['models']:
    if kind=='replay':
        per_pair=len(config['worlds'])*len(config['policies'])*len(config['organizations'])*len(config['repetition_conditions'])*config['stochastic_repetitions']
        pairs=json.loads((root/'pairs.json').read_text())
        planned[model]={'trajectories':manifest['trajectories']//len(config['models']),
                        'calls':manifest['manager_calls']//len(config['models']),
                        'pairs':{p['pair_id']:per_pair for p in pairs}}
    elif kind=='live':
        pairs=json.loads((root/'pairs.json').read_text())
        per_pair=len(config['worlds'])*5*config['stochastic_repetitions']
        planned[model]={'trajectories':manifest['trajectories'],'calls':manifest['calls'],
                        'pairs':{p['pair_id']:per_pair for p in pairs}}
    else:
        path=root/model/'run-manifest.json'
        if not path.exists():continue
        m=json.loads(path.read_text())
        planned[model]={'trajectories':m['trajectories'],'calls':m['calls'],
            'pairs':{p.stem:json.loads(p.read_text())['trajectories'] for p in (root/model/'manifests').glob('*.json')}}
telemetry=[]
for path in Path('artifacts/runs/telemetry').glob('*.jsonl'):
    for line in path.read_text().splitlines():
        try:telemetry.append(json.loads(line))
        except json.JSONDecodeError:raise RuntimeError('Partial telemetry record; refresh the mirror before auditing')
result={'suite':config['name'],'kind':kind,'planned_trajectories':sum(p['trajectories'] for p in planned.values()),
        'planned_calls':sum(p['calls'] for p in planned.values()),
        'planned_call_interpretation':'Maximum before explicit resource displacement' if kind=='live' else 'Exact planned calls',
        'models_without_manifest':sorted(set(config['models'])-set(planned)), 'models':{}}
for model in config['models']:
    (root/model).mkdir(parents=True,exist_ok=True)
    records=[];inventory=[]
    for p in sorted((root/model/'calls').glob('*.json.gz')):
        r=json.loads(gzip.decompress(p.read_bytes()))
        records.append(r)
        inventory.append({'file':str(p.relative_to(root)), 'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
                          'request_hash':r['request_hash'],'trial_id':r['trial_id'],'stage':r['stage']})
    events=[]
    log=root/model/'events.jsonl'
    if log.exists():
        for line in log.read_text().splitlines():
            try:events.append(json.loads(line))
            except json.JSONDecodeError:raise RuntimeError('Incomplete event record; recover explicitly before audit')
    accepted={r['request_hash'] for r in records}
    started={e['request_hash'] for e in events if e['event']=='started'}
    responses=[r['response'] for r in records]
    latencies=[r['latency_seconds'] for r in responses if r.get('latency_seconds') is not None]
    wall=sum(r['allocated_inference_seconds'] for r in responses)
    output_tokens=sum(r['output_tokens'] for r in responses)
    scores=[]
    for p in (root/model/'scores').glob('*.json'):
        s=json.loads(p.read_text());scores.extend(s if isinstance(s,list) else [s])
    cluster_counts=Counter(s['pair_id'] for s in scores)
    score_requests={key for s in scores for key in s['request_hashes']}
    expected=planned.get(model,{'pairs':{},'trajectories':None,'calls':None})
    complete_clusters=sum(cluster_counts[pid]==count for pid,count in expected['pairs'].items())
    result['models'][model]={'accepted_calls':len(records),'unique_request_hashes':len(accepted),
        'started_without_accepted':len(started-accepted),'complete_clusters':complete_clusters,
        'scored_trajectories':len(scores),'planned_trajectories':expected['trajectories'],'planned_calls':expected['calls'],
        'accepted_calls_match_completed_scores':score_requests==accepted,
        'run_complete':any(e['event']=='run_complete' for e in events),
        'finish_reasons':dict(Counter(r['finish_reason'] for r in responses)),
        'input_tokens':sum(r['input_tokens'] for r in responses),'output_tokens':output_tokens,
        'measured_inference_wall_seconds':wall,'amortized_output_tokens_per_second':output_tokens/wall if wall else None,
        'mean_input_tokens':statistics.mean(r['input_tokens'] for r in responses) if responses else None,
        'mean_output_tokens':statistics.mean(r['output_tokens'] for r in responses) if responses else None,
        'maximum_input_tokens':max((r['input_tokens'] for r in responses),default=None),
        'maximum_output_tokens':max((r['output_tokens'] for r in responses),default=None),
        'observed_request_latency_calls':len(latencies),
        'median_observed_request_latency_seconds':statistics.median(latencies) if latencies else None,
        'device_telemetry':measure_telemetry(records,telemetry),
        'latency_definition':'vLLM request elapsed; inference wall excludes model loading, disk writes and software setup',
        'raw_inventory_sha256':hashlib.sha256(json.dumps(inventory,sort_keys=True).encode()).hexdigest()}
    # Inventory is durable and small relative to raw prompts; not necessary to commit all rows.
    (root/model/'inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
out=Path('records/audits');out.mkdir(parents=True,exist_ok=True)
(out/(config['name']+'.json')).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
