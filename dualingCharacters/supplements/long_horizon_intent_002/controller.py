"""One-shot, foreground intent dispatch. No waiter and no post-session scheduling."""
from itertools import product
import argparse
import fcntl
import math
import os
import shlex
import subprocess
import sys
import time
from pcc.campaign import run_and_mirror
from pcc.resources import sha256,used_seconds
from supplements.review_001.controller import connection
from .common import ROOT,HERE,REPORTS,ARTIFACTS,read,write,utc
from .budget import readiness,allowance,cumulative_extension_seconds,choose_tier,timestamp
from .freeze import verify,bind
from .benchmark import selection


def state(status,**kwargs):write(ARTIFACTS/'controller_state.json',{'status':status,'pid':os.getpid(),'updated_utc':utc(),**kwargs})


def upload(ssh,target,remote):
    # Only new supplement sources/public data and explicit operational gate snapshots.
    subprocess.run(ssh+[target,'mkdir -p '+shlex.quote(remote+'/supplements/long_horizon_intent_002')+' '+shlex.quote(remote+'/artifacts/long_horizon_intent_002')+' '+shlex.quote(remote+'/artifacts/review_001')],check=True)
    subprocess.run(['rsync','-az','--exclude=__pycache__','--exclude=reports','-e',shlex.join(ssh),str(HERE)+'/',target+':'+remote+'/supplements/long_horizon_intent_002/'],check=True)
    subprocess.run(['rsync','-az','--include=*/','--include=*-public.json','--exclude=*','-e',shlex.join(ssh),str(ARTIFACTS/'dataset')+'/',target+':'+remote+'/artifacts/long_horizon_intent_002/dataset/'],check=True)
    for name in ('bindings.json','allocation.json','activation.json'):
        path=ARTIFACTS/name
        if path.exists():subprocess.run(['rsync','-az','-e',shlex.join(ssh),str(path),target+':'+remote+'/artifacts/long_horizon_intent_002/'],check=True)
    for rel in ('artifacts/campaign_state.json','artifacts/review_001/controller_state.json'):
        subprocess.run(['rsync','-az','-e',shlex.join(ssh),str(ROOT/rel),target+':'+remote+'/'+rel],check=True)


def execute(stage,condition,seed,reservation,ssh,target,remote):
    session=read(HERE/'SESSION.json')
    if time.time()>=timestamp(session['useful_work_deadline_utc']):raise PermissionError('Useful-work deadline reached; no new GPU stage')
    run_id=f'intent002-{stage}-17-v1' if stage!='evaluate' else f'intent002-evaluate-qwen-{condition.lower()}-{seed}-v1'
    status=ROOT/'artifacts/runs'/run_id/'status.json'
    if status.exists():
        if read(status)['status']=='completed':return
        raise RuntimeError('Existing incomplete intent run requires explicit audit; no automatic retry: '+run_id)
    state('running',run_id=run_id,stage=stage,reservation_seconds=reservation)
    env=['env','PYTHONPATH=src',f'HF_HOME={remote}/artifacts/hf-cache',f'PCC_CODE_COMMIT={verify()["code_commit"]}','VLLM_WORKER_MULTIPROC_METHOD=spawn']
    args=[*env,'.venv-infer/bin/python','-m','supplements.long_horizon_intent_002.deadline',stage,'--condition',condition,'--seed',str(seed),'--reservation',str(reservation),'--run-id',run_id]
    command='cd '+shlex.quote(remote)+' && '+shlex.join(args)
    rc=run_and_mirror(ssh+[target,command],ROOT,ARTIFACTS/(run_id+'.log'))
    subprocess.run(['bash','scripts/sync.sh','pull'],cwd=ROOT,check=True)
    # sync.sh mirrors all runs/registry, but this separate supplement's watchdog files need explicit pull.
    subprocess.run(['rsync','-az','-e',shlex.join(ssh),target+':'+remote+'/artifacts/long_horizon_intent_002/worker_exit.json',str(ARTIFACTS)+'/'],check=True)
    if rc or read(status,{}).get('status')!='completed':raise RuntimeError('Intent worker failed or stopped at deadline; partial artifacts retained, no automatic retry')


