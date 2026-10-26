"""Foreground exclusive owner, native locks and mirror, no automatic retry/waiter."""
import argparse,fcntl,os,shlex,subprocess,tarfile
from .common import *
def main(path):
 from pcc.resources import used_seconds
 from pcc.campaign import run_and_mirror
 from supplements.review_001.controller import connection
 a=read(path);verify(ROOT/a['freeze']);assert a['enabled']
 assert read(ROOT/'artifacts/campaign_boundary_hold.json')['requested_by']=='generalization_edge_cases_009'
 owner=(ROOT/'artifacts/campaign.lock').open('a+');fcntl.flock(owner,fcntl.LOCK_EX|fcntl.LOCK_NB)
 old=read(ART/'original_owner_private.json');assert not Path('/proc',str(old['pid'])).exists()
 elapsed=(datetime.now(timezone.utc)-datetime.fromisoformat(read(ART/'handoff.json')['exclusive_start_utc'])).total_seconds()
 assert elapsed+a['maximum_seconds']+60<=5400,'Exclusive handoff cap including restore margin'
 assert datetime.now(timezone.utc).timestamp()+a['maximum_seconds']<datetime.fromisoformat(a['absolute_stop_utc']).timestamp()
 assert used_seconds(ROOT/'artifacts/run_registry.jsonl')+a['remaining_obligations_seconds']+5400+1800<=345600
 os.environ.update(old['environment']);ssh,target,remote=connection()
 files={ROOT/n for n in read(ROOT/a['freeze'])['files']}|{ROOT/a['freeze'],path}
 bundle=ART/'dispatch.tar.gz'
 with tarfile.open(bundle,'w:gz') as arc:
  for f in sorted(files):arc.add(f,arcname=str(f.relative_to(ROOT)))
 subprocess.run(['rsync','-az','-e',shlex.join(ssh),str(bundle),target+':'+remote+'/artifacts/edge009_dispatch.tar.gz'],check=True)
 subprocess.run(ssh+[target,'cd '+shlex.quote(remote)+' && tar -xzf artifacts/edge009_dispatch.tar.gz'],check=True)
 cmd='cd '+shlex.quote(remote)+' && '+shlex.join(['env','PYTHONPATH=src:.','HF_HOME='+remote+'/artifacts/hf-cache','HF_HUB_OFFLINE=1','VLLM_WORKER_MULTIPROC_METHOD=spawn','PCC_CODE_COMMIT='+read(HERE/'SESSION.json')['input_commit'],'.venv-infer/bin/python','-m','supplements.generalization_edge_cases_009.replay_supervisor','--admission',remote+'/'+str(path.relative_to(ROOT))])
 write(ART/'owner_state.json',{'pid':os.getpid(),'status':'running','run_id':a['run_id'],'started_utc':now()})
 code=run_and_mirror(ssh+[target,cmd],ROOT,ART/(a['run_id']+'.log'))
 subprocess.run(['bash','scripts/sync.sh','pull'],cwd=ROOT,check=True)
 write(ART/'owner_state.json',{'pid':os.getpid(),'status':'completed' if code==0 else 'failed','run_id':a['run_id'],'ended_utc':now()})
 if code:raise SystemExit(code)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--admission',required=True);main(Path(p.parse_args().admission).resolve())
