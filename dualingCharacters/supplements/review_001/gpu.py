"""Serialized supplementary model operations, never a replacement core run."""
from pathlib import Path
import argparse
import importlib.metadata
import json
import tarfile
import time
from pcc.config import RunConfig
from pcc.fast_backend import FastBackbone
from pcc.resources import RunLedger,append_json,sha256,used_seconds
from .common import ROOT,HERE,ARTIFACTS,read,write,require_completed
from .freeze import verify
from .allocation import review_seconds
from .inputs import selected_families
from .fresh import family
from .rollout import run_rollout


class GuardedModel:
    """Composition adds a budget guard without modifying the core backbone."""
    def __init__(self,backbone,deadline):
        self.backbone=backbone;self.config=backbone.config;self.deadline=deadline
    def generate(self,*args,**kwargs):
        if time.monotonic()>self.deadline-90:raise RuntimeError('Review budget boundary before another generation batch; preserve partial evidence')
        return self.backbone.generate(*args,**kwargs)


def checkpoint(model,condition,bindings,ledger):
    entry=bindings[condition]
    if entry['adapter_path']:
        path=ROOT/entry['adapter_path']
        assert sha256(path/'adapter_model.safetensors')==entry['adapter_sha256']
        model.backbone.load_adapter(path)
    else:model.backbone.adapter=None
    assert ledger.metadata['model_revision']==entry['model_revision']
    assert ledger.metadata['chat_template_sha256']==entry['chat_template_sha256']
    ledger.metadata.setdefault('checkpoint_sequence',[]).append({'condition':condition,**entry,'starting_call_offset':ledger.calls})
    ledger.heartbeat()


def generate_records(model,rows,out):
    for offset in range(0,len(rows),model.config.batch_size):
        group=rows[offset:offset+model.config.batch_size]
        # Only the explicit prompt enters the policy, never saved answers/targets.
        outputs=model.generate([row['prompt'] for row in group])
        for row,generation in zip(group,outputs):append_json(out,{**row,'generation':generation})


def memory(model,ledger,bindings,count,common,profile=False):
    ids={f'test-{n:04d}' for n in selected_families(count)};timings={}
    # Base first; each final adapter loaded once. No reset of call-accounting RNG.
    for c in (('base','C1','C3','C5') if common else ('C1','C3','C5')):
        checkpoint(model,c,bindings,ledger)
        if c!='base':
            records=[r for r in read(ARTIFACTS/f'inputs/memory-{c}.json') if r['family_id'] in ids]
            start=time.monotonic()
            for variant in ('A0','A1','A2'):
                generate_records(model,[r for r in records if r['variant']==variant],ledger.run_dir/f'{c}-{variant}.jsonl')
            timings['memory_seconds']=timings.get('memory_seconds',0)+time.monotonic()-start
        if common:
            records=[{**r,'model_condition':c} for r in read(ARTIFACTS/'inputs/common-user-only.json') if r['family_id'] in ids]
            start=time.monotonic();generate_records(model,records,ledger.run_dir/f'{c}-common.jsonl')
            timings['common_seconds']=timings.get('common_seconds',0)+time.monotonic()-start
    return timings


