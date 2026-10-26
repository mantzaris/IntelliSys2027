from datetime import timedelta
from .common import *
def main():
 a=read(HERE/'ALLOCATION.json');assert all(read(ROOT/'artifacts/runs'/j['run_id']/'status.json')['status']=='completed' for j in a['jobs'])
 from .replay import select
 selected=select();session=read(HERE/'SESSION.json');current=datetime.now(timezone.utc);end=datetime.fromisoformat(read(ART/'handoff.json')['exclusive_start_utc'])+timedelta(seconds=5340)
 assert (datetime.fromisoformat(session['inference_cutoff_utc'])-current).total_seconds()>=900
 assert selected and (end-current).total_seconds()>420
 files=[HERE/n for n in ['common.py','scenarios.py','replay.py','replay_worker.py','replay_supervisor.py','replay_owner.py','OPTIONAL_REPLAY_PROTOCOL.md','ALLOCATION.json','inputs/replay.json','reports/REPLAY_SELECTION.json']]+list((ROOT/'src/pcc').glob('*.py'))+[ROOT/'configs/models.json',ROOT/'supplements/review_001/gpu.py']
 write(HERE/'REPLAY_FREEZE.json',{'utc':now(),'classification':'Optional immediate availability intervention after completed main grid; independently analyzed.','files':{str(p.relative_to(ROOT)):sha(p) for p in files}})
 job={'enabled':True,'task':'replay','model':'qwen','seed':17,'run_id':'edge009-delivery-replay-v1','maximum_seconds':300,'absolute_stop_utc':end.isoformat(),'remaining_obligations_seconds':a['jobs'][0]['remaining_obligations_seconds'],'freeze':str((HERE/'REPLAY_FREEZE.json').relative_to(ROOT))}
 write(HERE/'admissions/replay.json',job);write(HERE/'REPLAY_BINDING.json',{'run_id':job['run_id'],'states':len(selected),'planned_calls':4*len(selected),'seeds':[17,29],'admitted_utc':now()});print({'states':len(selected),'calls':len(selected)*4,'exact_baseline_prompt_equality':True})
if __name__=='__main__':main()
