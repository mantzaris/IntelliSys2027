"""Restore the same native owner; does not create a new campaign/queue."""
import os,fcntl,subprocess,shlex,time
from .common import *
def main():
 from supplements.review_001.controller import connection
 old=read(ART/'original_owner_private.json');hold=ROOT/'artifacts/campaign_boundary_hold.json';h=read(hold);assert h['requested_by']=='generalization_edge_cases_009'
 assert not Path('/proc',str(old['pid'])).exists()
 owner=read(ART/'owner_state.json');assert owner['status'] in ('completed','failed') and not Path('/proc',str(owner['pid'])).exists()
 lock=(ROOT/'artifacts/campaign.lock').open('a+');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 os.environ.update(old['environment']);ssh,target,remote=connection()
 active=subprocess.check_output(ssh+[target,'nvidia-smi --query-compute-apps=pid --format=csv,noheader'],text=True).strip();assert not active,'GPU occupied; never interrupt it'
 assert read(hold)==h;write(ART/'completed_boundary_hold.json',h);hold.unlink();fcntl.flock(lock,fcntl.LOCK_UN);lock.close()
 command=old.get('command') or old.get('cmdline');assert any('pcc.campaign' in str(x) for x in command)
 log=(ART/'core_resume.log').open('ab');child=subprocess.Popen(command,cwd=old['cwd'],env=dict(os.environ),stdout=log,stderr=subprocess.STDOUT,start_new_session=True);log.close();time.sleep(2);assert child.poll() is None
 elapsed=(datetime.now(timezone.utc)-datetime.fromisoformat(read(ART/'handoff.json')['exclusive_start_utc'])).total_seconds()
 report={'utc':now(),'native_owner_pid':child.pid,'previous_pid':old['pid'],'same_command':True,'same_queue':True,'no_new_waiter':True,'no_stage009_inference_scheduled':True,'exclusive_handoff_seconds':elapsed,'under90minutes':elapsed<=5400,'log':'artifacts/generalization_edge_cases_009/core_resume.log'};write(HERE/'reports/CORE_RESUMPTION.json',report);print(report)
if __name__=='__main__':main()
