"""Incremental use of the frozen sampler/loss-mask reconstruction."""
from collections import Counter
from pathlib import Path
import gzip
import hashlib
import json
from pcc.campaign import jobs,load_overrides,resolve_job
from pcc.freeze import verify_freeze
from pcc.resources import sha256
from pcc.training import balanced_stream,serialize_completion
from supplements.review_001.exposure import replay,concentration
from supplements.review_001.common import stream,trace_path,write_csv
from .common import ROOT,OUT,CACHE,read,write,utc,log,fingerprint


def main():
    from transformers import AutoTokenizer
    prior_summary=read(ROOT/'supplements/review_001/results/supervision_exposure.json')
    prior_pools=read(ROOT/'supplements/review_001/results/supervision_pool_concentration.json')
    prior_provenance=read(ROOT/'supplements/review_001/results/exposure_provenance.json')['inputs']
    frozen=verify_freeze(ROOT);overrides=load_overrides(ROOT);all_summary=[];all_pools=[];sources={};new=[];tokenizers={}
    for original in jobs(frozen['plan']):
        if original['command']!='fit':continue
        job=resolve_job(original,overrides)
        if read(ROOT/'artifacts/campaign_state.json',{}).get('active_job',{}).get('id')==job['id']:continue # wait for final mirror boundary
        run=ROOT/'artifacts/runs'/job['id'];status=run/'status.json'
        if not status.exists() or read(status)['status']!='completed':continue
        meta=read(status);cfg=meta['config'];report=run/'training/training_summary.json';loss=run/'training/loss.jsonl';sup=ROOT/job['supervision']
        paths=[status,report,loss,sup];cache=CACHE/'exposure'/f'{run.name}.json'
        if cache.exists() and read(cache)['fingerprint']==fingerprint(paths):
            item=read(cache);all_summary.append(item['summary']);all_pools+=item['pools'];sources[run.name]=item['provenance'];continue
        previous=next((r for r in prior_summary if r['run_id']==run.name and r['status']=='reconstructed_and_verified'),None)
        if previous:
            hashes={str(p.relative_to(ROOT)):sha256(p) for p in paths}
            if not all(prior_provenance.get(k)==v for k,v in hashes.items()):raise ValueError('Prior exposure evidence changed: '+run.name)
            details=ROOT/f'artifacts/review_001/exposure/{run.name}.jsonl.gz'
            assert sha256(details)==prior_provenance[str(details.relative_to(ROOT))]
            pools=[r for r in prior_pools if r['run_id']==run.name]
            item={'summary':previous,'pools':pools,'fingerprint':fingerprint(paths),'provenance':{'reused_verified_audit':True,'inputs':hashes,'detail_path':str(details.relative_to(ROOT)),'detail_sha256':sha256(details)}}
            write(cache,item);all_summary.append(previous);all_pools+=pools;sources[run.name]=item['provenance'];continue
        key=cfg['model'];tokenizer_path=ROOT/'artifacts/review_001/tokenizers'/key
        if not tokenizer_path.exists():
            all_summary.append({'run_id':run.name,'status':'missing_exact_tokenizer','model':key,'condition':cfg['condition'],'seed':cfg['seed']});continue
        if key not in tokenizers:tokenizers[key]=AutoTokenizer.from_pretrained(tokenizer_path,local_files_only=True,trust_remote_code=False,padding_side='left')
        tokenizer=tokenizers[key];assert hashlib.sha256(tokenizer.chat_template.encode()).hexdigest()==meta['chat_template_sha256']
        examples=list(stream(sup));lengths={};index={};losses=list(stream(loss));training=read(report)
        assert sha256(sup)==meta['supervision_sha256'];start=losses[0]['step']-1
        for example in examples:
            identity=(example['family_id'],example['world'],example['turn']);assert identity not in index;index[identity]=example
            prefix=len(tokenizer.apply_chat_template(example['messages'],tokenize=True,add_generation_prompt=True))
            suffix=len(tokenizer.encode(serialize_completion(example['completion']),add_special_tokens=False))+1
            assert prefix<=cfg['max_input_tokens'];lengths[identity]=(prefix,suffix)
        def lengths_stream():
            for ex in balanced_stream(examples,cfg['seed']):
                key=(ex['family_id'],ex['world'],ex['turn']);yield key,*lengths[key]
        exposed,steps=replay(lengths_stream(),cfg['train_steps'],cfg['train_tokens_per_step'],start)
        assert len(steps)==len(losses)==training['optimizer_steps']
        for expected,actual in zip(steps,losses):assert all(expected[k]==actual[k] for k in expected)
        assert sum(x['supervised_tokens'] for x in steps)==training['supervised_tokens']
        assert len(exposed)==training['unique_windows']
        assert sum(r['loaded_occurrences_including_resume_replay'] for r in exposed.values())-len(exposed)==training['reused_windows']
        detail=[]
        for identity,values in exposed.items():
            ex=index[identity];detail.append({'family_id':identity[0],'world':identity[1],'turn':identity[2],
              'pool':'clean' if ex['metrics']['success'] else 'recovery','label_source':ex['label_source'],**values})
        path=CACHE/'exposure'/f'{run.name}.jsonl.gz';path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('wb') as raw:
            with gzip.GzipFile(filename='',fileobj=raw,mode='wb',mtime=0) as stream_out:
                for row in detail:stream_out.write((json.dumps(row,sort_keys=True)+'\n').encode())
        active=[r for r in detail if r.get('unmasked_target_tokens',0)]
        base={'run_id':run.name,'model':key,'condition':cfg['condition'],'seed':cfg['seed'],'resume_start_step':start}
        summary={**base,'status':'reconstructed_and_verified','optimizer_steps_in_process':len(losses),'training_input_tokens':training['input_tokens'],
          'supervised_target_tokens':training['supervised_tokens'],'loaded_unique_windows_including_replay':len(exposed),
          'loss_contributing_unique_windows':len(active),'loss_contributing_unique_families':len({r['family_id'] for r in active}),
          'loaded_occurrences_including_replay':sum(r['loaded_occurrences_including_resume_replay'] for r in detail),
          'orphaned_target_tokens_masked':sum(r.get('orphaned_target_tokens_masked',0) for r in detail),
          'resume_replay_input_tokens_not_optimized':sum(r.get('input_tokens_in_resume_replay_only',0) for r in detail),
          'unoptimized_tail_input_tokens':sum(r.get('unoptimized_tail_input_tokens',0) for r in detail),
          'label_sources_contributing_loss':dict(Counter(r['label_source'] for r in active)),
          'target_tokens_by_label_source':{label:sum(r.get('unmasked_target_tokens',0) for r in detail if r['label_source']==label) for label in sorted({r['label_source'] for r in detail})},
          'supersedes_run_id':meta.get('supersedes_run_id'),'qualification':'Exact per-process loss exposure; resume prefix excluded from new gradients. Prior effective steps require joining the actual checkpoint-resume chain.'}
        pools=[]
        for pool in ('clean','recovery'):
            group=[r for r in detail if r['pool']==pool];contributing=[r for r in group if r.get('unmasked_target_tokens',0)]
            pools.append({**base,'pool':pool,'eligible_windows':sum(('clean' if ex['metrics']['success'] else 'recovery')==pool for ex in examples),
              'loaded_unique_windows':len(group),'loss_contributing_unique_windows':len(contributing),
              'loss_contributing_unique_families':len({r['family_id'] for r in contributing}),
              'loss_contributing_occurrences':sum(r.get('occurrences_contributing_loss',0) for r in contributing),
              **concentration([r.get('unmasked_target_tokens',0) for r in group])})
        item={'summary':summary,'pools':pools,'fingerprint':fingerprint(paths),'provenance':{'reused_verified_audit':False,'validated_utc':utc(),
          'inputs':{str(p.relative_to(ROOT)):sha256(p) for p in paths},'detail_path':str(path.relative_to(ROOT)),'detail_sha256':sha256(path),
          'tokenizer_hashes':{str(p.relative_to(ROOT)):sha256(p) for p in sorted(tokenizer_path.iterdir()) if p.is_file()},
          'replay_source_sha256':sha256(ROOT/'supplements/review_001/exposure.py')}}
        write(cache,item);all_summary.append(summary);all_pools+=pools;sources[run.name]=item['provenance'];new.append(run.name)
        log(f'Reconstructed {run.name}: {summary["supervised_target_tokens"]} target tokens; {summary["loss_contributing_unique_windows"]} distinct windows actually contributed loss. Every optimizer step matched.')
    write(OUT/'supervision_exposure.json',all_summary);write_csv(OUT/'supervision_exposure.csv',all_summary)
    write(OUT/'supervision_pools.json',all_pools);write_csv(OUT/'supervision_pools.csv',all_pools)
    write(OUT/'exposure_provenance.json',{'generated_utc':utc(),'runs':sources,'newly_reconstructed':new,'source_sha256':sha256(Path(__file__))})
    print(json.dumps({'new_fits':new,'audited_fits':len(all_summary),'prior_verified_audits_reused':sum(v['reused_verified_audit'] for v in sources.values())}))


if __name__=='__main__':main()
