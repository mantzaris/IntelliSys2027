"""Refresh small resource aggregates without rerunning bulk scientific audits.

Uses the unchanged aggregation definitions in pcc.package.regenerate. All attempts,
including failed and excluded ones, contribute. The ledger remains authoritative
for reservation accounting; these reports never enforce or alter scheduling.
"""
from datetime import datetime, timezone
import json
import hashlib
from pathlib import Path


def snapshot(root: Path) -> dict:
    paths=sorted((root/'artifacts/runs').glob('*/status.json'))
    raw={p:p.read_bytes() for p in paths}
    records=[json.loads(raw[p]) for p in paths]
    if not records:return {}
    start=min(datetime.fromisoformat(r['started_utc'].replace('Z','+00:00')) for r in records)
    end=max(datetime.fromisoformat(r['started_utc'].replace('Z','+00:00')).timestamp()+r['gpu_reserved_seconds'] for r in records)
    ledger=root/'artifacts/run_registry.jsonl'
    raw[ledger]=ledger.read_bytes();latest={}
    for line in raw[ledger].splitlines():
        record=json.loads(line);latest[record['run_id']]=record
    value={'reserved_gpu_hours':sum(float(r.get('gpu_reserved_seconds',0)) for r in latest.values())/3600,
      'observed_pod_wall_hours_first_to_latest_run':(end-start.timestamp())/3600,
      'pod_start_time':None,'actual_hourly_rate_usd':None,'actual_cost_usd':None,
      'inference_input_tokens':sum(r.get('input_tokens',0) for r in records),
      'generated_output_tokens':sum(r.get('output_tokens',0) for r in records),
      'training_input_tokens':sum(r.get('train_tokens',0) for r in records),
      'generation_requests':sum(r.get('model_calls',0) for r in records),
      'runs':len(records),'completed':sum(r['status']=='completed' for r in records),
      'generated_utc':datetime.now(timezone.utc).isoformat(),
      'aggregation_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
      'qualification':'Latest local mirrored metadata, including running/failed/excluded attempts. Reservation includes model loads. Observed first-to-latest interval is not total billed pod lifetime. Current remote progress may exceed the last local mirror.',
      'input_hashes':{str(p.relative_to(root)):hashlib.sha256(content).hexdigest() for p,content in raw.items()}}
    destination=root/'reports/tables/resource_totals.json';destination.parent.mkdir(parents=True,exist_ok=True)
    temporary=destination.with_suffix('.json.tmp');temporary.write_text(json.dumps(value,indent=2)+'\n');temporary.replace(destination)
    return value
