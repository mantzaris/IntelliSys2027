"""Lock completed core populations; reuse frozen paired statistics without rewriting originals."""
from collections import defaultdict
from .common import *
from pcc.analysis import paired_success,contrast,holm
from pcc.study_analysis import family_signflip_p
from pcc.freeze import verify_freeze
from pcc.campaign import jobs,resolve_job,load_overrides
from pcc.eligibility import exclusions

def snapshot():
 f=verify_freeze(ROOT);excluded=exclusions(ROOT);queue=[resolve_job(j,load_overrides(ROOT)) for j in jobs(f['plan'])];records=[]
 for j in queue:
  path=ROOT/'artifacts/runs'/j['id']/'status.json';state=read(path) if path.exists() else None
  paths={'status':str(path.relative_to(ROOT))};bound={paths['status']:sha(path)} if state else {}
  run=path.parent
  for p in run.glob('*summary.json'):
   paths[p.name]=str(p.relative_to(ROOT));bound[str(p.relative_to(ROOT))]=sha(p)
  records.append({'job':j,'status':state['status'] if state else 'not_started','eligible':bool(state and state['status']=='completed' and j['id'] not in excluded),'exclusion':excluded.get(j['id']),'metadata':state,'paths':paths,'hashes':bound})
 target=HERE/'inputs/CORE_CUTOFF.json';assert not target.exists(),'Cutoff immutable; later completions get separate operational appendix'
 write(target,{'cutoff_utc':now(),'core_freeze_sha256':sha(ROOT/'configs/freeze.json'),'exclusions_sha256':sha(ROOT/'configs/run_exclusions.json'),'jobs':records,'excluded_history':excluded})
 print('Core cutoff:',sum(r['eligible'] for r in records),'completed eligible stages')

def run():
 d=read(HERE/'inputs/CORE_CUTOFF.json');groups=defaultdict(list);counts=[];allrows=[];trace=[];missing=[];specs=read(ROOT/'configs/models.json')
 for rec in d['jobs']:
  j=rec['job'];s=rec['metadata']
  if not rec['eligible']:missing.append({'run_id':j['id'],'model':j['model'],'condition':j['condition'],'seed':j['seed'],'task':j['command'],'status':rec['status'],'exclusion':rec['exclusion']});continue
  # Bind every summary used; status may evolve only for active runs, excluded above.
  for p,h in rec['hashes'].items():assert sha(ROOT/p)==h,p
  assert s['model_revision']==specs[j['model']]['revision']
  if j['command']!='evaluate':continue
  path=ROOT/rec['paths']['evaluation_summary.json'];rows=read(path);assert len(rows)==480
  keys={(r['family_id'],r['world']) for r in rows};assert len(keys)==480
  assert all(r['seed']==j['seed'] for r in rows)
  pairs=paired_success(rows);assert len(pairs)==240
  if j.get('adapter'):assert sha(ROOT/j['adapter']/'adapter_model.safetensors')==s['loaded_adapter_sha256']
  for name in ['environment','evaluation','memory','schemas','backend','fast_backend','config']:
   p=f'src/pcc/{name}.py';assert s['source_hashes'][p]==sha(ROOT/p)
  groups[j['model'],j['condition']]+=rows
  counts.append({'model':j['model'],'condition':j['condition'],'seed':j['seed'],'run_id':j['id'],'paired_successes':sum(pairs.values()),'paired_families':240,'conversation_successes':sum(r['success'] for r in rows),'conversations':480,'summary_sha256':sha(path),'checkpoint_sha256':s.get('loaded_adapter_sha256'),'status':'completed eligible at cutoff'})
  allrows += [{**r,'model':j['model'],'condition':j['condition'],'evaluation_condition':r.get('condition')} for r in rows]
  trace.append({'run_id':j['id'],'summary_path':str(path.relative_to(ROOT)),'summary_sha256':sha(path),'status_sha256':rec['hashes'][rec['paths']['status']],'adapter_sha256':s.get('loaded_adapter_sha256'),'code_commit':s['code_commit'],'model_revision':s['model_revision'],'dataset_hash':s.get('dataset_hash')})
 contrasts=[];transitions=[]
 for model in ['qwen','phi']:
  conds=['C1','C2','C3','C4','C5','C6','A1','A2','A3'] if model=='qwen' else ['C1','C3','C5'];pvalues={}
  for c in conds:
   if c=='C5':continue
   a=groups[model,'C5'];b=groups[model,c];seeds=sorted({r['seed'] for r in a}&{r['seed'] for r in b})
   if not seeds:continue
   aa=[r for r in a if r['seed'] in seeds];bb=[r for r in b if r['seed'] in seeds];value=contrast(aa,bb);p=family_signflip_p(aa,bb)
   contrasts.append({'model':model,'comparison':'C5-'+c,'matched_seeds':seeds,'planned_three_seed_complete':len(seeds)==3,**value,'p_conditional_family':p,'holm_secondary':None})
   if c!='C3':pvalues[c]=p if len(seeds)==3 else 1.
   pa,pb=paired_success(aa),paired_success(bb)
   for seed in seeds:
    pairs=[(pa[seed,f],pb[seed,f]) for s,f in pa if s==seed]
    transitions.append({'model':model,'comparison':'C5-'+c,'seed':seed,'families':len(pairs),'both':sum(a and b for a,b in pairs),'C5_only':sum(a and not b for a,b in pairs),'control_only':sum(not a and b for a,b in pairs),'neither':sum(not a and not b for a,b in pairs)})
  adjusted=holm({c:pvalues.get(c,1.) for c in conds if c not in ['C5','C3']})
  for r in contrasts:
   if r['model']==model and r['planned_three_seed_complete']:r['holm_secondary']=adjusted.get(r['comparison'].split('-')[1])
 write(HERE/'tables/CORE_COUNTS.json',counts);csv_write(HERE/'tables/CORE_COUNTS.csv',counts);write(HERE/'tables/CORE_CONTRASTS.json',contrasts);csv_write(HERE/'tables/CORE_TRANSITIONS.csv',transitions);write(HERE/'tables/CORE_PROVENANCE.json',trace);csv_write(HERE/'tables/CORE_PENDING.csv',missing)
 # Compact family/world sufficient outcomes, no prompts or synthetic controls.
 write(HERE/'inputs/core_summary_outcomes.json',allrows)
 print('Core summary rows',len(counts),'contrasts',len(contrasts),'pending',len(missing))
if __name__=='__main__':
 import argparse;p=argparse.ArgumentParser();p.add_argument('--snapshot',action='store_true');a=p.parse_args();snapshot() if a.snapshot else run()
