"""Foreground integration with the existing campaign lock and mirroring path.
Disabled by default; never waits for dependencies, changes priority, or starts a coordinator.
"""
import argparse,fcntl,os,shlex,subprocess
from .common import *
from .compatibility_gate import verify_freeze,prerequisites,check_admission,extension_seconds

def main(admission):
 from pcc.resources import used_seconds
 request=read(admission)
 if request.get('enabled') is not True:raise PermissionError('Disabled; no upload, worker or reservation created')
 # The existing owner must release/hand over its stage boundary explicitly. Nonblocking acquisition cannot preempt it.
 owner=(ROOT/'artifacts/campaign.lock').open('a+');fcntl.flock(owner,fcntl.LOCK_EX|fcntl.LOCK_NB)
 try:
  frozen=verify_freeze();core,review=prerequisites()
  check_admission(request,datetime.now(timezone.utc),used_seconds(ROOT/'artifacts/run_registry.jsonl'),extension_seconds(ROOT/'artifacts/run_registry.jsonl'),core,review)
  from supplements.review_001.controller import connection
  from pcc.campaign import run_and_mirror
  ssh,target,remote=connection()
  local=[ROOT/p for p in frozen['files'] if p.startswith('supplements/evidence_validation_006/')]+[HERE/'compatibility/FREEZE.json']
  # Exact new namespace files only. Core and review scientific dependencies are verified remotely, never overwritten here.
  for source in local:
   destination=remote+'/'+str(source.relative_to(ROOT))
   subprocess.run(ssh+[target,'mkdir -p '+shlex.quote(str(Path(destination).parent))],check=True)
   subprocess.run(['rsync','-az','-e',shlex.join(ssh),str(source),target+':'+destination],check=True)
  remote_admission=remote+'/artifacts/evidence_validation_006/admission-'+sha(admission)[:16]+'.json'
  subprocess.run(ssh+[target,'mkdir -p '+shlex.quote(str(Path(remote_admission).parent))],check=True)
  subprocess.run(['rsync','-az','-e',shlex.join(ssh),str(admission),target+':'+remote_admission],check=True)
  for rel in ['artifacts/review_001/controller_state.json','artifacts/review_001/allocation.json','artifacts/campaign_resume.json']:
   source=ROOT/rel
   if source.exists():subprocess.run(['rsync','-az','-e',shlex.join(ssh),str(source),target+':'+remote+'/'+rel],check=True)
  commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
  args=['env','PYTHONPATH=src:.','PCC_CODE_COMMIT='+commit,'HF_HOME='+remote+'/artifacts/hf-cache','VLLM_WORKER_MULTIPROC_METHOD=spawn',
        '.venv-infer/bin/python','-m','supplements.evidence_validation_006.compatibility_launch','--admission',remote_admission]
  command='cd '+shlex.quote(remote)+' && '+shlex.join(args)
  log=ROOT/'artifacts/evidence_validation_006/compatibility-owner.log'
  code=run_and_mirror(ssh+[target,command],ROOT,log)
  subprocess.run(['bash','scripts/sync.sh','pull'],cwd=ROOT,check=True)
  if code:raise RuntimeError('Compatibility incomplete; existing mirror retains traces, costs and logs. No automatic retry.')
  run_dir=ROOT/'artifacts/runs/dialogue005-compat-17-v1'
  assert read(run_dir/'completion.json')['fixed_grid_complete'] is True
  write(ROOT/'artifacts/evidence_validation_006/compatibility_mirror_hashes.json',{str(p.relative_to(ROOT)):sha(p) for p in sorted(run_dir.glob('*.json*'))})
 finally:fcntl.flock(owner,fcntl.LOCK_UN);owner.close()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--admission',type=Path,default=HERE/'compatibility/ADMISSION_DISABLED.json');main(p.parse_args().admission)
