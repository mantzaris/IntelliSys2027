"""One scheduling handoff; preserve every frozen experiment implementation.

No mid-inference interleaving is supported. Wait for the original natural model
stage to finish, execute the short root diagnostic once, then return to the
existing extension/Phi controller. New confirmation runs follow original Phi.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def live(pid, marker='runner.py'):
    try:
        return marker.encode() in Path('/proc',str(pid),'cmdline').read_bytes()
    except FileNotFoundError:return False


def idle_gpu():
    deadline=time.monotonic()+300
    while subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip():
        if time.monotonic()>deadline:raise RuntimeError('GPU busy; no active process interrupted')
        time.sleep(5)


def record(path,obj):
    from datetime import datetime,timezone
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():raise RuntimeError('Refusing to rewrite an execution record')
    path.write_text(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),**obj},indent=2)+'\n')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',required=True);args=parser.parse_args()
    spec=json.loads(Path(args.config).read_text());root=Path('artifacts/runs/continuation-execution-v3');root.mkdir(parents=True,exist_ok=True)
    lock=(root/'.controller.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    while live(spec['after_pid']):time.sleep(5)
    stage=Path('artifacts/runs/study-execution-v8/primary_replay_and_live-complete.json')
    if not stage.exists():raise RuntimeError('Protected original Qwen stage did not complete')
    for item in spec['stages']:
        marker=root/(item['name']+'.json')
        if marker.exists():
            prior=json.loads(marker.read_text())
            if prior['returncode']==0:continue
            # Failed new exploration must not be silently retried on restart.
            if item.get('continue_on_failure'):continue
            raise RuntimeError('Prior protected-stage failure requires investigation: '+item['name'])
        idle_gpu()
        environment=dict(os.environ,PYTHONPATH=str(Path(item['snapshot']).resolve()))
        start=time.monotonic()
        with Path(item['log']).open('a') as log:
            result=subprocess.run([sys.executable,*item['arguments']],env=environment,stdout=log,stderr=subprocess.STDOUT)
        record(marker,{'stage':item['name'],'returncode':result.returncode,'elapsed_wall_seconds':time.monotonic()-start,
            'snapshot':item['snapshot'],'action':'Accepted outputs retained; no completed response is resampled'})
        if result.returncode and not item.get('continue_on_failure'):raise RuntimeError('Protected stage stopped; inspect failure record')

if __name__=='__main__':main()
