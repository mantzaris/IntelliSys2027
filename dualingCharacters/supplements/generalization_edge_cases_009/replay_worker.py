import argparse,time
from dataclasses import replace
from .common import *
def main(path):
 from pcc.resources import RunLedger,append_json,used_seconds
 from pcc.config import RunConfig
 from pcc.fast_backend import FastBackbone
 from supplements.review_001.gpu import GuardedModel
 a=read(path);verify(ROOT/a['freeze']);assert a['enabled']
 remaining=(datetime.fromisoformat(a['absolute_stop_utc'])-datetime.now(timezone.utc)).total_seconds();bound=min(a['maximum_seconds'],int(remaining)-15);assert bound>150
 assert used_seconds(ROOT/'artifacts/run_registry.jsonl')+a['remaining_obligations_seconds']+bound+1800<=345600
 cfg=RunConfig(model='qwen',condition='base',seed=17,engine='vllm',structured_decoding=True,batch_size=64,max_run_seconds=bound,active_gpu_hours_ceiling=95.5,phase='generalization009_replay')
 items=read(HERE/'inputs/replay.json');assert 0<len(items)<=16
 with RunLedger(ROOT/'artifacts',a['run_id'],cfg) as ledger:
  ledger.metadata.update(stage009=True,task='optional_delivery_replay',freeze_sha256=sha(ROOT/a['freeze']),no_adapter=True)
  backend=FastBackbone(cfg,ledger,ROOT/'configs/models.json');model=GuardedModel(backend,ledger.start+bound)
  for seed in [17,29]:
   # Backend computes batch seed as config.seed+ledger.calls. Bind effective seed exactly.
   backend.config=replace(cfg,seed=seed-ledger.calls)
   prompts=[item[v+'_prompt'] for item in items for v in ['actual','omitted']]
   outputs=model.generate(prompts,cfg.character_tokens,frozen=True,sample=True)
   for (item,v),out in zip([(item,v) for item in items for v in ['actual','omitted']],outputs):append_json(ledger.run_dir/'replay.jsonl',{'item_id':item['item_id'],'family_id':item['family_id'],'condition':item['condition'],'world':item['world'],'replay_seed':seed,'variant':v,'effective_batch_seed':seed,'generation':out,'prompt':item[v+'_prompt']})
  write(ledger.run_dir/'completion.json',{'completed':True,'states':len(items),'calls':ledger.calls})
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--admission',required=True);main(Path(p.parse_args().admission))
