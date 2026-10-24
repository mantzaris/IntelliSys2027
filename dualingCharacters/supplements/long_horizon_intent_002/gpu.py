"""Optional serialized GPU runner. It refuses missing core/review/time/resource gates."""
from dataclasses import asdict
from pathlib import Path
import argparse
import importlib.metadata
import signal
import tarfile
import time
from pcc.config import RunConfig
from pcc.resources import RunLedger,sha256,append_json,used_seconds
from pcc.fast_backend import FastBackbone
from .common import ROOT,HERE,ARTIFACTS,read,write
from .budget import prerequisites,admit,cumulative_extension_seconds,timestamp
from .freeze import verify
from .public import PublicConversation
from .interface import InterfaceConfig,observation,SCHEMA
from .rollout import run


VERSIONS={'vllm':'0.10.2','transformers':'4.56.2','tokenizers':'0.22.2','huggingface-hub':'0.35.3','xgrammar':'0.1.23'}


def terminate(signum,frame):raise TimeoutError('New intent worker received deadline termination; preserve partial evidence')


def public_inputs(collection,horizon,families=None):
    manifest=read(HERE/'dataset_manifest.json');entries=[e for e in manifest['entries'] if e['collection']==collection and e['horizon']==horizon and (families is None or e['family_id'] in families)]
    result=[]
    for entry in sorted(entries,key=lambda e:(e['family_id'],e['world'])):
        path=ROOT/entry['public_path']
        if sha256(path)!=entry['public_sha256']:raise ValueError('Public script hash changed')
        result.append(PublicConversation.load(read(path)))
    return result


def checkpoint(model,ledger,condition,seed,bindings):
    entry=bindings[f'{condition}-{seed}'];path=ROOT/entry['adapter_path']
    if sha256(path/'adapter_model.safetensors')!=entry['adapter_sha256'] or sha256(path/'adapter_config.json')!=entry['adapter_config_sha256']:raise ValueError('Bound adapter changed')
    if ledger.metadata['model_revision']!=entry['model_revision'] or ledger.metadata['chat_template_sha256']!=entry['chat_template_sha256']:raise ValueError('Model/tokenizer binding mismatch')
    started=time.monotonic();model.load_adapter(path)
    ledger.metadata.setdefault('checkpoint_sequence',[]).append({'condition':condition,'seed':seed,**entry,'starting_call_offset':ledger.calls,'load_seconds':time.monotonic()-started});ledger.heartbeat()


