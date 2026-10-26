"""Read-only resource forecast; no writes to historical packages."""
import shutil
from .common import *
def snapshot():
 from pcc.resources import used_seconds
 from pcc.campaign import jobs,resolve_job,load_overrides
 from pcc.freeze import verify_freeze
 from analysis.overnight.monitor import forecast
 records={p.parent.name:read(p) for p in (ROOT/'artifacts/runs').glob('*/status.json')}
 queue=[resolve_job(j,load_overrides(ROOT)) for j in jobs(verify_freeze(ROOT)['plan'])]
 used=used_seconds(ROOT/'artifacts/run_registry.jsonl');pred=forecast(queue,records,used)
 r={'utc':now(),'completed':sum(records.get(j['id'],{}).get('status')=='completed' for j in queue),'total':len(queue),'recorded_seconds':used,'forecast':pred,'review_reserved_obligation_seconds':7200,'contingency_seconds':1800,'new_max_seconds':5400,'local_free_bytes':shutil.disk_usage(ROOT).free,'active_records':[n for n,v in records.items() if v['status']=='running']}
 r['conservative_total_hours']=(used+pred['conservative_remaining_core_hours']*3600+7200+5400+1800)/3600
 assert r['conservative_total_hours']<=96,r
 write(HERE/'reports/START_RESOURCES.json',r);print({k:v for k,v in r.items() if k!='forecast'});return r
if __name__=='__main__':snapshot()
