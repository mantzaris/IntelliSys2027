from datetime import timedelta
from .common import *
def main():
 r=read(HERE/'reports/START_RESOURCES.json');old=read(ROOT/'supplements/automated_evaluation_008/tables/RESOURCES.json')
 margin=old.get('conservative_additional_unledgered_window_seconds',0)
 obligations=r['forecast']['conservative_remaining_core_hours']*3600+7200+margin
 files=[HERE/n for n in ['common.py','scenarios.py','worker.py','supervisor.py','owner.py','SESSION.json','inputs/development.json','inputs/scenarios.json']]+list((ROOT/'src/pcc').glob('*.py'))+[ROOT/'configs/models.json',ROOT/'supplements/review_001/gpu.py']
 write(HERE/'PROFILE_FREEZE.json',{'utc':now(),'purpose':'development throughput only; no research outcome allocation','files':{str(p.relative_to(ROOT)):sha(p) for p in files}})
 stop=datetime.fromisoformat(read(ART/'handoff.json')['exclusive_start_utc'])+timedelta(seconds=5340)
 for model in ['qwen','phi']:
  a={'enabled':True,'task':'profile','model':model,'seed':917,'conditions':['C3'],'run_id':f'edge009-profile-{model}-v1','freeze':str((HERE/'PROFILE_FREEZE.json').relative_to(ROOT)),'maximum_seconds':600,'absolute_stop_utc':stop.isoformat(),'remaining_obligations_seconds':obligations}
  write(HERE/'admissions'/f'profile-{model}.json',a)
 print({'obligations_hours':obligations/3600,'prior_window_margin':margin,'exclusive_stop':stop.isoformat()})
if __name__=='__main__':main()