def main(args):
    signal.signal(signal.SIGTERM,terminate);frozen=verify();session=read(HERE/'SESSION.json');activation=read(ARTIFACTS/'activation.json',{'enabled':False})
    gates=prerequisites();gate=admit(args.reservation,session,time.time(),used_seconds(ROOT/'artifacts/run_registry.jsonl'),cumulative_extension_seconds(ROOT/'artifacts/run_registry.jsonl'),gates['core_complete'],gates['review_complete'],activation.get('enabled') is True)
    if not gate['admitted']:raise PermissionError(str(gate['reasons']))
    if activation.get('session_id')!=session['session_id']:raise PermissionError('Activation belongs to a different session')
    bindings_doc=read(ARTIFACTS/'bindings.json')
    if bindings_doc['intent_freeze_sha256']!=sha256(HERE/'FREEZE.json'):raise ValueError('Scientific binding mismatch')
    bindings=bindings_doc['bindings'];allocation=read(ARTIFACTS/'allocation.json',{})
    expected=f'intent002-{args.stage}-17-v1' if args.stage!='evaluate' else f'intent002-evaluate-qwen-{args.condition.lower()}-{args.seed}-v1'
    if expected!=args.run_id:raise ValueError('Run ID does not match declared stage')
    if args.stage in {'engineering','profile'}:
        if args.seed!=17 or args.reservation!=900:raise ValueError('Fixed engineering/profile allocation required')
    else:
        selected=allocation.get('selected')
        if not selected or args.seed not in selected['seeds'] or args.condition not in ('C1','C3','C5'):raise PermissionError('Outside frozen timing allocation')
        if args.reservation!=allocation['per_worker_reservation_seconds']:raise ValueError('Worker reservation differs from allocation')
        if allocation['intent_freeze_sha256']!=sha256(HERE/'FREEZE.json') or allocation['bindings_sha256']!=sha256(ARTIFACTS/'bindings.json'):raise ValueError('Allocation provenance mismatch')
    cfg=RunConfig(model='qwen',condition=args.condition,seed=args.seed,engine='vllm',precision='bf16',structured_decoding=True,
      batch_size=32,max_input_tokens=4096,answer_tokens=640,character_tokens=128,retrieval_messages=8,recent_messages=4,
      phase='intent002_exploratory',active_gpu_hours_ceiling=95.5,max_run_seconds=int(args.reservation)-20)
    with RunLedger(ROOT/'artifacts',args.run_id,cfg) as ledger:
        deadline=min(time.monotonic()+args.reservation-90,time.monotonic()+timestamp(session['deadline_utc'])-time.time()-90)
        def guard():
            if time.monotonic()>=deadline:raise TimeoutError('Before-batch deadline/resource stop; partial grid stays incomplete')
        ledger.metadata.update(task='intent002_'+args.stage,intent_freeze_sha256=sha256(HERE/'FREEZE.json'),
          bindings_sha256=sha256(ARTIFACTS/'bindings.json'),dataset_manifest_sha256=sha256(HERE/'dataset_manifest.json'),
          allocation_sha256=sha256(ARTIFACTS/'allocation.json') if args.stage=='evaluate' else None,
          session_id=session['session_id'],session_deadline_utc=session['deadline_utc'],admission=gate,
          inference_versions={k:importlib.metadata.version(k) for k in VERSIONS},interface=asdict(InterfaceConfig()),
          private_ledger_in_policy_inputs=False,parameter_training=False)
        if ledger.metadata['inference_versions']!=VERSIONS:raise ValueError('Inference environment version mismatch')
        with tarfile.open(ledger.run_dir/'intent_source.tar.gz','w:gz') as archive:
            for rel in frozen['files']:archive.add(ROOT/rel,arcname=rel)
            for path in (HERE/'FREEZE.json',HERE/'SESSION.json',ARTIFACTS/'bindings.json',ARTIFACTS/'allocation.json'):
                if path.exists():archive.add(path,arcname=str(path.relative_to(ROOT)))
        ledger.metadata['intent_source_sha256']=sha256(ledger.run_dir/'intent_source.tar.gz');guard()
        model=FastBackbone(cfg,ledger,ROOT/'configs/models.json');guard();completed=[];timings=[]
        if args.stage=='engineering':
            for condition in ('C1','C3','C5'):
                guard();checkpoint(model,ledger,condition,17,bindings)
                completed.extend(run(model,public_inputs('engineering',16),ledger.run_dir/f'{condition}-engineering.jsonl',condition,17,before_batch=guard))
            # Execution/interface checks only. No ledger/rubric task scoring.
            summaries=[]
            for condition in ('C1','C3','C5'):
                rows=[__import__('json').loads(line) for line in (ledger.run_dir/f'{condition}-engineering.jsonl').read_text().splitlines()]
                summaries.append({'condition':condition,'calls':len(rows),'valid_interface':sum(r['interface_valid'] for r in rows),'generation_capped':sum(r['generation_capped'] for r in rows),'max_input_tokens':max(r['observation']['input_tokens'] for r in rows)})
            write(ledger.run_dir/'engineering_checks.json',{'execution_only':True,'task_scores_computed':False,'conditions':summaries})
        elif args.stage=='profile':
            for condition in ('C1','C3','C5'):
                guard();checkpoint(model,ledger,condition,17,bindings)
                for horizon in (16,64,128):
                    conversations=public_inputs('engineering',horizon);prompts=[]
                    for c in conversations:
                        prompt,_=observation([c.prior_message,*c.messages],'',model.tokenizer);prompts.append(prompt)
                    guard();start=time.monotonic();outputs=model.generate(prompts,max_new_tokens=640,sample=False,response_schema=SCHEMA);seconds=time.monotonic()-start
                    tokens=sum(x['output_tokens'] for x in outputs)
                    if tokens<=0:raise ValueError('Profiling returned no generated tokens')
                    timings.append({'condition':condition,'horizon':horizon,'calls':len(outputs),'seconds':seconds,'generated_tokens':tokens,
                      'seconds_per_generated_token':seconds/tokens,'classification':'Collapsed public-prefix timing only; not an interactive scientific rollout'})
                    for c,prompt,result in zip(conversations,prompts,outputs):append_json(ledger.run_dir/'profile.jsonl',{'family_id':c.family_id,'world':c.world,'horizon':horizon,'condition':condition,'prompt':prompt,'generation':result})
                    guard()
            write(ledger.run_dir/'timing_only.json',{'batches':timings,'slowest_seconds_per_generated_token':max(t['seconds_per_generated_token'] for t in timings),
              'load_seconds':ledger.metadata['model_load_seconds']+max(x['load_seconds'] for x in ledger.metadata['checkpoint_sequence']),
              'allocation_output_cap':640,'task_scores_computed':False})
        else:
            guard();checkpoint(model,ledger,args.condition,args.seed,bindings)
            for horizon in (16,64,128):
                completed.extend(run(model,public_inputs('scientific',horizon,allocation['selected']['family_ids']),ledger.run_dir/'trajectories.jsonl',args.condition,args.seed,before_batch=guard))
        write(ledger.run_dir/'completion.json',{'stage':args.stage,'completed_fixed_scope':True,'completed_conversations':completed,
          'allocation_sha256':sha256(ARTIFACTS/'allocation.json') if args.stage=='evaluate' else None})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['engineering','profile','evaluate']);p.add_argument('--condition',choices=['C1','C3','C5'],default='C1');p.add_argument('--seed',type=int,default=17);p.add_argument('--reservation',type=float,required=True);p.add_argument('--run-id',required=True);main(p.parse_args())
