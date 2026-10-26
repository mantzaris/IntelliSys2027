"""One foreground owner-dispatched operation, no waiter and no queue changes.
The existing owner must hold local campaign.lock across this remote operation and mirroring.
The remote supervisor acquires an additional dispatch lock and the worker owns gpu.lock.
"""
import argparse,fcntl,os,signal,subprocess,sys,time
from .common import *
from .compatibility_gate import verify_freeze,prerequisites,check_admission,extension_seconds
from .compatibility_design import IDENTITY

def main(admission):
 from pcc.resources import used_seconds,append_json
 request=read(admission);verify_freeze();core,review=prerequisites()
 gate=check_admission(request,datetime.now(timezone.utc),used_seconds(ROOT/'artifacts/run_registry.jsonl'),extension_seconds(ROOT/'artifacts/run_registry.jsonl'),core,review)
 doc=read(HERE/'compatibility/DESIGN.json');run_id=doc['run_id'];run_dir=ROOT/'artifacts/runs'/run_id
 if run_dir.exists():raise FileExistsError('Existing complete or partial run preserved; no automatic retry')
 lock=(ROOT/'artifacts/compatibility_dispatch.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 if run_dir.exists():raise FileExistsError('Run appeared before dispatch lock; preserve it')
 env=dict(os.environ,PCC_COMPATIBILITY_OWNER_TOKEN=request['owner_dispatch_id']);started=time.monotonic()
 child=subprocess.Popen([sys.executable,'-m','supplements.evidence_validation_006.compatibility_worker','--admission',str(admission.resolve())],cwd=ROOT,env=env,start_new_session=True)
 write(ROOT/'artifacts/compatibility_supervisor_state.json',{'pid':os.getpid(),'child_pid':child.pid,'run_id':run_id,'budget_identity':IDENTITY,'status':'running','admission_sha256':sha(admission),'started_utc':now()})
 try:
  code=child.wait(timeout=gate['hard_timeout_seconds'])
 except (subprocess.TimeoutExpired,KeyboardInterrupt):
  os.killpg(child.pid,signal.SIGTERM)
  try:child.wait(timeout=5)
  except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
  code=124
 # A failed model process can leave its own spawned engine children. Clean only
 # this launch's isolated process group, never another campaign/GPU process.
 try:
  os.killpg(child.pid,signal.SIGTERM)
  end=time.monotonic()+5
  while time.monotonic()<end:
   try:os.killpg(child.pid,0)
   except ProcessLookupError:break
   time.sleep(.1)
  else:os.killpg(child.pid,signal.SIGKILL)
 except ProcessLookupError:pass
 elapsed=time.monotonic()-started
 # Preserve and conservatively charge the tail since last heartbeat, even on termination during loading.
 status=run_dir/'status.json'
 if status.exists() and read(status).get('owner_dispatch_id') not in [None,request['owner_dispatch_id']]:raise RuntimeError('Run ownership mismatch; do not overwrite evidence')
 row=read(status) if status.exists() else {'run_id':run_id,'status':'failed','model_calls':0,'input_tokens':0,'output_tokens':0}
 row.update(budget_identity=IDENTITY,gpu_reserved_seconds=max(elapsed,float(row.get('gpu_reserved_seconds',0))),supervisor_returncode=code,
            supervisor_tail_reconciled=True,owner_dispatch_id=request['owner_dispatch_id'])
 if code:row.update(status='failed',error='Supervised operation incomplete; preserve partial grid and all costs')
 run_dir.mkdir(parents=True,exist_ok=True);write(status,row);append_json(ROOT/'artifacts/run_registry.jsonl',row)
 write(ROOT/'artifacts/compatibility_supervisor_state.json',{'pid':os.getpid(),'child_pid':child.pid,'run_id':run_id,'status':'completed' if not code else 'incomplete','elapsed_reserved_seconds':elapsed,'returncode':code})
 fcntl.flock(lock,fcntl.LOCK_UN);lock.close()
 if code:raise SystemExit(code)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--admission',required=True);main(Path(p.parse_args().admission))