def main(stage):
    frozen=verify();protocol=read(HERE/'protocol.json');binding_doc=read(ARTIFACTS/'bindings.json');bindings=binding_doc['bindings']
    assert binding_doc['supplement_freeze_sha256']==sha256(HERE/'FREEZE.json')
    # Independently require every core job before any model loading.
    from pcc.campaign import jobs,resolve_job,load_overrides
    from pcc.freeze import verify_freeze
    for j in jobs(verify_freeze(ROOT)['plan']):require_completed(resolve_job(j,load_overrides(ROOT))['id'])
    allocation=read(ARTIFACTS/'allocation.json') if stage!='profile' else None
    if allocation is not None and stage not in allocation['stages']:raise PermissionError('Stage not in outcome-blind allocation')
    available=min(7200-review_seconds(),96*3600-1800-used_seconds(ROOT/'artifacts/run_registry.jsonl'))
    if stage=='profile':available=min(available,900)
    if available<180:raise RuntimeError('Insufficient review budget after contingency')
    cfg=RunConfig(model='qwen',condition='base',seed=17,engine='vllm',phase='review001_exploratory',
                  active_gpu_hours_ceiling=95.5,max_run_seconds=int(available)-30,**protocol['inference'])
    with RunLedger(ROOT/'artifacts',protocol['run_ids'][stage],cfg) as ledger:
        ledger.metadata.update(task='review001_'+stage,supplement_freeze_sha256=sha256(HERE/'FREEZE.json'),
          bindings_sha256=sha256(ARTIFACTS/'bindings.json'),allocation_sha256=sha256(ARTIFACTS/'allocation.json') if allocation else None,
          inference_versions={p:importlib.metadata.version(p) for p in ('vllm','transformers','tokenizers','huggingface-hub','xgrammar')})
        assert ledger.metadata['inference_versions']=={'vllm':'0.10.2','transformers':'4.56.2','tokenizers':'0.22.2','huggingface-hub':'0.35.3','xgrammar':'0.1.23'}
        with tarfile.open(ledger.run_dir/'review_source.tar.gz','w:gz') as archive:
            for rel in frozen['files']:archive.add(ROOT/rel,arcname=rel)
            for path in (HERE/'FREEZE.json',ARTIFACTS/'bindings.json',ARTIFACTS/'allocation.json'):
                if path.exists():archive.add(path,arcname=str(path.relative_to(ROOT)))
        ledger.metadata['review_source_sha256']=sha256(ledger.run_dir/'review_source.tar.gz')
        ledger.metadata['input_hashes']={str(p.relative_to(ROOT)):sha256(p) for p in sorted((ARTIFACTS/'inputs').glob('*.json'))}
        for condition in ('C1','C3','C5'):
            meta=read(ROOT/'artifacts/runs'/bindings[condition]['evaluation_run_id']/'status.json')
            for field in ('engine','structured_decoding','batch_size','max_input_tokens','answer_tokens','character_tokens','retrieval_messages','recent_messages'):
                assert getattr(cfg,field)==meta['config'][field], 'Replay inference configuration mismatch: '+field
        backend=FastBackbone(cfg,ledger,ROOT/'configs/models.json')
        model=GuardedModel(backend,ledger.start+available)
        if stage=='profile':
            timing=memory(model,ledger,bindings,16,True,True)
            checkpoint(model,'base',bindings,ledger);start=time.monotonic()
            run_rollout(model,[s for n in range(8) for s in family('profile',n,32)],'B1',ledger.run_dir/'profile-B1.jsonl','profile',False)
            timing.update(rollout_seconds=time.monotonic()-start,load_seconds=ledger.metadata['model_load_seconds'],
                          classification='Timing only. Raw generations saved; task scores not computed for allocation.')
            write(ledger.run_dir/'timing_only.json',timing)
        elif stage=='memory':memory(model,ledger,bindings,allocation['families'],allocation['common_input'])
        elif stage in ('conflict','routing'):
            checkpoint(model,'base',bindings,ledger)
            variants=protocol['B_variants' if stage=='conflict' else 'C_variants']
            for condition in variants:
                ledger.metadata.setdefault('condition_call_offsets',{})[condition]=ledger.calls
                run_rollout(model,[s for n in range(16) for s in family('mechanism',n,32)],condition,ledger.run_dir/(condition+'.jsonl'))
        elif stage=='severity':
            checkpoint(model,'base',bindings,ledger)
            generate_records(model,read(ARTIFACTS/'inputs/severity.json'),ledger.run_dir/'severity.jsonl')
        elif stage=='balanced':
            for condition in ('C1','C3','C5'):
                checkpoint(model,condition,bindings,ledger)
                run_rollout(model,[s for n in range(64) for s in family('balanced',n,64)],'none',ledger.run_dir/(condition+'.jsonl'),'balanced')
        write(ledger.run_dir/'completion.json',{'stage':stage,'allocation':allocation,'completed_fixed_scope':True})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['profile','memory','conflict','routing','severity','balanced']);main(p.parse_args().stage)
