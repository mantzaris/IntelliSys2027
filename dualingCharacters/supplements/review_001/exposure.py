"""CPU replay of exact token packing and loss masks, without model weights."""
from collections import Counter,defaultdict,deque
import gzip
import hashlib
import json
from pcc.training import balanced_stream,serialize_completion
from .common import ROOT,HERE,ARTIFACTS,RESULTS,read,write,write_csv,stable_rows,eligible_runs,record_source


def replay(length_stream,steps,quota,start_step=0):
    """length_stream yields (key,prefix_len,suffix_len); count real loss exposure."""
    buffer=deque();buffer_size=0;occurrence=0;rows=defaultdict(Counter);step_rows=[];contributed=set()
    for step in range(steps):
        while buffer_size<quota:
            key,prefix,suffix=next(length_stream);occurrence+=1
            buffer.append([key,prefix,prefix+suffix,0,occurrence]);buffer_size+=prefix+suffix
            rows[key]['loaded_occurrences_including_resume_replay']+=1
        left=quota;supervised=0;first=True
        while left:
            key,prefix,total,position,occ=buffer[0];take=min(total-position,left)
            labels=max(0,min(position+take,total)-max(position,prefix))
            orphan=first and position!=0
            if step>=start_step:
                rows[key]['input_tokens_in_optimized_chunks']+=take
                if orphan:rows[key]['orphaned_target_tokens_masked']+=labels
                else:
                    supervised+=labels;rows[key]['unmasked_target_tokens']+=labels
                    if labels and occ not in contributed:
                        contributed.add(occ);rows[key]['occurrences_contributing_loss']+=1
            else:rows[key]['input_tokens_in_resume_replay_only']+=take
            position+=take;left-=take;buffer_size-=take;first=False
            if position==total:buffer.popleft()
            else:buffer[0][3]=position
        if step>=start_step:step_rows.append({'step':step+1,'input_tokens':quota,'supervised_tokens':supervised})
    for key,prefix,total,position,occ in buffer:
        rows[key]['unoptimized_tail_input_tokens']+=total-position
    return rows,step_rows


def concentration(values):
    values=sorted((v for v in values if v),reverse=True);total=sum(values)
    if not total:return {'target_tokens':0,'top1_token_share':None,'top5_token_share':None,'effective_windows_by_token_share':None}
    return {'target_tokens':total,'top1_token_share':values[0]/total,'top5_token_share':sum(values[:5])/total,
            'effective_windows_by_token_share':total**2/sum(v*v for v in values)}


