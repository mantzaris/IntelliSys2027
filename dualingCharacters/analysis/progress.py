"""Read-only queue progress without opening task outcomes."""
from pathlib import Path
import json
from pcc.campaign import jobs,load_overrides,resolve_job
from pcc.resources import used_seconds

root=Path(__file__).resolve().parents[1]
plan=json.loads((root/'configs/freeze.json').read_text())['plan']
overrides=load_overrides(root)
queue=[resolve_job(job,overrides) for job in jobs(plan)]
def read(path):
    try:return json.loads(path.read_text())
    except (FileNotFoundError,json.JSONDecodeError):return {}
state=read(root/'artifacts/campaign_state.json');current=state.get('active_job',{})
metadata=read(root/'artifacts/runs'/current.get('id','__none__')/'status.json')
complete=sum(read(root/'artifacts/runs'/job['id']/'status.json').get('status')=='completed' for job in queue)
seconds=(state['gpu_seconds_before']+metadata.get('gpu_reserved_seconds',0)) if 'gpu_seconds_before' in state else used_seconds(root/'artifacts/run_registry.jsonl')
result={'eligible_core_stages_completed':complete,'scheduled_core_stages':len(queue),
        'active_job':current.get('id'),'job_status':metadata.get('status','awaiting_mirror'),
        'reserved_gpu_hours_at_last_mirror':round(seconds/3600,4),'ceiling_hours':plan['gpu_hour_ceiling'],
        'current_job_generation_requests':metadata.get('model_calls',0),'current_job_training_input_tokens':metadata.get('train_tokens',0),
        'qualification':'Read-only progress; mirror can lag about one minute; no task-success outcomes read.'}
print(json.dumps(result,indent=2))
