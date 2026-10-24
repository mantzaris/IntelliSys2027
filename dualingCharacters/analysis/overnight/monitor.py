"""Read-only snapshots; never schedules, restarts or kills GPU work."""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import fcntl
import json
import os
import shlex
import shutil
import statistics
import subprocess
from pcc.campaign import jobs,resolve_job,load_overrides
from pcc.freeze import verify_freeze
from pcc.resources import used_seconds,sha256
from supplements.review_001.freeze import verify as review_freeze
from .common import ROOT,OUT,CACHE,utc,read,write,append,log


def ssh():
    return ['ssh','-F','/dev/null','-i',os.environ.get('PCC_SSH_KEY',str(Path.home()/'.ssh/id_rsa')),'-p',os.environ.get('PCC_SSH_PORT','10219'),
      '-o','BatchMode=yes','-o','IdentitiesOnly=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=20',
      '-o','UserKnownHostsFile='+os.environ.get('PCC_KNOWN_HOSTS','/tmp/intellisys-runpod-known-hosts'),
      'root@'+os.environ.get('PCC_SSH_HOST','203.57.40.186')]


def remote_snapshot(run_id,verify_remote=False):
    script='''import json,pathlib,subprocess,time,shutil,datetime
root=pathlib.Path('/workspace/dualingCharacters');run=root/'artifacts/runs'/RUN_ID
status=json.loads((run/'status.json').read_text()) if (run/'status.json').exists() else {}
result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':status,'free_bytes':shutil.disk_usage(root).free,
'gpu':subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.total,memory.used,utilization.gpu','--format=csv,noheader'],text=True).strip(),
'gpu_processes':subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'],text=True).strip(),
'container_started':subprocess.check_output(['ps','-p','1','-o','lstart='],text=True).strip()}
files={}
for name in ('status.json','collection.jsonl','evaluation.jsonl','supervision.jsonl','training/loss.jsonl'):
 p=run/name
 if p.exists():
  st=p.stat();files[name]={'size':st.st_size,'mtime':st.st_mtime}
result['files']=files
if VERIFY:
 from pcc.freeze import verify_freeze
 result['frozen_core_files']=len(verify_freeze(root)['files'])
print(json.dumps(result))
'''.replace('RUN_ID',repr(run_id)).replace('VERIFY',str(verify_remote))
    result=subprocess.run(ssh()+['cd /workspace/dualingCharacters && PYTHONPATH=src .venv/bin/python -'],input=script,text=True,capture_output=True,timeout=45)
    if result.returncode:raise RuntimeError(result.stderr[-2000:])
    return json.loads(result.stdout)


def forecast(queue,records,current_seconds):
    # Original pilot-based per-job prediction, updated only from durations.
    original={r['run_id']:r['seconds_forecast'] for r in read(ROOT/'reports/tables/workload_forecast.json')['jobs']}
    unresolved=list(jobs(verify_freeze(ROOT)['plan']));observed={}
    for job,raw in zip(queue,unresolved):
        status=records.get(job['id'],{})
        if status.get('status')=='completed':
            key=job['model'],job['command'],job.get('horizon'),job.get('families')
            observed.setdefault(key,[]).append(status['gpu_reserved_seconds'])
    pending=[]
    for job,raw in zip(queue,unresolved):
        status=records.get(job['id'],{})
        if status.get('status')=='completed':continue
        key=job['model'],job['command'],job.get('horizon'),job.get('families')
        baseline=original[raw['id']];values=observed.get(key,[])
        predicted=statistics.median(values) if values else baseline
        conservative=max([baseline,*values])
        elapsed=status.get('gpu_reserved_seconds',0) if status.get('status')=='running' else 0
        pending.append({'run_id':job['id'],'expected_remaining_seconds':max(0,predicted-elapsed),
                        'conservative_remaining_seconds':max(0,conservative-elapsed),'matched_timing_stages':len(values)})
    estimate=current_seconds+sum(r['expected_remaining_seconds'] for r in pending)
    conservative=current_seconds+sum(r['conservative_remaining_seconds'] for r in pending)
    return {'expected_total_reserved_hours':estimate/3600,'conservative_total_reserved_hours':conservative/3600,
      'expected_remaining_core_hours':sum(r['expected_remaining_seconds'] for r in pending)/3600,
      'conservative_remaining_core_hours':sum(r['conservative_remaining_seconds'] for r in pending)/3600,
      'forecast_over_ceiling':conservative>96*3600,'method':'Completed matched model/stage/horizon/family-count median; maximum of matched observations and original per-job forecast as conservative scenario. Active elapsed time subtracted once. Not a guarantee; no outcome or schedule changes.',
      'pending':pending}