def allocate():
    session=read(HERE/'SESSION.json');profile=ROOT/'artifacts/runs/intent002-profile-17-v1';engineering=ROOT/'artifacts/runs/intent002-engineering-17-v1'
    for run in (profile,engineering):
        if read(run/'status.json')['status']!='completed' or not read(run/'completion.json')['completed_fixed_scope']:raise ValueError('Completed engineering and profile required')
    timing=read(profile/'timing_only.json')
    if timing['task_scores_computed'] is not False or timing['allocation_output_cap']!=640:raise ValueError('Timing-only profile required')
    available=allowance(session,time.time(),used_seconds(ROOT/'artifacts/run_registry.jsonl'),cumulative_extension_seconds(ROOT/'artifacts/run_registry.jsonl'))
    result=choose_tier(timing['slowest_seconds_per_generated_token'],640,timing['load_seconds'],available['available_seconds'])
    selected=result['selected']
    if selected:
        selected['family_ids']=selection(selected['families'])
        # Round DOWN the common worker reservation. The conservative whole-tier
        # estimate includes one 90-second margin; each worker also has its own
        # stop-before-batch safety margin, making this stricter, never more compute.
        result['per_worker_reservation_seconds']=math.floor(selected['conservative_seconds']/(len(selected['seeds'])*3))
        if result['per_worker_reservation_seconds']<120:raise ValueError('Implausibly short safe worker reservation')
    result.update(frozen_utc=utc(),session_id=session['session_id'],session_deadline_utc=session['deadline_utc'],
      intent_freeze_sha256=sha256(HERE/'FREEZE.json'),bindings_sha256=sha256(ARTIFACTS/'bindings.json'),
      profile_status_sha256=sha256(profile/'status.json'),profile_timing_sha256=sha256(profile/'timing_only.json'),
      engineering_status_sha256=sha256(engineering/'status.json'),available=available,model_judging=False)
    path=ARTIFACTS/'allocation.json'
    if path.exists():
        previous=read(path)
        for k in ('intent_freeze_sha256','bindings_sha256','profile_timing_sha256'):
            if previous[k]!=result[k]:raise ValueError('Existing allocation provenance differs')
        return previous
    write(path,result);write(REPORTS/'ALLOCATION.json',result);return result


def run_once():
    ARTIFACTS.mkdir(parents=True,exist_ok=True)
    own=(ARTIFACTS/'controller.lock').open('a+');fcntl.flock(own,fcntl.LOCK_EX|fcntl.LOCK_NB)
    gate=readiness()
    if not gate['admitted']:state('disabled_or_pending',gate=gate,waiting_process_created=False);return
    verify()
    shared=(ROOT/'artifacts/campaign.lock').open('a+')
    try:fcntl.flock(shared,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:state('pending_shared_owner',waiting_process_created=False);return
    try:
        # Recheck after acquiring the existing ownership lock; no polling/waiter.
        if not readiness()['admitted']:state('disabled_or_pending_after_lock');return
        bind();ssh,target,remote=connection();upload(ssh,target,remote)
        execute('engineering','C1',17,900,ssh,target,remote)
        execute('profile','C1',17,900,ssh,target,remote)
        allocation=allocate();upload(ssh,target,remote)
        if not allocation['selected']:state('no_complete_tier_fits',allocation=allocation);return
        for seed,condition in product(allocation['selected']['seeds'],('C1','C3','C5')):
            execute('evaluate',condition,seed,allocation['per_worker_reservation_seconds'],ssh,target,remote)
        state('complete_frozen_scope',allocation=allocation)
    except Exception as error:
        state('incomplete_or_blocked',error=str(error),automatic_retries=0);raise
    finally:
        fcntl.flock(shared,fcntl.LOCK_UN);shared.close()
        # A completed/failed foreground dispatch never leaves implicit permission to restart.
        write(ARTIFACTS/'activation.json',{'enabled':False,'session_id':read(HERE/'SESSION.json')['session_id'],'reason':'Foreground dispatch ended; no new background extension','updated_utc':utc()})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['readiness','run']);a=p.parse_args()
    if a.command=='readiness':print(readiness())
    else:run_once()
