"""Timing-only tier selection. Does not read development labels or research outputs."""
from datetime import timedelta
import math
from .common import *
def main():
 session=read(HERE/'SESSION.json');start=datetime.fromisoformat(read(ART/'handoff.json')['exclusive_start_utc']);elapsed=(datetime.now(timezone.utc)-start).total_seconds()
 timings={m:read(ROOT/'artifacts/runs'/f'edge009-profile-{m}-v1'/'timing_only.json') for m in ('qwen','phi')}
 bounds={m:math.ceil(t['timings'][0]['seconds']/8*96*1.5+t['load_seconds']+90) for m,t in timings.items()}
 sequence=[('qwen',17,['C3','C5','A1']),('phi',17,['A1','C5','C3']),('qwen',29,['C5','A1','C3']),('phi',29,['C3','A1','C5'])]
 choices=[('full',sequence),('reduced',sequence[:2]),('minimum',sequence[:1])];estimates=[];chosen=None
 for name,queue in choices:
  total=sum(bounds[m] for m,s,c in queue);fits=elapsed+total+180<5400 and datetime.now(timezone.utc).timestamp()+total+180<datetime.fromisoformat(session['inference_cutoff_utc']).timestamp()
  estimates.append({'tier':name,'future_bound_seconds':total,'elapsed_exclusive_seconds':elapsed,'fits':fits})
  if fits and chosen is None:chosen=(name,queue)
 assert chosen,'No complete tier fits: restore native owner without research inference'
 assert datetime.now(timezone.utc)<datetime.fromisoformat(session['profile_deadline_utc'])
 obligations=read(HERE/'admissions/profile-qwen.json')['remaining_obligations_seconds'];stop=min(start+timedelta(seconds=5340),datetime.fromisoformat(session['inference_cutoff_utc']))
 jobs=[]
 for model,seed,conditions in chosen[1]:
  jobs.append({'enabled':True,'task':'research','model':model,'seed':seed,'conditions':conditions,'run_id':f'edge009-{model}-{seed}-v1','maximum_seconds':bounds[model],'absolute_stop_utc':stop.isoformat(),'remaining_obligations_seconds':obligations,'freeze':str((HERE/'SCIENTIFIC_FREEZE.json').relative_to(ROOT))})
 doc={'frozen_utc':now(),'tier':chosen[0],'basis':'Development timings only; no scores read. 1.5x per-conversation time plus measured model loading and90seconds per block;180seconds restoration margin.','profile_timings':timings,'candidates':estimates,'jobs':jobs,'models':list(dict.fromkeys(j['model'] for j in jobs)),'seeds':list(dict.fromkeys(j['seed'] for j in jobs)),'planned_conversations':len(jobs)*96,'planned_generation_calls':len(jobs)*4224,'families':16,'conditions':['C3','C5','A1'],'examples':{}}
 from .scenarios import all_scenarios,PATTERNS,metadata
 for pattern in PATTERNS:
  ids=sorted({s.family_id for s in all_scenarios() if metadata(s)['pattern']==pattern},key=lambda x:hashlib.sha256(('edge009-example:'+x).encode()).hexdigest());doc['examples'][pattern]=ids[0]
 write(HERE/'ALLOCATION.json',doc)
 files=[HERE/n for n in ['common.py','scenarios.py','worker.py','supervisor.py','owner.py','analysis.py','allocate.py','SESSION.json','PROTOCOL.md','ALLOCATION.json','inputs/scenarios.json','inputs/OVERLAP.json']]+list((HERE/'tests').glob('*.py'))+list((ROOT/'src/pcc').glob('*.py'))+[ROOT/'configs/models.json',ROOT/'supplements/review_001/gpu.py']
 write(HERE/'SCIENTIFIC_FREEZE.json',{'frozen_utc':now(),'known_outcomes':'Earlier core and stages003-008 known; no stage009 research generated, only development timings inspected.','files':{str(p.relative_to(ROOT)):sha(p) for p in files}})
 for job in jobs:write(HERE/'admissions'/f"{job['model']}-{job['seed']}.json",job)
 print({'tier':chosen[0],'bounds':bounds,'candidates':estimates,'conversations':doc['planned_conversations']})
if __name__=='__main__':main()
