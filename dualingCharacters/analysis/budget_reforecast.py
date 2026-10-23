"""Runtime-only amended forecast; no score or significance enters allocation."""
from pathlib import Path
import json
from pcc.campaign import load_overrides,resolve_job,jobs
from pcc.resources import sha256,used_seconds


def forecast(root: Path):
    oldpath=root/'configs/freeze_before_serialization_repair.json'
    original=json.loads(oldpath.read_text());plan=original['plan']
    basepath=root/'reports/tables/workload_forecast.json';baseline=json.loads(basepath.read_text())
    predicted={row['run_id']:row['seconds_forecast'] for row in baseline['jobs']}
    overrides=load_overrides(root);multipliers={};sources={str(basepath.relative_to(root)):sha256(basepath)}
    # Completed full-size stages are useful timing evidence even when scientifically
    # excluded for serialization. This is not an efficacy analysis.
    for model in ('qwen','phi'):
        for stage in ('fit','evaluate'):
            ratios=[1.]
            for p in sorted((root/'artifacts/runs').glob('*/status.json')):
                meta=json.loads(p.read_text());name=meta['run_id']
                if meta['status']!='completed' or meta['config']['model']!=model or meta.get('task')!=stage or name not in predicted:continue
                ratios.append(meta['gpu_reserved_seconds']/predicted[name]);sources[str(p.relative_to(root))]=sha256(p)
            multipliers[model,stage]=max(ratios)
    rows=[]
    for job in jobs(plan):
        resolved=resolve_job(job,overrides);path=root/'artifacts/runs'/resolved['id']/'status.json'
        complete=path.exists() and json.loads(path.read_text())['status']=='completed'
        seconds=0 if complete else predicted[job['id']]*multipliers.get((job['model'],job['command']),1.)
        rows.append({'original_id':job['id'],'resolved_id':resolved['id'],'completed_eligible':complete,'remaining_seconds_forecast':seconds})
    used=used_seconds(root/'artifacts/run_registry.jsonl')/3600
    remaining=sum(row['remaining_seconds_forecast'] for row in rows)/3600
    result={'classification':'Post-amendment runtime forecast; no experimental choice changed','consumed_reserved_gpu_hours':used,
            'remaining_core_forecast_hours':remaining,'total_core_forecast_hours':used+remaining,'ceiling_hours':96.,'contingency_hours':96-used-remaining,
            'supplement_not_in_core_forecast':'Unchanged separate requirement: original queue complete and at least 3.5 hours left',
            'method':'Retain original job forecasts; inflate full-size fit/evaluation stages by the largest observed actual/predicted runtime ratio, at least one; count all consumed attempts, including excluded ones',
            'multipliers':{f'{m}-{s}':v for (m,s),v in multipliers.items()},'inputs':sources,'jobs':rows}
    path=root/'reports/tables/serialization_budget_reforecast.json';path.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in {'inputs','jobs'}},indent=2))
    return result

if __name__=='__main__':forecast(Path(__file__).resolve().parents[1])
