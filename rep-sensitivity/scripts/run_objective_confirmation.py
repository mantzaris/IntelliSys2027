"""Post-Phi, two-hour maximum GPU allocation for the new confirmation only."""
import argparse,fcntl,json,os,signal,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path
from rep_sensitivity.schema import digest
from rep_sensitivity.storage import immutable_json


def append(path,value):
    with path.open('a') as f:
        f.write(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),**value})+'\n');f.flush();os.fsync(f.fileno())


def prior_seconds(events):
    starts={};ends={}
    for e in events:
        if e['event']=='attempt_start':starts[e['attempt']]=e
        if e['event']=='attempt_end':ends[e['attempt']]=e
    # Ambiguous controller death is charged its whole reserved allowance. Never
    # silently reset a GPU budget on resume or repeat accepted malformed answers.
    return sum(ends[k]['elapsed_seconds'] if k in ends else s['reserved_seconds'] for k,s in starts.items())


def main():
    p=argparse.ArgumentParser();p.add_argument('--after-pid',type=int);p.add_argument('--config',default='configs/frozen/objective-confirmation-v1.json')
    p.add_argument('--model');p.add_argument('--budget-seconds',type=float);a=p.parse_args()
    config=json.loads(Path(a.config).read_text());freeze=json.loads(Path('records/freezes/objective-confirmation-v1.json').read_text())
    import rep_sensitivity
    package=Path(rep_sensitivity.__file__).parent
    if digest({p.name:p.read_text() for p in package.glob('*.py')})!=freeze['source_sha256'] or digest(config)!=freeze['config_sha256']:
        raise RuntimeError('Frozen source/config mismatch')
    if a.model:
        from rep_sensitivity.objective_confirmation import run
        if not run(config,a.model,a.budget_seconds):raise SystemExit(2)
        return
    root=Path('artifacts/runs/objective-confirmation-execution');root.mkdir(parents=True,exist_ok=True)
    lock=(root/'.controller.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    while a.after_pid:
        try:alive=b'run_safe_continuation.py' in Path('/proc',str(a.after_pid),'cmdline').read_bytes()
        except FileNotFoundError:alive=False
        if not alive:break
        time.sleep(5)
    if not Path('artifacts/runs/study-execution-v8/secondary_replay_and_live-complete.json').exists():
        raise RuntimeError('Original Phi-4 is incomplete; new confirmation stays blocked')
    journal=root/'budget.jsonl';journal.touch(exist_ok=True)
    for model in config['models']:
        marker=root/(model+'-complete.json')
        if marker.exists():continue
        events=[json.loads(x) for x in journal.read_text().splitlines() if x]
        remaining=config['additional_gpu_wall_seconds_cap']-prior_seconds(events)
        if remaining<=60:
            append(journal,{'event':'budget_exhausted','remaining_seconds':remaining});break
        if subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip():
            raise RuntimeError('GPU occupied; no unrelated process interrupted')
        attempt=str(time.time_ns());start=time.monotonic()
        append(journal,{'event':'attempt_start','attempt':attempt,'model':model,'reserved_seconds':remaining})
        with Path('logs',config['name']+'-'+model+'.log').open('a') as log:
            child=subprocess.Popen([sys.executable,__file__,'--config',a.config,'--model',model,'--budget-seconds',str(remaining-30)],
                                   stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            timeout=False
            try:returncode=child.wait(timeout=remaining-30)
            except subprocess.TimeoutExpired:
                timeout=True;os.killpg(child.pid,signal.SIGTERM)
                try:returncode=child.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid,signal.SIGKILL);returncode=child.wait(timeout=5)
        elapsed=time.monotonic()-start
        append(journal,{'event':'attempt_end','attempt':attempt,'model':model,'elapsed_seconds':elapsed,'returncode':returncode,
            'wall_budget_stop':timeout,'action':'Preserve accepted outputs; in-flight requests remain explicitly ambiguous. No accuracy-based stopping.'})
        if returncode==0:immutable_json(marker,{'model':model,'completed':True,'elapsed_wall_seconds':elapsed})
        # Analyze each complete model immediately. Use the archived analysis file
        # and original package; local hooks add manuscript assets after mirroring.
        subprocess.run([sys.executable,str(Path(__file__).parent/'analyze_objective_confirmation.py')],check=True)
        if returncode!=0:break

if __name__=='__main__':main()
