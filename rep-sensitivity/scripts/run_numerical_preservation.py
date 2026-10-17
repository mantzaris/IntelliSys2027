"""Last-priority diagnostic sharing the existing cumulative budget ledger."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from rep_sensitivity.schema import digest
from rep_sensitivity.storage import immutable_json, utcnow
from run_objective_confirmation import append, prior_seconds
from authorized_gpu_budget import authorized_cap


def main():
    p=argparse.ArgumentParser();p.add_argument('--after-pid',type=int);p.add_argument('--worker',action='store_true');a=p.parse_args()
    config=json.loads(Path('configs/frozen/numerical-preservation-v1.json').read_text())
    freeze=json.loads(Path('records/freezes/numerical-preservation-v1.json').read_text())
    import rep_sensitivity
    source={p.name:p.read_text() for p in Path(rep_sensitivity.__file__).parent.glob('*.py')}
    amendment=Path('records/amendments/numerical-preservation-numeric-noop-v1.json')
    execution_source=json.loads(amendment.read_text())['execution_source_sha256'] if amendment.exists() else freeze['source_sha256']
    if digest(source)!=execution_source or digest(config)!=freeze['config_sha256']:raise RuntimeError('Frozen implementation changed')
    if a.worker:
        from rep_sensitivity.objective_preservation import run
        run(config);return
    own=Path('artifacts/runs/numerical-preservation-execution');own.mkdir(parents=True,exist_ok=True)
    lock=(own/'.controller.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if (own/'complete.json').exists() or (own/'not-launched.json').exists() or (own/'attempt.json').exists():return
    while a.after_pid:
        try:alive=b'runner.py' in Path('/proc',str(a.after_pid),'cmdline').read_bytes()
        except FileNotFoundError:alive=False
        if not alive:break
        time.sleep(5)
    shared=Path('artifacts/runs/objective-confirmation-execution')
    shared.mkdir(parents=True,exist_ok=True)
    # The original confirmation owns this lock while waiting/running. Acquire it
    # only after its process exits. No cap reset or competing GPU process.
    budget_lock=(shared/'.controller.lock').open('a');fcntl.flock(budget_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    journal=shared/'budget.jsonl';events=[json.loads(x) for x in journal.read_text().splitlines()] if journal.exists() else []
    remaining=authorized_cap(config['shared_gpu_wall_seconds_cap'])-prior_seconds(events)
    reasons=[]
    if not Path('artifacts/runs/study-execution-v8/secondary_replay_and_live-complete.json').exists():reasons.append('original Phi-4 incomplete')
    if not all((shared/(m+'-complete.json')).exists() for m in ('phi4','qwen3')):reasons.append('protected objective confirmation incomplete')
    if remaining<config['minimum_remaining_seconds_to_start']:reasons.append('remaining cumulative allowance below frozen start threshold')
    if reasons:
        immutable_json(own/'not-launched.json',{'utc':utcnow(),'reasons':reasons,'remaining_seconds':remaining});return
    if subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip():
        raise RuntimeError('GPU occupied; diagnostic not launched')
    allocation=min(remaining,config['maximum_gpu_wall_seconds']);attempt='numerical-'+str(time.time_ns())
    journal.touch(exist_ok=True);start=time.monotonic()
    append(journal,{'event':'attempt_start','attempt':attempt,'experiment':config['name'],'model':'qwen3','reserved_seconds':allocation})
    with Path('logs/numerical-preservation-v1.log').open('a') as log:
        child=subprocess.Popen([sys.executable,__file__,'--worker'],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        timeout=False
        try:returncode=child.wait(timeout=allocation-30)
        except subprocess.TimeoutExpired:
            timeout=True;os.killpg(child.pid,signal.SIGTERM)
            try:returncode=child.wait(timeout=20)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);returncode=child.wait(timeout=5)
    elapsed=time.monotonic()-start
    append(journal,{'event':'attempt_end','attempt':attempt,'experiment':config['name'],'model':'qwen3','elapsed_seconds':elapsed,
        'returncode':returncode,'wall_budget_stop':timeout})
    immutable_json(own/('complete.json' if returncode==0 else 'attempt.json'),{'utc':utcnow(),'elapsed_seconds':elapsed,'returncode':returncode,
        'cumulative_additional_seconds':prior_seconds(events)+elapsed,'action':'Retain all accepted outputs; no automatic retry or sample extension'})
    subprocess.run([sys.executable,str(Path(__file__).parent/'analyze_numerical_preservation.py')],check=True)


if __name__=='__main__':main()
