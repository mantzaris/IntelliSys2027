"""CPU-only native-token and measured batch-wall planning; no model responses."""
from pathlib import Path
from collections import defaultdict,Counter
import gzip,json
import numpy as np
from transformers import AutoTokenizer
from rep_sensitivity.models import LocalModel
from rep_sensitivity.objective_confirmation import prepare
from rep_sensitivity.targeted_replay import manager_requests,root_request,lossless_summary,shared_manager_requests
from rep_sensitivity.schema import canonical,digest
from rep_sensitivity.storage import immutable_json,utcnow

config=json.loads(Path('configs/objective-confirmation-v1.json').read_text());manifest,plans=prepare(config)
records=[]
for alias in config['models']:
    counter=object.__new__(LocalModel);counter.alias=alias
    counter.tokenizer=AutoTokenizer.from_pretrained(Path('artifacts/models/'+alias+'_path.txt').read_text().strip(),trust_remote_code=False)
    lengths=[];outputs=[];batch_sizes=Counter();inputs=[];arm_lengths=defaultdict(list)
    for pair,models in plans:
        jobs=models[alias];requests=[]
        for job in jobs:requests.extend(manager_requests(job,pair,counter))
        unique,_=shared_manager_requests(requests)
        for stage,n in [('manager',len(unique)),('root',len(jobs))]:
            for offset in range(0,n,config['batch_size']):batch_sizes[stage,min(config['batch_size'],n-offset)]+=1
        for request in unique:
            n=len(counter.token_ids(request['prompt']));lengths.append(n)
            inputs.append({'trial':request['trial'],'stage':request['stage'],'prompt_sha256':digest(request['prompt']),'tokens':n})
            arm_lengths[request['trial']['arm']].append(n)
        for job in jobs:
            fake={}
            for index,branch in enumerate(job['branches']):
                text=canonical(lossless_summary(branch));outputs.append(len(counter.tokenizer.encode(text,add_special_tokens=False)))
                fake[job['trial']['trial_id'],'manager'+str(index)]={'response':{'text':text,'finish_reason':'stop'}}
            request=root_request(job,fake);n=len(counter.token_ids(request['prompt']));lengths.append(n)
            inputs.append({'trial':request['trial'],'stage':'root_reference','prompt_sha256':digest(request['prompt']),'tokens':n})
    if max(lengths)+config['max_output_tokens']>config['max_context_tokens'] or max(outputs)>config['max_output_tokens']:
        raise RuntimeError('Native-token context/output-cap feasibility failed')
    # Use complete validation timings only. One record per physical batch, no
    # optimistic linear TPS assumption when the new batch has fewer requests.
    timings={}
    for p in Path('artifacts/runs/validation-v7',alias,'calls').glob('*.json.gz'):
        call=json.loads(gzip.decompress(p.read_bytes()));r=call['response'];stage='root' if call['stage']=='root' else 'manager'
        timings[stage,r['started_utc'],r['batch_size']]=r['batch_wall_seconds']
    projected_mean=0;projected_p95=0;matched=[]
    for (stage,size),number in sorted(batch_sizes.items()):
        larger=[seconds for (s,utc,n),seconds in timings.items() if s==stage and n>=size]
        if not larger:raise RuntimeError('No measured batch at least as large as planned batch')
        # Conservatively retain full wall time of the smallest measured >= size
        # batches. Also record prompt-length and reference-output differences.
        selected_size=min(n for s,utc,n in timings if s==stage and n>=size)
        sample=[seconds for (s,utc,n),seconds in timings.items() if s==stage and n==selected_size]
        mean=float(np.mean(sample));p95=float(np.quantile(sample,.95))
        projected_mean+=number*mean;projected_p95+=number*p95
        matched.append({'stage':stage,'new_batch_size':size,'batches':number,'measured_batch_size':selected_size,
            'measured_batches':len(sample),'measured_mean_seconds':mean,'measured_p95_seconds':p95})
    loads=[]
    for line in Path('artifacts/runs/validation-v7',alias,'events.jsonl').read_text().splitlines():
        e=json.loads(line)
        if e['event']=='run_start':loads.append(e.get('model_load_seconds',0))
    # Main engine reuse can give zero load in validation. Use other prior run
    # starts of this model for measured load cost, without reading their choices.
    for p in Path('artifacts/runs').glob('*/'+alias+'/events.jsonl'):
        for line in p.read_text().splitlines():
            try:e=json.loads(line)
            except json.JSONDecodeError:continue
            if e['event']=='run_start' and e.get('model_load_seconds',0)>0:loads.append(e['model_load_seconds'])
    load=max(loads) if loads else None
    if load is None:raise RuntimeError('No measured model loading overhead available')
    records.append({'model':alias,'trajectories':len(plans)*10,'physical_calls':sum(size*n for (_,size),n in batch_sizes.items()),
        'manager_prompt_tokens_by_arm':{k:{'minimum':min(v),'maximum':max(v),'mean':float(np.mean(v))} for k,v in arm_lengths.items()},
        'reference_prompt_token_range':[min(lengths),max(lengths)],'reference_summary_max_tokens':max(outputs),
        'batch_planning':matched,'projected_inference_seconds_mean':projected_mean,'projected_inference_seconds_p95':projected_p95,
        'measured_prior_load_seconds_max':load,'planned_load_seconds':load+30,
        'input_inventory_sha256':digest(inputs)})
    immutable_json(Path('artifacts/designs/objective-confirmation-v1')/(alias+'-'+digest(inputs)+'.json'),inputs)
source=digest({p.name:p.read_text() for p in Path('src/rep_sensitivity').glob('*.py')})
result={'utc':utcnow(),'config_sha256':digest(config),'source_sha256':source,'manifest_sha256':digest(manifest),
        'models':records,'gpu_inference_calls':0,'new_gpu_wall_cap_seconds':config['additional_gpu_wall_seconds_cap'],
        'projected_total_seconds_mean':sum(r['projected_inference_seconds_mean']+r['planned_load_seconds'] for r in records),
        'projected_total_seconds_p95':sum(r['projected_inference_seconds_p95']+r['planned_load_seconds'] for r in records),
        'warning':'Conservative measured-batch projection, not actual new runtime. Reference summaries do not bound arbitrary model output. Per-call caps reject overflow; no input truncation. Hard shared two-hour wall budget includes model loads, starts only when GPU available, and may leave a model incomplete without selecting by accuracy.'}
result['eligible_under_planning_cap']=result['projected_total_seconds_p95']<=config['additional_gpu_wall_seconds_cap']
p=Path('records/preflight')/('objective-confirmation-v1-'+digest([config,source])[:12]+'.json')
immutable_json(p,result);print(json.dumps({'record':str(p),**result}),flush=True)
