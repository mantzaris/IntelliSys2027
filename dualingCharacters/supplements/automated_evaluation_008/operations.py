"""Read-only owner, resource and mirror status. No scheduling or inference."""
import os,subprocess,shutil,shlex,time
from .common import *
from .gpu_worker import stage_seconds
from pcc.resources import used_seconds
from pcc.campaign import jobs,resolve_job,load_overrides
from pcc.freeze import verify_freeze
from analysis.overnight.monitor import forecast

def snapshot(remote=False):
 records={p.parent.name:read(p) for p in (ROOT/'artifacts/runs').glob('*/status.json')}
 queue=[resolve_job(j,load_overrides(ROOT)) for j in jobs(verify_freeze(ROOT)['plan'])];used=used_seconds(ROOT/'artifacts/run_registry.jsonl');active=[r for r in records.values() if r['status']=='running']
 upper=0
 for r in active:
  age=(datetime.now(timezone.utc)-datetime.fromisoformat(r['started_utc'].replace('Z','+00:00'))).total_seconds();upper+=max(0,age-r['gpu_reserved_seconds'])
 pred=forecast(queue,records,used+upper);rstate=read(ROOT/'artifacts/review_001/controller_state.json');owner=read(ART/'owner_state.json');core=read(ROOT/'artifacts/campaign_state.json')
 result={'utc':now(),'core_completed':sum(records.get(j['id'],{}).get('status')=='completed' for j in queue),'core_scheduled':len(queue),'core_state':core,'core_boundary_hold':(ROOT/'artifacts/campaign_boundary_hold.json').exists(),'stage008_owner':owner,'review_state':rstate,'global_reserved_seconds':used,'active_upper_unrecorded_seconds':upper,'stage008_reserved_seconds':stage_seconds(ROOT/'artifacts/run_registry.jsonl'),'compatibility_reserved_seconds':sum(r.get('gpu_reserved_seconds',0) for r in records.values() if r['run_id'].startswith('dialogue005-compat')),'review_reserved_seconds':sum(r.get('gpu_reserved_seconds',0) for r in records.values() if r['run_id'].startswith('review001-')),'forecast':{k:v for k,v in pred.items() if k!='pending'},'local_free_bytes':shutil.disk_usage(ROOT).free,'active_runs':[{k:r.get(k) for k in ['run_id','status','model_calls','gpu_reserved_seconds','input_tokens','output_tokens']} for r in active],'known_cost_usd':None,'pod_wall_time':'Not inferred from reserved execution or utilization; session wall time is recorded separately.'}
 if remote:
  from supplements.review_001.controller import connection
  os.environ.update(read(ART/'original_owner_private.json')['environment']);ssh,target,base=connection()
  script="import json,shutil,subprocess; print(json.dumps({'free_bytes':shutil.disk_usage('.').free,'gpu':subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.used,utilization.gpu','--format=csv,noheader'],text=True).strip(),'compute_pids':subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip()}))"
  result['remote']=json.loads(subprocess.check_output(ssh+[target,'cd '+shlex.quote(base)+' && python3 -c '+shlex.quote(script)],text=True))
 write(HERE/'reports/LATEST_OPERATIONAL_STATE.json',result)
 with (ART/'monitor.jsonl').open('a') as f:f.write(json.dumps(result)+'\n')
 print({k:result[k] for k in ['utc','core_completed','core_boundary_hold','global_reserved_seconds','stage008_reserved_seconds','compatibility_reserved_seconds','review_reserved_seconds','local_free_bytes','active_runs']});return result
if __name__=='__main__':
 import argparse;p=argparse.ArgumentParser();p.add_argument('--remote',action='store_true');a=p.parse_args();snapshot(a.remote)
