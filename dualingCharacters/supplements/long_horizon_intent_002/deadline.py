"""Remote deadline supervisor for ONE newly launched intent worker process group.

Never targets an existing controller, core job, other GPU process, or the pod.
"""
from pathlib import Path
import argparse
import os
import signal
import subprocess
import sys
import time
from pcc.resources import append_json
from .common import ROOT,ARTIFACTS,read,write,utc
from .budget import timestamp


def stop_owned_group(pid,termination=signal.SIGTERM):
    # Only a child launched with start_new_session=True may be supplied by caller.
    if pid<=1 or pid==os.getpgrp():raise ValueError('Refuse invalid/self process group')
    try:os.killpg(pid,termination)
    except ProcessLookupError:pass


def supervise(command,absolute_deadline,run_id,reservation_seconds,clock=time.time):
    start=clock();cutoff=min(float(absolute_deadline),start+float(reservation_seconds))
    if cutoff-start<30:raise PermissionError('No safe deadline interval remains')
    process=subprocess.Popen(command,start_new_session=True)
    write(ARTIFACTS/'worker_ownership.json',{'run_id':run_id,'supervisor_pid':os.getpid(),'owned_child_pid':process.pid,
      'owned_process_group':process.pid,'started_utc':utc(),'absolute_cutoff_epoch':cutoff,'reservation_seconds':reservation_seconds,
      'scope':'Only this newly created intent worker group; never core/review or unrelated processes'})
    interrupted=False
    try:
        while process.poll() is None and clock()<cutoff-15:time.sleep(min(1,max(.01,cutoff-15-clock())))
        if process.poll() is None:
            interrupted=True;stop_owned_group(process.pid)
            while process.poll() is None and clock()<cutoff-5:time.sleep(min(.25,max(.01,cutoff-5-clock())))
        if process.poll() is None:stop_owned_group(process.pid,signal.SIGKILL)
        code=process.wait(timeout=5)
    finally:
        # Any descendants belong to our new group and must not outlive its owner.
        stop_owned_group(process.pid,signal.SIGTERM)
        time.sleep(.2);stop_owned_group(process.pid,signal.SIGKILL)
    elapsed=clock()-start
    path=ROOT/'artifacts/runs'/run_id/'status.json'
    if path.exists():
        row=read(path);row.update(gpu_reserved_seconds=max(elapsed,float(row.get('gpu_reserved_seconds',0))),
          supervisor_elapsed_seconds=elapsed,supervisor_deadline_interrupted=interrupted,supervisor_exit_code=code,
          reservation_accounting='Conservative complete worker-process wall time including model load, failure and cleanup; original heartbeat retained in registry history')
        if code or interrupted:row['status']='failed';row['error']='Intent deadline/worker failure; partial artifacts retained; no automatic retry'
        append_json(ROOT/'artifacts/run_registry.jsonl',row);write(path,row)
    write(ARTIFACTS/'worker_exit.json',{'run_id':run_id,'exit_code':code,'interrupted':interrupted,'elapsed_seconds':elapsed,
      'deadline_epoch':cutoff,'ended_utc':utc(),'status_file_exists':path.exists()})
    return code if code else (124 if interrupted else 0)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['engineering','profile','evaluate']);parser.add_argument('--condition',default='C1');parser.add_argument('--seed',type=int,default=17);parser.add_argument('--reservation',type=float,required=True);parser.add_argument('--run-id',required=True);a=parser.parse_args()
    session=read(ROOT/'supplements/long_horizon_intent_002/SESSION.json')
    cmd=[sys.executable,'-m','supplements.long_horizon_intent_002.gpu',a.stage,'--condition',a.condition,'--seed',str(a.seed),'--reservation',str(a.reservation),'--run-id',a.run_id]
    raise SystemExit(supervise(cmd,timestamp(session['deadline_utc']),a.run_id,a.reservation))


if __name__=='__main__':main()
