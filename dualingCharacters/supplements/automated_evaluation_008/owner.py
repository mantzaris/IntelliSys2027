"""Foreground stage008 dispatch at a verified native core boundary. No waiter."""
import argparse,fcntl,os,shlex,subprocess
from .common import *
def main(admission):
 from pcc.resources import used_seconds
 from pcc.campaign import run_and_mirror
 from supplements.review_001.controller import connection
 from .gpu_worker import stage_seconds
 a=read(admission);assert a['enabled'];verify(ROOT/a['freeze'])
 hold=read(ROOT/'artifacts/campaign_boundary_hold.json');assert hold.get('requested_by')=='automated_evaluation_008'
 owner=(ROOT/'artifacts/campaign.lock').open('a+');fcntl.flock(owner,fcntl.LOCK_EX|fcntl.LOCK_NB)
 # Native previous controller must already have exited after completing/mirroring its stage.
 old=read(ART/'original_owner_private.json');assert not Path('/proc',str(old['pid'])).exists(),'Original owner still exists'
 os.environ.update(old['environment']);ssh,target,remote=connection()
 used=used_seconds(ROOT/'artifacts/run_registry.jsonl');assert used+a['remaining_obligations_seconds']+a['maximum_seconds']+1800<=345600
 assert stage_seconds(ROOT/'artifacts/run_registry.jsonl')+a['maximum_seconds']<=14400
 inputs=ROOT/a['inputs'] if a.get('inputs') else None
 # Upload only bound008 files and unchanged compatibility dependencies, not whole project.
 files={ROOT/n for n in read(ROOT/a['freeze'])['files']}|{ROOT/a['freeze'],admission}
 if inputs:files.add(inputs)
 if a['task']=='compatibility':
  cf=read(ROOT/'supplements/evidence_validation_006/compatibility/FREEZE.json')
  files|={ROOT/n for n in cf['files'] if n.startswith('supplements/evidence_validation_006/')}
  files.add(ROOT/'supplements/evidence_validation_006/compatibility/FREEZE.json')
 for source in sorted(files):
  dest=remote+'/'+str(source.relative_to(ROOT));subprocess.run(ssh+[target,'mkdir -p '+shlex.quote(str(Path(dest).parent))],check=True)
  subprocess.run(['rsync','-az','-e',shlex.join(ssh),str(source),target+':'+dest],check=True)
 remote_admission=remote+'/'+str(admission.relative_to(ROOT));cmd='cd '+shlex.quote(remote)+' && '+shlex.join(['env','PYTHONPATH=src:.','HF_HOME='+remote+'/artifacts/hf-cache','VLLM_WORKER_MULTIPROC_METHOD=spawn','PCC_CODE_COMMIT='+subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'.venv-infer/bin/python','-m','supplements.automated_evaluation_008.launch','--admission',remote_admission])
 write(ART/'owner_state.json',{'pid':os.getpid(),'status':'running','run_id':a['run_id'],'admission_sha256':sha(admission),'started_utc':now()})
 code=run_and_mirror(ssh+[target,cmd],ROOT,ART/(a['run_id']+'.log'))
 subprocess.run(['bash','scripts/sync.sh','pull'],cwd=ROOT,check=True)
 write(ART/'owner_state.json',{'pid':os.getpid(),'status':'completed' if not code else 'incomplete','run_id':a['run_id'],'ended_utc':now()})
 if code:raise RuntimeError('Stage failed; preserve mirrored evidence and costs; audit before any authorized retry')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--admission',type=Path,required=True);main(p.parse_args().admission.resolve())
