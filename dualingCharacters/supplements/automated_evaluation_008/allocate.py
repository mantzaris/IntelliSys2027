"""Development-timing allocation only. Must run before research outputs exist."""
from .common import *
from .analysis import calibration_metrics
from .gpu_worker import stage_seconds
from pcc.resources import used_seconds

def main():
 assert not (HERE/'SCIENTIFIC_FREEZE.json').exists(),'Preserve existing allocation'
 profiles={};consumed=stage_seconds(ROOT/'artifacts/run_registry.jsonl')
 for m in ['phi','qwen']:
  run=ROOT/'artifacts/runs'/f'auto008-development-final-{m}-v1';s=read(run/'status.json');assert s['status']=='completed'
  profiles[m]={'run_id':s['run_id'],'reserved_seconds':s['gpu_reserved_seconds'],'load_seconds':s['model_load_seconds'],'calls':s['model_calls'],'unique_controls':40,'seconds_per_control_including_repairs':(s['gpu_reserved_seconds']-s['model_load_seconds'])/40,'status_sha256':sha(run/'status.json')}
  write(HERE/f'reports/FINAL_DEVELOPMENT_{m.upper()}.json',calibration_metrics(read(HERE/'inputs/calibration.json'),[r for _,r in stream(run/'judgments.jsonl')],m,'development'))
 estimates={}
 for families in [30,15]:
  units=80+72+families*36
  estimates[str(families)]={'units_per_judge':units,'judge_seconds':sum(1.5*p['seconds_per_control_including_repairs']*(units+108+32)+3*p['load_seconds']+300 for p in profiles.values())}
  estimates[str(families)]['all_stage_seconds']=consumed+7200+estimates[str(families)]['judge_seconds']
 feasible=next(n for n in [30,15] if estimates[str(n)]['all_stage_seconds']<=14400)
 assert feasible==15,'Review fixed bounds if timing chooses a different prespecified tier, before any research call'
 broad=read(HERE/'inputs/broad15.json');fixed=read(HERE/'inputs/fixed72.json');held=[r for r in read(HERE/'inputs/calibration.json') if r['population']=='synthetic_holdout'];research=held+fixed+broad
 # Probe 6 in each condition/stratum, outcome-independent hash ranking.
 probes=[]
 for condition in ['C3','C5','A1']:
  for stratum in ['direct','communication']:
   eligible=[r for r in broad if r['private']['identity']['condition']==condition and r['private']['identity']['stratum']==stratum]
   probes+=sorted(eligible,key=lambda r:rank('auto008-probe:'+r['item_id']))[:6]
 assert len(probes)==36 and len(research)==692
 write(HERE/'inputs/research.json',research);write(HERE/'inputs/probes.json',probes)
 bounds={'research_phi':1000,'research_qwen':3600,'probes_phi':260,'probes_qwen':670,'compatibility':7200,'compatibility_judge_phi':200,'compatibility_judge_qwen':300}
 assert consumed+sum(bounds.values())<=14400
 allocation={'frozen_utc':now(),'basis':'Development-only measured wall reservation including repairs; 1.5 times per-control execution plus measured model loads and batch margins. No held-out/research labels viewed.','tier_families':15,'research_per_judge':692,'synthetic_holdout':80,'fixed_events':72,'broad_events':540,'probe_events':36,'probe_calls_per_judge':108,'compatibility_semantic_events':32,'compatibility_conversations':64,'bounds_seconds':bounds,'profiles':profiles,'candidate_estimates':estimates,'already_consumed_seconds':consumed,'total_worst_admitted_stage_seconds':consumed+sum(bounds.values()),'project_used_seconds_at_freeze':used_seconds(ROOT/'artifacts/run_registry.jsonl'),'remaining_obligations_seconds':36936,'contingency_seconds':1800,'stage_cap_seconds':14400,'inputs':{str(p.relative_to(ROOT)):sha(p) for p in [HERE/'inputs/research.json',HERE/'inputs/probes.json',HERE/'inputs/COMPATIBILITY_SEMANTIC_SELECTION.json']},'probe_items':[r['item_id'] for r in probes],'family_order':read(HERE/'inputs/BROAD_SELECTION.json')['family_order'][:15]}
 assert allocation['project_used_seconds_at_freeze']+36936+sum(bounds.values())+1800<=96*3600
 write(HERE/'ALLOCATION.json',allocation)
 bindings={'research':{m:f'auto008-research-{m}-v1' for m in ['phi','qwen']},'analysis':{m:[f'auto008-research-{m}-v1',f'auto008-probes-{m}-v1',f'auto008-compatibility-judge-{m}-v1'] for m in ['phi','qwen']}}
 write(HERE/'RUN_BINDINGS_FINAL.json',bindings)
 for m in ['phi','qwen']:
  for stage,inputfile,probeset in [('research','research.json',['base']),('probes','probes.json',['alias_permutation','category_order','api_exposed'])]:
   a=read(HERE/'admissions/development_final_phi.json');a.update(model=m,run_id=bindings['research'][m] if stage=='research' else f'auto008-probes-{m}-v1',inputs=f'supplements/automated_evaluation_008/inputs/{inputfile}',inputs_sha256=sha(HERE/'inputs'/inputfile),probes=probeset,maximum_seconds=bounds[stage+'_'+m],freeze='supplements/automated_evaluation_008/SCIENTIFIC_FREEZE.json');write(HERE/f'admissions/{stage}_{m}.json',a)
 a=read(HERE/'admissions/development_final_phi.json');a.update(task='compatibility',model='qwen',run_id='dialogue005-compat-17-v1',maximum_seconds=7200,freeze='supplements/automated_evaluation_008/SCIENTIFIC_FREEZE.json',budget_identity='dialogue005-compatibility');a.pop('inputs');a.pop('inputs_sha256');a.pop('probes');write(HERE/'admissions/compatibility.json',a)
 files=[HERE/n for n in ['common.py','judge_spec.py','judge_spec_final.py','calibration.py','gpu_worker.py','gpu_worker_final.py','launch.py','launch_final.py','owner.py','owner_final.py','sampling.py','analysis.py','semantic_analysis.py','controlled.py','allocate.py','PROTOCOL.md','AMENDMENT_008.md','PROMPT_REVISION_001.md','FINAL_PROTOCOL.md','ALLOCATION.json','RUN_BINDINGS_FINAL.json','JUDGE_SCHEMA_FINAL.json','inputs/research.json','inputs/probes.json','inputs/COMPATIBILITY_SEMANTIC_SELECTION.json','inputs/BROAD_SELECTION.json','inputs/calibration.json']]
 files +=[ROOT/'configs/models.json',ROOT/'supplements/evidence_validation_006/compatibility/FREEZE.json']
 freeze(HERE/'SCIENTIFIC_FREEZE.json',files,purpose='Final shared prompt, allocation and analyses before held-out/research/compatibility inference')
 print({k:allocation[k] for k in ['tier_families','already_consumed_seconds','total_worst_admitted_stage_seconds','candidate_estimates']})
if __name__=='__main__':main()
