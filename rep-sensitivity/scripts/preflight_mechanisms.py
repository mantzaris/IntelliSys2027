"""CPU-only native-token input/cap and physical-call audit before new inference."""
import argparse
from collections import Counter
from difflib import SequenceMatcher
import json
from pathlib import Path
from transformers import AutoTokenizer
from rep_sensitivity.models import LocalModel
from rep_sensitivity.schema import canonical,digest
from rep_sensitivity.storage import immutable_json
from rep_sensitivity.controls import semantic_inventory
from rep_sensitivity.targeted_replay import prepare,manager_requests,root_request,lossless_summary,shared_manager_requests

p=argparse.ArgumentParser();p.add_argument('--config',required=True);a=p.parse_args()
config=json.loads(Path(a.config).read_text())
counter=object.__new__(LocalModel);counter.alias=config['model']
counter.tokenizer=AutoTokenizer.from_pretrained(Path('artifacts/models/'+config['model']+'_path.txt').read_text().strip(),trust_remote_code=False)
source_sha256=digest({p.name:p.read_text() for p in Path('src/rep_sensitivity').glob('*.py')})
identity=digest([config,source_sha256,Path(__file__).read_text()])[:12]
directory=Path('artifacts/designs')/(config['name']+'-'+identity)
manifest,blocks=prepare(config,directory)
counts=[];outputs=[];physical_calls=0;branch_differences=[];matching=[]
for pair,jobs in blocks:
    requests=[];root_lengths={}
    for job in jobs:requests.extend(manager_requests(job,pair,counter))
    unique,_=shared_manager_requests(requests);physical_calls+=len(unique)+len(jobs)
    counts.extend(len(counter.token_ids(r['prompt'])) for r in requests)
    for job in jobs:
        fake={}
        for index,branch in enumerate(job['branches']):
            text=canonical(lossless_summary(branch));outputs.append(len(counter.tokenizer.encode(text,add_special_tokens=False)))
            fake[(job['trial']['trial_id'],'manager'+str(index))]={'response':{'text':text,'finish_reason':'stop'}}
        request=root_request(job,fake);length=len(counter.token_ids(request['prompt']));counts.append(length)
        root_lengths[job['trial']['trial_id']]=length
        if job.get('neutral'):branch_differences.extend(job['audit']['neutral_manager_token_residuals'])
    by_arm={j['trial']['arm']:j for j in jobs if j['trial']['world']==0}
    for prefix in ('near_decisive_','near_harmless_','numeric_'):
        for dose in (1,4):
            high=by_arm.get(prefix+'high'+str(dose));low=by_arm.get(prefix+'low'+str(dose))
            if not high or not low:continue
            if semantic_inventory(high['reports'])!=semantic_inventory(low['reports']):raise RuntimeError('Different claims in overlap control')
            if [r.identifier for r in high['reports']]!=[r.identifier for r in low['reports']]:raise RuntimeError('Different report order/slots')
            record={'pair_id':pair['pair_id'],'family':pair['evaluation']['family'],'contrast':prefix+str(dose),
                'report_slots':len(high['reports']),'same_distinct_claims':True,'same_ids_and_order':True,
                'root_reference_token_difference_high_minus_low':root_lengths[high['trial']['trial_id']]-root_lengths[low['trial']['trial_id']],
                'manager_prompt_token_differences_high_minus_low':[
                    len(counter.token_ids(next(r['prompt'] for r in requests if r['trial']['trial_id']==high['trial']['trial_id'] and r['stage']=='manager'+str(i))))-
                    len(counter.token_ids(next(r['prompt'] for r in requests if r['trial']['trial_id']==low['trial']['trial_id'] and r['stage']=='manager'+str(i)))) for i in (0,1)]}
            if prefix=='numeric_':
                key=high['audit']['false_numeric_key']
                for label,j in [('high',high),('low',low)]:
                    original=[r for r in j['reports'] if r.claim.key==key and r.operation_type not in ('copy','paraphrase')]
                    record[label+'_pair_character_similarity']=SequenceMatcher(None,original[0].text,original[1].text).ratio()
                if record['high_pair_character_similarity']<=record['low_pair_character_similarity']:raise RuntimeError('Numerical overlap manipulation not effective')
            else:
                for label,j in [('high',high),('low',low)]:record[label+'_rendering_audit']=j['audit']['rendering_audit']
            matching.append(record)
maximum=max(counts);output_max=max(outputs)
if maximum+config['max_output_tokens']>config['max_context_tokens']:raise RuntimeError('Reference input plus output allowance exceeds context')
if output_max>config['max_output_tokens']:raise RuntimeError('Lossless reference schema exceeds output cap')
record={'suite':config['name'],'config_sha256':digest(config),'manifest_sha256':digest(manifest),
        'source_sha256':source_sha256,'preflight_script_sha256':digest(Path(__file__).read_text()),
        'base_pairs':manifest['base_pairs'],'trajectories':manifest['trajectories'],
        'logical_calls':manifest['calls'],'physical_calls_after_declared_manager_reuse':physical_calls,
        'maximum_reference_prompt_tokens':maximum,'maximum_reference_summary_tokens':output_max,
        'context_tokens':config['max_context_tokens'],'output_cap':config['max_output_tokens'],
        'neutral_manager_residual_token_range':[min(branch_differences),max(branch_differences)] if branch_differences else None,
        'ineligible_targets':len(manifest['ineligible']),'gpu_inference_calls':0,'overlap_matching':matching,
        'caution':'Reference summaries check schema feasibility, not maximum arbitrary model output. Actual input lengths remain checked before every call; no truncation or hidden case removal.'}
immutable_json(Path('records/preflight')/(config['name']+'-'+identity+'.json'),record)
print(json.dumps({k:v for k,v in record.items() if k!='overlap_matching'}),flush=True)
