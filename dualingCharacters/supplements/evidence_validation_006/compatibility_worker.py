"""GPU worker executable only after an existing-owner admission and exclusive lock.
Do not call directly: compatibility_launch supplies the bound and timeout.
"""
import os,time,json,tarfile,importlib.metadata,argparse
from .common import *
from .compatibility_design import load_scenarios,dry_run,IDENTITY,REVISION
from .compatibility_gate import verify_freeze,prerequisites,check_admission,extension_seconds

def main(admission_path):
 from pcc.config import RunConfig
 from pcc.resources import RunLedger,used_seconds
 request=read(admission_path);frozen=verify_freeze();doc=read(HERE/'compatibility/DESIGN.json');dry_run(doc)
 if os.environ.get('PCC_COMPATIBILITY_OWNER_TOKEN')!=request.get('owner_dispatch_id'):raise PermissionError('Use existing-owner supervised launch')
 core,review=prerequisites();gate=check_admission(request,datetime.now(timezone.utc),used_seconds(ROOT/'artifacts/run_registry.jsonl'),extension_seconds(ROOT/'artifacts/run_registry.jsonl'),core,review)
 cfg=RunConfig(model='qwen',condition='C5',seed=17,phase='dialogue005_compatibility_exploratory',active_gpu_hours_ceiling=95.5,max_run_seconds=gate['worker_seconds'],**doc['config'])
 with RunLedger(ROOT/'artifacts',doc['run_id'],cfg) as ledger:
  ledger.metadata.update(budget_identity=IDENTITY,compatibility_freeze_sha256=sha(HERE/'compatibility/FREEZE.json'),admission_sha256=sha(admission_path),owner_dispatch_id=request['owner_dispatch_id'])
  ledger.heartbeat();expected={'vllm':'0.10.2','transformers':'4.56.2','tokenizers':'0.22.2','huggingface-hub':'0.35.3','xgrammar':'0.1.23'}
  versions={p:importlib.metadata.version(p) for p in expected};assert versions==expected
  ledger.metadata['inference_versions']=versions
  with tarfile.open(ledger.run_dir/'compatibility_source.tar.gz','w:gz') as archive:
   for rel in frozen['files']:archive.add(ROOT/rel,arcname=rel)
   archive.add(HERE/'compatibility/FREEZE.json',arcname='compatibility/FREEZE.json')
   archive.add(admission_path,arcname='operational_admission.json')
  # Backend import/loading is below all scientific, resource and ownership checks.
  from pcc.fast_backend import FastBackbone
  from supplements.review_001.gpu import GuardedModel
  from .compatibility_rollout import run
  backend=FastBackbone(cfg,ledger,ROOT/'configs/models.json');assert ledger.metadata['model_revision']==REVISION
  assert backend.adapter is None
  model=GuardedModel(backend,ledger.start+gate['worker_seconds']);ss=load_scenarios(doc)
  order={n:i for i,n in enumerate(doc['family_order'])};ss.sort(key=lambda s:(order[int(s.family_id.split('-')[-1])],s.world!='authorized'))
  for arm in doc['arms']:
   ledger.metadata.setdefault('arm_call_offsets',{})[arm]=ledger.calls
   summary=run(model,ss,arm,ledger.run_dir/(arm+'.jsonl'))
   assert len(summary)==32 and len({(r['family_id'],r['world']) for r in summary})==32
  assert ledger.calls==2816
  write(ledger.run_dir/'completion.json',{'fixed_grid_complete':True,'conversations':64,'calls':ledger.calls,'all_arms_worlds_families_complete':True})
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--admission',required=True);main(Path(p.parse_args().admission))