def snapshot(remote=True,initial=False):
    frozen=verify_freeze(ROOT);review=review_freeze();overrides=load_overrides(ROOT)
    queue=[resolve_job(j,overrides) for j in jobs(frozen['plan'])]
    records={p.parent.name:read(p,{}) for p in (ROOT/'artifacts/runs').glob('*/status.json')}
    state=read(ROOT/'artifacts/campaign_state.json',{});current=state.get('active_job',{}).get('id');meta=records.get(current,{})
    # Latest status reservations are checked against the shared registry at each
    # snapshot; no weighting by utilization and no exclusion of failed attempts.
    recorded=used_seconds(ROOT/'artifacts/run_registry.jsonl')
    review_used=sum(m.get('gpu_reserved_seconds',0) for name,m in records.items() if name.startswith('review001-'))
    rem=None
    if remote and current:
        try:rem=remote_snapshot(current,initial)
        except Exception as error:rem={'error':str(error)}
    updated=recorded
    if rem and 'status' in rem:
        updated+=max(0,rem['status'].get('gpu_reserved_seconds',0)-meta.get('gpu_reserved_seconds',0))
        records[current]=rem['status'];meta=rem['status']
    now=datetime.now(timezone.utc);started=meta.get('started_utc')
    unrecorded=max(0,(now-datetime.fromisoformat(started.replace('Z','+00:00'))).total_seconds()-meta.get('gpu_reserved_seconds',0)) if started and meta.get('status')=='running' else 0
    full=updated+unrecorded
    complete=[j['id'] for j in queue if records.get(j['id'],{}).get('status')=='completed']
    local_status=ROOT/'artifacts/runs'/str(current)/'status.json';local_mtime=local_status.stat().st_mtime if local_status.exists() else None
    paths=read(OUT/'SESSION.json');pids={}
    for key in ('core_controller_pid','review_coordinator_pid'):
        pids[key]=subprocess.run(['ps','-p',str(paths[key]),'-o','pid=,ppid=,etime=,comm='],capture_output=True,text=True).stdout.strip()
    summary={'utc':utc(),'active_job':current,'stage_status':meta.get('status'),'core_completed':len(complete),'core_scheduled':len(queue),
      'generation_requests':meta.get('model_calls',0),'training_input_tokens':meta.get('train_tokens',0),
      'stage_reserved_seconds':meta.get('gpu_reserved_seconds',0),'recorded_reserved_hours':recorded/3600,
      'reconciled_reserved_hours':full/3600,'active_unrecorded_upper_seconds':unrecorded,'remaining_overall_hours':96-full/3600,
      'review_reserved_hours':review_used/3600,'review_remaining_hours':2-review_used/3600,
      'review_available_after_contingency_hours':max(0,min(2-review_used/3600,95.5-full/3600)),
      'local_free_bytes':shutil.disk_usage(ROOT).free,'mirror_status_age_seconds':now.timestamp()-local_mtime if local_mtime else None,
      'core_freeze_sha256':sha256(ROOT/'configs/freeze.json'),'review_freeze_sha256':sha256(ROOT/'supplements/review_001/FREEZE.json'),
      'core_files_verified':len(frozen['files']),'supplement_files_verified':len(review['files']),
      'processes':pids,'remote':rem,'completed':complete,'review_state':read(ROOT/'artifacts/review_001/controller_state.json',{}),'known_cost_usd':None}
    if current in records and unrecorded:
        records[current]={**records[current],'gpu_reserved_seconds':records[current].get('gpu_reserved_seconds',0)+unrecorded}
    summary['sampled_gpu_busy_hours_completed']=sum(r.get('sampled_gpu_busy_seconds',0) for r in records.values() if r.get('status')=='completed')/3600
    summary['utilization_weighted_hours_completed']=sum(r.get('utilization_weighted_seconds',0) for r in records.values() if r.get('status')=='completed')/3600
    summary['utilization_qualification']='Completed-run five-second samples only; active utilization is the remote instantaneous sample. Neither is billed pod uptime.'
    prediction=forecast(queue,records,full);summary['forecast']={k:v for k,v in prediction.items() if k!='pending'}
    CACHE.mkdir(parents=True,exist_ok=True)
    stamp=now.strftime('%Y%m%dT%H%M%SZ');write(CACHE/f'monitor_{stamp}.json',summary)
    last_log=read(CACHE/'last_progress_log.json',{})
    if last_log.get('stage')!=current or now.timestamp()-last_log.get('time',0)>=3600:
        log(f'Progress: {len(complete)}/241 core stages complete; active {current}, {meta.get("model_calls",0)} generation requests, {meta.get("train_tokens",0)} training input tokens; {full/3600:.4f}/96 reserved hours. Review remains {summary["review_state"].get("status")}.')
        write(CACHE/'last_progress_log.json',{'time':now.timestamp(),'stage':current})
    write(OUT/'LATEST_STATE.json',summary);write(OUT/'RESOURCE_FORECAST.json',prediction)
    append(CACHE/'monitor.jsonl',{k:v for k,v in summary.items() if k not in {'remote','completed'}})
    if initial:write(OUT/'STARTING_INVENTORY.json',summary)
    print(json.dumps({k:summary[k] for k in ('utc','active_job','core_completed','generation_requests','training_input_tokens','reconciled_reserved_hours','mirror_status_age_seconds','forecast')},indent=2))
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--local-only',action='store_true');p.add_argument('--initial',action='store_true');a=p.parse_args();snapshot(not a.local_only,a.initial)
