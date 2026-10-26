"""Remote hard-timeout supervisor. Cleans only its own newly launched process group."""
import argparse,os,signal,subprocess,sys,time,fcntl
from .common import *
def main(path):
 from pcc.resources import append_json
 a=read(path);assert a['enabled'];verify(ROOT/a['freeze'])
 lock=(ROOT/'artifacts/auto008_dispatch.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 run=ROOT/'artifacts/runs'/a['run_id'];assert not run.exists(),'Preserve existing run; no implicit retry'
 env=dict(os.environ,AUTO008_OWNER_TOKEN=a['dispatch_id']);started=time.monotonic()
 child=subprocess.Popen([sys.executable,'-m','supplements.automated_evaluation_008.gpu_worker','--admission',str(path)],cwd=ROOT,env=env,start_new_session=True)
 try:code=child.wait(timeout=a['maximum_seconds']-15)
 except (subprocess.TimeoutExpired,KeyboardInterrupt):
  os.killpg(child.pid,signal.SIGTERM)
  try:child.wait(timeout=5)
  except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
  code=124
 try:os.killpg(child.pid,signal.SIGTERM)
 except ProcessLookupError:pass
 elapsed=time.monotonic()-started;status=run/'status.json'
 row=read(status) if status.exists() else {'run_id':a['run_id'],'status':'failed','model_calls':0}
 row.update(stage008=True,gpu_reserved_seconds=max(elapsed,row.get('gpu_reserved_seconds',0)),supervisor_returncode=code,supervisor_tail_reconciled=True)
 if a['task']=='compatibility':row['budget_identity']='dialogue005-compatibility'
 if code:row.update(status='failed',error='Preserved incomplete stage008 run')
 write(status,row);append_json(ROOT/'artifacts/run_registry.jsonl',row)
 if code:raise SystemExit(code)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--admission',required=True);main(Path(p.parse_args().admission))
