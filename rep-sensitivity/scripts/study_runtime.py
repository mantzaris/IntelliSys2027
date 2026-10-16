"""Progress/provenance and measured runtime without inspecting held-out choices."""
from collections import defaultdict
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
from statistics import mean
from rep_sensitivity.schema import digest

def read(p): return json.loads(p.read_text())
now = datetime.now(timezone.utc)
rows = []
for suite in ('pilot-v7', 'validation-v7', 'main-v7', 'supporting-v7', 'live-v8',
              'controls-development-v7', 'live-development-v8', 'mechanism-development-v1',
              'fresh-probe-v1', 'mechanism-validation-v1', 'mechanism-heldout-v1', 'root-diagnostic-v1'):
    root = Path('artifacts/runs')/suite
    if not (root/'manifest.json').exists() and not (root/'config.json').exists():
        rows.append({'suite': suite, 'status': 'not_initialized'}); continue
    base_manifest = read(root/'manifest.json') if (root/'manifest.json').exists() else {'config':read(root/'config.json')}
    config = base_manifest['config']
    for model in config.get('models', [config.get('model')]):
        folder = root/model
        manifest={**base_manifest, **(read(folder/'run-manifest.json') if (folder/'run-manifest.json').exists() else {})}
        events=[]
        for line in (folder/'events.jsonl').read_text().splitlines() if (folder/'events.jsonl').exists() else []:
            try:events.append(json.loads(line))
            except json.JSONDecodeError:pass  # Active append may be partially mirrored.
        starts = [e for e in events if e['event'] == 'run_start']
        accepted = [e for e in events if e['event'] == 'accepted']
        clusters = [e for e in events if e['event'] in ('cluster_complete','live_cluster_complete','control_cluster_complete')]
        completed_bases=len({e['pair_id'] for e in clusters})
        planned_bases=config.get('base_pairs',manifest.get('base_pairs'))
        if planned_bases is None and (root/'pairs.json').exists():planned_bases=len(read(root/'pairs.json'))
        complete = any(e['event'] == 'run_complete' for e in events)
        score_paths = sorted((folder/'scores').glob('*.json'))
        # Hash raw bytes and count file names; no held-out choices are evaluated.
        score_hash = digest({p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in score_paths})
        elapsed = (datetime.fromisoformat(clusters[-1]['utc'])-datetime.fromisoformat(starts[0]['utc'])).total_seconds()/3600 if clusters and starts else None
        remaining = max(0, (planned_bases or completed_bases)-completed_bases)
        rows.append({'suite': suite, 'model': model, 'status': 'complete' if complete else 'running_or_queued',
            'completed_base_pairs': completed_bases, 'planned_base_pairs': planned_bases, 'score_files':len(score_paths),
            'accepted_calls_in_journal': len(accepted), 'call_files': len(list((folder/'calls').glob('*.json.gz'))),
            'manifest_sha256': digest(manifest), 'config_sha256': digest(config),
            'implementation_sha256': digest(read(root/'implementation.json')) if (root/'implementation.json').exists() else None,
            'dataset_pairs_sha256': manifest.get('pairs_sha256'), 'report_corpus_sha256': manifest.get('corpus_sha256'),
            'score_file_inventory_sha256': score_hash, 'settings': starts[-1]['settings'] if starts else None,
            'measured_hours_through_last_complete_cluster': elapsed,
            'projected_remaining_hours_same_mean_cluster_rate': elapsed*remaining/completed_bases if elapsed and completed_bases else None})
resource = []
for suite in ('validation-v7', 'controls-development-v7', 'live-development-v8'):
    for model in ('qwen3', 'phi4'):
        times = []; input_tokens = []; output_tokens = []; stage_times = defaultdict(list)
        for p in (Path('artifacts/runs')/suite/model/'calls').glob('*.json.gz'):
            with gzip.open(p, 'rt') as f: call = json.load(f)
            response = call['response']; seconds = response['allocated_inference_seconds']
            times.append(seconds); input_tokens.append(response['input_tokens']); output_tokens.append(response['output_tokens'])
            stage_times['root' if call['stage']=='root' else 'other'].append(seconds)
        if times:
            resource.append({'suite': suite, 'model': model, 'calls': len(times), 'allocated_hours': sum(times)/3600,
                'input_tokens': sum(input_tokens), 'output_tokens': sum(output_tokens),
                'generated_tokens_per_allocated_engine_second': sum(output_tokens)/sum(times),
                'stage_mean_allocated_seconds': {k: mean(v) for k, v in stage_times.items()}})
freeze = read(Path('records/freezes/main-v7.json'))
result = {'utc': now.isoformat(), 'heldout_outcomes_inspected': False,
    'interpretation': 'Counts, hashes, settings and timing only. Projections are extrapolations, not measured future runtimes. Allocated seconds sum measured engine batch wall time, not dedicated request latency or GPU kernel time. No monetary billing rate observed.',
    'runs': rows, 'measured_resources': resource,
    'original_main_validation_projection_hours': {m: v['projected_inference_hours'] for m, v in freeze['evidence']['projections']['192']['models'].items()}}
Path('records/execution/current-runtime.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps({'utc': result['utc'], 'main': [x for x in rows if x['suite']=='main-v7'], 'resources': resource}))
