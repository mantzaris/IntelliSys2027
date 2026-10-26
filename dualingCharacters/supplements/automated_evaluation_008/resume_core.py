"""Return the GPU to the original native campaign after all008owners exit; no new queue."""
import os,fcntl,subprocess,shlex,time
from .common import *

def main():
 from supplements.review_001.controller import connection
 old=read(ART/'original_owner_private.json');hold=ROOT/'artifacts/campaign_boundary_hold.json';h=read(hold);assert h.get('requested_by')=='automated_evaluation_008'
 assert not Path('/proc',str(old['pid'])).exists(),'Original process still exists'
 owner=read(ART/'owner_state.json');assert owner['status']=='completed','Last008owner not complete'
 required=['dialogue005-compat-17-v1']+[f'auto008-{stage}-{model}-v1' for stage in ['probes','compatibility-judge'] for model in ['phi','qwen']]
 binding=read(HERE/('RUN_BINDINGS_COMPLETE.json' if (HERE/'RUN_BINDINGS_COMPLETE.json').exists() else 'RUN_BINDINGS_FINAL.json'))
 for model in ['phi','qwen']:
  research=binding.get('research_sources',{}).get(model,[binding['research'][model]]);seen=[]
  for run in research:seen += [r['item_id'] for _,r in stream(ROOT/'artifacts/runs'/run/'judgments.jsonl')]
  assert len(seen)==len(set(seen))==692 and set(seen)=={r['item_id'] for r in read(HERE/'inputs/research.json')},'Research coverage incomplete'
  assert read(ROOT/'artifacts/runs'/research[-1]/'status.json')['status']=='completed'
 for name in required:assert read(ROOT/'artifacts/runs'/name/'status.json')['status']=='completed',name
 last=next(r['metadata'] for r in read(HERE/'inputs/CORE_CUTOFF.json')['jobs'] if r['job']['id']=='main-qwen-c6-43-r1-fit')
 end_fit=datetime.fromisoformat(last['started_utc'].replace('Z','+00:00')).timestamp()+last['gpu_reserved_seconds']
 conservative_handoff_elapsed=datetime.now(timezone.utc).timestamp()-end_fit
 lock=(ROOT/'artifacts/campaign.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 os.environ.update(old['environment']);ssh,target,remote=connection()
 active=subprocess.check_output(ssh+[target,'nvidia-smi --query-compute-apps=pid --format=csv,noheader'],text=True).strip();assert not active,'GPU is occupied; do not interrupt it'
 # Archive only this explicitly owned operational request; do not remove others.
 assert read(hold)==h;archive=ART/'completed_boundary_hold.json';assert not archive.exists();write(archive,h);hold.unlink()
 fcntl.flock(lock,fcntl.LOCK_UN);lock.close()
 command=old.get('command') or old.get('cmdline');assert isinstance(command,list) and any('pcc.campaign' in str(x) for x in command)
 log=(ART/'core_resume.log').open('ab');child=subprocess.Popen(command,cwd=old['cwd'],env=dict(os.environ),stdout=log,stderr=subprocess.STDOUT,start_new_session=True);log.close();time.sleep(2);assert child.poll() is None,'Native owner exited immediately; inspect private log'
 report={'utc':now(),'native_owner_pid':child.pid,'prior_owner_pid':old['pid'],'same_command':True,'recorded_connection_environment_restored':True,'environment_note':'Recorded owner variables restored over the current process environment; no secret values are reported.','healthy_gpu_not_interrupted':True,'unchanged_queue':True,'next_stage_at_handoff':'main-qwen-c6-43-eval','log':'artifacts/automated_evaluation_008/core_resume.log','hold_archived':'artifacts/automated_evaluation_008/completed_boundary_hold.json','no_new_waiter':True,'conservative_handoff_seconds_before_resume':conservative_handoff_elapsed,'conservative_handoff_under_four_hours':conservative_handoff_elapsed<14400};write(HERE/'reports/CORE_RESUMPTION.json',report);print(report)
if __name__=='__main__':main()
