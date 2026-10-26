"""Reconcile every008attempt with raw generations; never infer billed pod cost."""
from .common import *
def main():
 rows=[]
 for p in sorted((ROOT/'artifacts/runs').glob('*/status.json')):
  if not (p.parent.name.startswith('auto008-') or p.parent.name=='dialogue005-compat-17-v1'):continue
  d=read(p);assert d['status']!='running','Wait until the stage ends before final accounting'
  r={k:d.get(k) for k in ['run_id','status','model_name','model_revision','model_calls','gpu_reserved_seconds','model_load_seconds','input_tokens','output_tokens','train_tokens','peak_vram_bytes','sampled_gpu_busy_seconds','utilization_weighted_seconds','known_cost_usd']};r.update(status_sha256=sha(p),source_type=d.get('source_type'))
  raw=p.parent/'judgments.jsonl'
  if raw.exists():
   records=[x for _,x in stream(raw)];gs=[x['generation'] for x in records if 'generation' in x]+[x['repair']['generation'] for x in records if x.get('repair')];r.update(task_records=len(records),repairs=sum(bool(x.get('repair')) for x in records),input_rejections=sum(x.get('status')=='input_rejected' for x in records),raw_sha256=sha(raw))
   r['unpersisted_generation_calls']=d['model_calls']-len(gs);assert r['unpersisted_generation_calls']>=0
   for name in ['input_tokens','output_tokens']:
    r['unpersisted_'+name]=d[name]-sum(g[name] for g in gs);assert r['unpersisted_'+name]>=0
   if d['status']=='completed':
    assert r['unpersisted_generation_calls']==0,p
    assert r['unpersisted_input_tokens']==r['unpersisted_output_tokens']==0,p
  elif d['status']=='completed':assert d['model_calls']==2816 and read(p.parent/'completion.json')['fixed_grid_complete']
  else:assert d['model_calls']==0,'Unrecorded model calls must be investigated'
  assert d.get('train_tokens',0)==0;rows.append(r)
 totals={name:sum(r.get(name) or 0 for r in rows) for name in ['model_calls','gpu_reserved_seconds','model_load_seconds','input_tokens','output_tokens','sampled_gpu_busy_seconds','utilization_weighted_seconds','task_records','repairs','input_rejections']}
 total=totals['gpu_reserved_seconds'];compat=sum(r['gpu_reserved_seconds'] for r in rows if r['run_id']=='dialogue005-compat-17-v1');assert total<=14400 and compat<=7200
 report={'as_of_utc':now(),'runs':rows,'totals':totals,'stage_hours':total/3600,'compatibility_hours':compat/3600,'cap_hours':4,'compatibility_cap_hours':2,'peak_vram_bytes':max(r.get('peak_vram_bytes') or 0 for r in rows),'no_training':True,'no_paid_apis':True,'human_annotations':0,'pod_billed_hours':None,'actual_dollar_cost':None,'qualification':'Reserved GPU wall time includes loading, calibration, failures, repair and execution. Sampled activity and weighted utilization differ from reservation and billed pod uptime. Existing pod rate/start billing data are unavailable. The ongoing core is accounted separately.'}
 if (HERE/'reports/CORE_RESUMPTION.json').exists():
  ended=datetime.fromisoformat(read(HERE/'reports/CORE_RESUMPTION.json')['utc']);cutoff=read(HERE/'inputs/CORE_CUTOFF.json');last=next(x['metadata'] for x in cutoff['jobs'] if x['job']['id']=='main-qwen-c6-43-r1-fit');start=datetime.fromisoformat(last['started_utc'].replace('Z','+00:00')).timestamp()+last['gpu_reserved_seconds'];window=ended.timestamp()-start
  assert max(window,total)<=14400,'Even the conservative full handoff window must fit the stage cap'
  report.update(exclusive_handoff_window_seconds=window,exclusive_handoff_window_hours=window/3600,exclusive_window_qualification='Conservative wall interval from the last core fit ending to native-owner resumption, including dispatch/mirroring/CPU gaps. Separate from native RunLedger reservations and billed pod uptime.',conservative_additional_unledgered_window_seconds=max(0,window-total))
 write(HERE/'tables/RESOURCES.json',report);csv_write(HERE/'tables/RESOURCE_RUNS.csv',rows);print({k:v for k,v in report.items() if k not in ['runs','qualification']})
if __name__=='__main__':main()