def main():
    from transformers import AutoTokenizer
    import transformers,tokenizers
    inputs={};summaries=[];by_pool=[];tokenizer_cache={}
    for run,meta in eligible_runs('fit'):
        cfg=meta['config'];model=cfg['model'];key_path=ARTIFACTS/'tokenizers'/model
        if not key_path.exists():
            summaries.append({'run_id':run.name,'status':'pending_exact_tokenizer'});continue
        if model not in tokenizer_cache:
            tokenizer_cache[model]=AutoTokenizer.from_pretrained(key_path,local_files_only=True,trust_remote_code=False,padding_side='left')
            for path in sorted(key_path.iterdir()):
                if path.is_file():record_source(inputs,path)
        tokenizer=tokenizer_cache[model]
        assert hashlib.sha256(tokenizer.chat_template.encode()).hexdigest()==meta['chat_template_sha256']
        record_source(inputs,run/'status.json')
        report=read(run/'training/training_summary.json');record_source(inputs,run/'training/training_summary.json')
        # Explicit scheduled supervision path, including the four amendment aliases.
        from pcc.campaign import jobs,load_overrides,resolve_job
        from pcc.freeze import verify_freeze
        frozen=verify_freeze(ROOT);overrides=load_overrides(ROOT)
        job=next(resolve_job(j,overrides) for j in jobs(frozen['plan']) if resolve_job(j,overrides)['id']==run.name)
        source=ROOT/job['supervision'];examples=list(stable_rows(source,inputs))
        assert inputs[str(source.relative_to(ROOT))]==meta['supervision_sha256']
        losses=list(stable_rows(run/'training/loss.jsonl',inputs));start=losses[0]['step']-1
        index={};lengths={}
        for row in examples:
            key=(row['family_id'],row['world'],row['turn']);index[key]=row
            prefix=len(tokenizer.apply_chat_template(row['messages'],tokenize=True,add_generation_prompt=True))
            suffix=len(tokenizer.encode(serialize_completion(row['completion']),add_special_tokens=False))+1
            assert prefix<=cfg['max_input_tokens']
            lengths[key]=(prefix,suffix)
        def length_stream():
            for row in balanced_stream(examples,cfg['seed']):
                key=(row['family_id'],row['world'],row['turn'])
                yield (key,*lengths[key])
        exposed,reconstructed=replay(length_stream(),cfg['train_steps'],cfg['train_tokens_per_step'],start)
        assert len(reconstructed)==len(losses)==report['optimizer_steps']
        for expected,actual in zip(reconstructed,losses):
            assert all(actual[k]==expected[k] for k in expected), 'Reconstructed loss mask differs from optimizer log'
        assert sum(r['supervised_tokens'] for r in reconstructed)==report['supervised_tokens']
        assert len(exposed)==report['unique_windows']
        assert sum(x['loaded_occurrences_including_resume_replay'] for x in exposed.values())-len(exposed)==report['reused_windows']
        details=[]
        for key,values in exposed.items():
            row=index[key];details.append({'family_id':key[0],'world':key[1],'turn':key[2],
              'pool':'clean' if row['metrics']['success'] else 'recovery','label_source':row['label_source'],**values})
        dest=ARTIFACTS/'exposure'/f'{run.name}.jsonl.gz';dest.parent.mkdir(parents=True,exist_ok=True)
        # Deterministic archive; actual per-window records remain outside Git.
        with dest.open('wb') as raw:
            with gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as compressed:
                for row in details:compressed.write((json.dumps(row,sort_keys=True)+'\n').encode())
        record_source(inputs,dest)
        base={'run_id':run.name,'model':model,'condition':cfg['condition'],'seed':cfg['seed'],'resume_start_step':start}
        contributing=[r for r in details if r.get('unmasked_target_tokens',0)]
        summaries.append({**base,'status':'reconstructed_and_verified','optimizer_steps_in_process':len(losses),
          'training_input_tokens':report['input_tokens'],'supervised_target_tokens':report['supervised_tokens'],
          'loaded_unique_windows_including_replay':len(exposed),'loss_contributing_unique_windows':len(contributing),
          'loss_contributing_unique_families':len({r['family_id'] for r in contributing}),
          'loaded_occurrences_including_replay':sum(x['loaded_occurrences_including_resume_replay'] for x in exposed.values()),
          'orphaned_target_tokens_masked':sum(r.get('orphaned_target_tokens_masked',0) for r in details),
          'resume_replay_input_tokens_not_optimized':sum(r.get('input_tokens_in_resume_replay_only',0) for r in details),
          'unoptimized_tail_input_tokens':sum(r.get('unoptimized_tail_input_tokens',0) for r in details),
          'label_sources_contributing_loss':dict(Counter(r['label_source'] for r in contributing)),
          'target_tokens_by_label_source':{label:sum(r.get('unmasked_target_tokens',0) for r in details if r['label_source']==label) for label in sorted({r['label_source'] for r in details})},
          'supersedes_run_id':meta.get('supersedes_run_id'),
          'qualification':'Per optimizer process. Resume-prefix token replay contributes no new gradient; prior-process effective steps must be joined by the recorded resume chain, not double counted.'})
        for pool in ('clean','recovery'):
            group=[r for r in details if r['pool']==pool];active=[r for r in group if r.get('unmasked_target_tokens',0)]
            by_pool.append({**base,'pool':pool,'eligible_windows':sum(('clean' if x['metrics']['success'] else 'recovery')==pool for x in examples),
              'loaded_unique_windows':len(group),'loss_contributing_unique_windows':len(active),
              'loss_contributing_unique_families':len({r['family_id'] for r in active}),
              'loss_contributing_occurrences':sum(r.get('occurrences_contributing_loss',0) for r in group),
              **concentration([r.get('unmasked_target_tokens',0) for r in group])})
    write(RESULTS/'supervision_exposure.json',summaries);write_csv(RESULTS/'supervision_exposure.csv',summaries)
    write(RESULTS/'supervision_pool_concentration.json',by_pool);write_csv(RESULTS/'supervision_pool_concentration.csv',by_pool)
    record_source(inputs,HERE/'exposure.py')
    write(RESULTS/'exposure_provenance.json',{'inputs':inputs,'transformers':transformers.__version__,'tokenizers':tokenizers.__version__,
      'no_model_weights_or_gpu_operations':True,'meaning':'Target tokens count only non-masked labels in logged optimizer steps; all counts checked against the actual step logs.'})
    print(json.dumps({'fits':len(summaries),'verified':sum(x['status']=='reconstructed_and_verified' for x in summaries)}))


if __name__=='__main__':main()
