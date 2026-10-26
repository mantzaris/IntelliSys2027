"""One base-model judge or unchanged compatibility rollout, under existing GPU ledger."""
import argparse,time,os,tarfile,copy
from .common import *

def stage_seconds(registry):
 rows={r['run_id']:r for _,r in stream(registry)} if Path(registry).exists() else {}
 return sum(float(r.get('gpu_reserved_seconds',0)) for r in rows.values() if r.get('stage008') or r['run_id'].startswith('auto008-') or r.get('budget_identity')=='dialogue005-compatibility')

def main(admission_path):
 from pcc.config import RunConfig
 from pcc.resources import RunLedger,used_seconds,append_json
 from supplements.evidence_validation_006.compatibility_gate import extension_seconds
 a=read(admission_path);verify(ROOT/a['freeze']);assert a['enabled'] and os.environ.get('AUTO008_OWNER_TOKEN')==a['dispatch_id']
 remaining=(datetime.fromisoformat(a['cutoff_utc'])-datetime.now(timezone.utc)).total_seconds()
 bound=a['maximum_seconds'];used=used_seconds(ROOT/'artifacts/run_registry.jsonl');already=stage_seconds(ROOT/'artifacts/run_registry.jsonl')
 assert remaining>=bound and already+bound<=14400 and used+a['remaining_obligations_seconds']+bound+1800<=96*3600,'Admission resource gate'
 compat=a['task']=='compatibility'
 if compat:assert extension_seconds(ROOT/'artifacts/run_registry.jsonl')+bound<=7200
 config={'model':a['model'],'condition':'base','seed':800017,'engine':'vllm','precision':'bf16','phase':'automated008_exploratory','batch_size':32,'max_input_tokens':8192,'answer_tokens':768,'structured_decoding':True,'active_gpu_hours_ceiling':95.5,'max_run_seconds':bound-30}
 if compat:
  from supplements.evidence_validation_006.compatibility_gate import verify_freeze
  from supplements.evidence_validation_006.compatibility_design import load_scenarios,IDENTITY
  cf=verify_freeze();design=read(ROOT/'supplements/evidence_validation_006/compatibility/DESIGN.json')
  config.update(design['config']);config.update(model='qwen',condition='C5',seed=17,max_run_seconds=bound-30)
 cfg=RunConfig(**config)
 with RunLedger(ROOT/'artifacts',a['run_id'],cfg) as ledger:
  ledger.metadata.update(stage008=True,source_type='automated_model' if not compat else 'controlled_experiment',owner_dispatch_id=a['dispatch_id'],admission_sha256=sha(admission_path),freeze_sha256=sha(ROOT/a['freeze']),no_adapter=True)
  if compat:ledger.metadata['budget_identity']='dialogue005-compatibility'
  ledger.heartbeat()
  from pcc.fast_backend import FastBackbone
  from supplements.review_001.gpu import GuardedModel
  backend=FastBackbone(cfg,ledger,ROOT/'configs/models.json');assert backend.adapter is None
  if compat:
   from supplements.evidence_validation_006.compatibility_rollout import run
   model=GuardedModel(backend,ledger.start+bound-30);ss=load_scenarios(design);order={n:i for i,n in enumerate(design['family_order'])};ss.sort(key=lambda s:(order[int(s.family_id.split('-')[-1])],s.world!='authorized'))
   for arm in design['arms']:
    ledger.metadata.setdefault('arm_call_offsets',{})[arm]=ledger.calls
    summary=run(model,ss,arm,ledger.run_dir/(arm+'.jsonl'));assert len(summary)==32
   assert ledger.calls==2816;write(ledger.run_dir/'completion.json',{'fixed_grid_complete':True,'conversations':64,'calls':ledger.calls});return
  from .judge_spec import prompt,judgment_schema,validate
  items=read(ROOT/a['inputs']);assert sha(ROOT/a['inputs'])==a['inputs_sha256']
  tasks=[(item,probe) for item in items for probe in a['probes']]
  write(ledger.run_dir/'input_manifest.json',{'inputs':a['inputs'],'sha256':a['inputs_sha256'],'items':len(items),'tasks':len(tasks),'probes':a['probes']})
  for start in range(0,len(tasks),cfg.batch_size):
   batch=tasks[start:start+cfg.batch_size];valid_batch=[];prompts=[]
   for item,probe in batch:
    convo=prompt(item,probe)
    try:backend.prompt_ids(convo)
    except ValueError as error:
     append_json(ledger.run_dir/'judgments.jsonl',{'item_id':item['item_id'],'probe':probe,'source_type':'automated_model','status':'input_rejected','error':str(error)});continue
    valid_batch.append((item,probe));prompts.append(convo)
   if time.monotonic()+90>ledger.start+bound-30:raise TimeoutError('Stop before new batch; preserve partial results')
   outputs=backend.generate(prompts,768,frozen=True,response_schema=judgment_schema())
   for (item,probe),convo,g in zip(valid_batch,prompts,outputs):
    check=validate(g['parsed'],item,probe);row={'item_id':item['item_id'],'probe':probe,'source_type':'automated_model','model':a['model'],'model_revision':ledger.metadata['model_revision'],'population':item['population'],'prompt':convo,'generation':g,'validation':check,'repair':None}
    if not check['format_valid']:
     if time.monotonic()+90>ledger.start+bound-30:raise TimeoutError('No format-repair time remains')
     repair=convo+[{'role':'assistant','content':g['raw']},{'role':'user','content':'Format-only repair: return the requested JSON schema. Preserve your semantic decisions; do not reconsider the evidence. No extra prose.'}]
     rg=backend.generate([repair],768,frozen=True,response_schema=judgment_schema())[0];row['repair']={'prompt':repair,'generation':rg};row['validation']=validate(rg['parsed'],item,probe);row['final_parsed']=rg['parsed']
    else:row['final_parsed']=g['parsed']
    append_json(ledger.run_dir/'judgments.jsonl',row)
   print(json.dumps({'completed_tasks':min(start+cfg.batch_size,len(tasks)),'total_tasks':len(tasks),'calls':ledger.calls}),flush=True)
  write(ledger.run_dir/'completion.json',{'tasks':len(tasks),'model_calls':ledger.calls,'complete':True})
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--admission',required=True);main(Path(p.parse_args().admission))
