"""Last-priority bounded execution, sharing the original cumulative budget."""
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
from rep_sensitivity.storage import immutable_json,utcnow
try:
    from .run_objective_confirmation import append,prior_seconds
except ImportError:
    from run_objective_confirmation import append,prior_seconds


def choose_allocation(config, remaining):
    rule=config['allocation_rule']
    for mode in rule['priority']:
        p=rule['projections'][mode]
        if p['prospectively_feasible'] and remaining>=p['minimum_remaining_seconds']+rule['margin_seconds']:
            return mode,min(config['maximum_gpu_wall_seconds'],remaining-rule['margin_seconds'])
    return None,0


def main():
    p=argparse.ArgumentParser();p.add_argument('--after-pid',type=int);p.add_argument('--worker',choices=['both','feedback_only']);a=p.parse_args()
    config=json.loads(Path('configs/frozen/adjacent-explorations-v1.json').read_text())
    freeze=json.loads(Path('records/freezes/adjacent-explorations-v1.json').read_text())
    import rep_sensitivity
    source={p.name:p.read_text() for p in Path(rep_sensitivity.__file__).parent.glob('*.py')}
    if digest(source)!=freeze['source_sha256'] or digest(config)!=freeze['config_sha256']:
        raise RuntimeError('Frozen source/config changed')
    if digest(json.loads(Path('records/models/qwen3.json').read_text()))!=freeze['model_metadata_sha256']:
        raise RuntimeError('Frozen model metadata changed')
    if a.worker:
        from rep_sensitivity.adjacent_explorations import run
        run({**config,'execution_mode':a.worker});return
    own=Path('artifacts/runs/adjacent-explorations-execution');own.mkdir(parents=True,exist_ok=True)
    lock=(own/'.controller.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if any((own/name).exists() for name in ('complete.json','not-launched.json','attempt.json')):return
    while a.after_pid:
        try:alive=b'runner.py' in Path('/proc',str(a.after_pid),'cmdline').read_bytes()
        except FileNotFoundError:alive=False
        if not alive:break
        time.sleep(5)
    shared=Path('artifacts/runs/objective-confirmation-execution');shared.mkdir(parents=True,exist_ok=True)
    budget_lock=(shared/'.controller.lock').open('a');fcntl.flock(budget_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    journal=shared/'budget.jsonl';events=[json.loads(x) for x in journal.read_text().splitlines()] if journal.exists() else []
    remaining=7200-prior_seconds(events);reasons=[]
    if not Path('artifacts/runs/study-execution-v8/secondary_replay_and_live-complete.json').exists():reasons.append('Original Phi-4 incomplete')
    if not all((shared/(m+'-complete.json')).exists() for m in ('qwen3','phi4')):reasons.append('Protected confirmation incomplete')
    if not Path('artifacts/runs/numerical-preservation-execution/complete.json').exists():reasons.append('Protected numerical-preservation replay incomplete')
    mode,allocation=choose_allocation(config,remaining)
    if mode is None:reasons.append('Remaining shared allowance below frozen threshold')
    if reasons:
        immutable_json(own/'not-launched.json',{'utc':utcnow(),'reasons':reasons,'remaining_seconds':remaining});return
    if subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip():
        raise RuntimeError('GPU occupied; do not interrupt any workload')
    immutable_json(own/'allocation.json',{'mode':mode,'calls':104 if mode=='both' else 72,'allocation_seconds':allocation,
        'remaining_shared_seconds':remaining,'budget_events_sha256':digest(events),'utc':utcnow(),'new_outputs_observed':False})
    attempt='adjacent-'+str(time.time_ns());start=time.monotonic()
    append(journal,{'event':'attempt_start','attempt':attempt,'experiment':config['name'],'model':'qwen3','reserved_seconds':allocation})
    with Path('logs/adjacent-explorations-v1.log').open('a') as log:
        child=subprocess.Popen([sys.executable,__file__,'--worker',mode],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        timeout=False
        try:returncode=child.wait(timeout=allocation-30)
        except subprocess.TimeoutExpired:
            timeout=True;os.killpg(child.pid,signal.SIGTERM)
            try:returncode=child.wait(timeout=20)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);returncode=child.wait(timeout=5)
    elapsed=time.monotonic()-start
    append(journal,{'event':'attempt_end','attempt':attempt,'experiment':config['name'],'model':'qwen3','elapsed_seconds':elapsed,
        'returncode':returncode,'wall_budget_stop':timeout})
    immutable_json(own/('complete.json' if returncode==0 else 'attempt.json'),{'utc':utcnow(),'mode':mode,
        'elapsed_seconds':elapsed,'returncode':returncode,'cumulative_additional_seconds':prior_seconds(events)+elapsed,
        'action':'Retain accepted outputs, including malformed responses. No automatic restart or outcome-based sample expansion.'})
    subprocess.run([sys.executable,str(Path(__file__).parent/'analyze_adjacent_explorations.py')],check=True)


if __name__=='__main__':main()
