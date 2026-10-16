"""Inventory physical accepted calls without charging shared summaries twice."""
import gzip
import json
from pathlib import Path
from .schema import digest


def inventory(directory,rows):
    directory=Path(directory);manifest=json.loads((directory/'manifest.json').read_text())
    model=manifest['config']['model'];calls={}
    for path in sorted((directory/model/'calls').glob('*.json.gz')):
        with gzip.open(path,'rt') as f:call=json.load(f)
        expected=digest({k:call[k] for k in ('prompt','settings','trial','stage')})
        if expected!=call['request_hash'] or path.stem.split('.')[0]!=expected:
            raise RuntimeError('Accepted-call hash mismatch: '+str(path))
        calls[expected]=call
    referenced={h for row in rows for h in row['request_hashes']}
    missing=sorted(referenced-set(calls))
    if missing:raise RuntimeError('Raw calls have not all been mirrored: '+str(len(missing)))
    accepted=[calls[h]['response'] for h in sorted(referenced)]
    return {'physical_accepted_calls':len(calls),'physical_calls_referenced_by_scores':len(referenced),
            'unscored_accepted_calls':len(set(calls)-referenced),'logical_graph_calls':sum(len(r['request_hashes']) for r in rows),
            'physical_input_tokens':sum(r['input_tokens'] for r in accepted),
            'physical_output_tokens':sum(r['output_tokens'] for r in accepted),
            'physical_inference_seconds_allocated':sum(r['allocated_inference_seconds'] for r in accepted),
            'latency_seconds_sum':sum(r['latency_seconds'] for r in accepted if r.get('latency_seconds') is not None),
            'latency_denominator':sum(r.get('latency_seconds') is not None for r in accepted),
            'call_identity_sha256':digest(sorted(referenced)),
            'accounting':'Per-trajectory resources count its logical decision graph. These physical totals count each shared accepted call once. Allocated inference time is measured engine batch wall time divided across its requests, not dedicated per-request GPU time. Monetary cost is not observed.'}
