"""One pinned base model, original rollout, bounded dedicated reservation."""
import argparse,time,tarfile,importlib.metadata
from .common import *
def main(path):
 from pcc.config import RunConfig
 from pcc.resources import RunLedger,used_seconds
 from pcc.fast_backend import FastBackbone
 from pcc.evaluation import run_episodes
 from supplements.review_001.gpu import GuardedModel
 from .scenarios import all_scenarios
 a=read(path);verify(ROOT/a['freeze']);assert a['enabled']
 remaining=(datetime.fromisoformat(a['absolute_stop_utc'])-datetime.now(timezone.utc)).total_seconds();bound=min(a['maximum_seconds'],int(remaining)-15)
 assert bound>150 and used_seconds(ROOT/'artifacts/run_registry.jsonl')+a['remaining_obligations_seconds']+bound+1800<=345600
 cfg=RunConfig(model=a['model'],condition='base',seed=a['seed'],engine='vllm',structured_decoding=True,batch_size=64,max_run_seconds=bound,active_gpu_hours_ceiling=95.5,phase='generalization009')
 with RunLedger(ROOT/'artifacts',a['run_id'],cfg) as ledger:
  ledger.metadata.update(stage009=True,admission_sha256=sha(path),freeze_sha256=sha(ROOT/a['freeze']),task=a['task'],no_adapter=True,versions={p:importlib.metadata.version(p) for p in ('torch','vllm','transformers','tokenizers')})
  with tarfile.open(ledger.run_dir/'stage009_source.tar.gz','w:gz') as archive:
   for name in read(ROOT/a['freeze'])['files']:archive.add(ROOT/name,arcname=name)
   archive.add(path,arcname=str(path.relative_to(ROOT)))
  backend=FastBackbone(cfg,ledger,ROOT/'configs/models.json');assert backend.adapter is None
  model=GuardedModel(backend,ledger.start+bound)
  timings=[];scenarios=all_scenarios(a['task']=='profile')
  for condition in a['conditions']:
   start=time.monotonic();before=ledger.calls
   ledger.metadata.setdefault('condition_call_offsets',{})[condition]=before
   run_episodes(model,scenarios,condition,ledger.run_dir/(condition+'.jsonl'))
   timings.append({'condition':condition,'seconds':time.monotonic()-start,'calls':ledger.calls-before,'conversations':len(scenarios)})
  write(ledger.run_dir/'timing_only.json',{'load_seconds':ledger.metadata['model_load_seconds'],'timings':timings,'total_calls':ledger.calls,'classification':'Development profiling excluded from scientific estimates' if a['task']=='profile' else 'frozen research grid'})
  write(ledger.run_dir/'completion.json',{'completed':True,'conditions':a['conditions'],'conversations':len(scenarios)*len(a['conditions'])})
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--admission',required=True);main(Path(p.parse_args().admission))
