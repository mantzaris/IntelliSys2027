"""Small targeted replay using the existing adapter, ledger and output contract."""
from dataclasses import asdict
import json
from pathlib import Path
from .aux_analysis import false_finding_metrics
from .controls import neutral_report_control,semantic_inventory
from .generation import oracle
from .information import possible_decisions
from .mechanism import transport_metrics,necessary_keys,injected_value_metrics
from .metrics import parse,score_root,same_value,score_assertions
from .models import reuse_or_load
from .policies import make_prompt
from .replay import execute_requests
from .reports import registry,ancestry_registry
from .schema import canonical,digest
from .storage import Ledger,immutable_json
from .targeted_design import source_pairs,plan_pair,branches_for


def shared_manager_requests(requests):
    """Freeze identical manager computations only within one world/repetition.

    This deliberately couples interventions, including bypass, to the same
    unaffected summaries. Independent stochastic repetitions never collapse.
    """
    unique={};mapping={}
    for request in requests:
        t=request['trial']
        key=(t['pair_id'],t['world'],t['repetition'],request['stage'],request['prompt'],request.get('max_output_tokens'))
        canonical_request=unique.setdefault(key,request)
        mapping[(t['trial_id'],request['stage'])]=(canonical_request['trial']['trial_id'],canonical_request['stage'])
    return list(unique.values()),mapping


def lossless_summary(reports):
    """Diagnostic transport of supplied assertions, never an oracle correction."""
    groups={}
    for r in reports:
        if r.operation_type=='administrative':continue
        for c in r.claims():
            key=canonical([c.key,'bool' if type(c.asserted_value) is bool else 'number',c.asserted_value])
            item=groups.setdefault(key,{'key':c.key,'value':c.asserted_value,'reports':[]})
            item['reports'].append(r.identifier)
    return {'assertions':list(groups.values()),'unresolved':[],'candidate_assessments':[],'choice':None,'probabilities':{}}


def manager_requests(job,pair,model):
    if job.get('neutral'):
        repeated=job['reports'];job['reports']=neutral_report_control(repeated,model.tokenizer)
        job['audit']['neutral_manager_token_residuals']=[
            len(model.token_ids(make_prompt(job['world'],a,job['trial']['policy'],role='manager')))-
            len(model.token_ids(make_prompt(job['world'],b,job['trial']['policy'],role='manager')))
            for a,b in zip(branches_for(job,pair),branches_for({**job,'reports':repeated},pair))]
    branches=branches_for(job,pair);job['branches']=branches
    architecture=job['trial']['organization']
    if architecture in ('flat','lossless'):return []
    return [{'trial':job['trial'],'stage':'manager'+str(i),
             'prompt':make_prompt(job['world'],rs,job['trial']['policy'],role='manager',
                                  extra_evidence=job.get('extra_evidence'))} for i,rs in enumerate(branches)]


def root_request(job,calls):
    t=job['trial'];architecture=t['organization'];summaries=[];objects=[];statuses=[]
    if architecture=='lossless':
        for i,branch in enumerate(job['branches']):
            obj=lossless_summary(branch)
            parsed,status=parse(canonical(obj),job['world']['tie_order']+['NONE'],manager=True)
            summaries.append({'manager':i,'summary':obj,'parse_status':'valid'});objects.append(parsed);statuses.append(status)
    elif architecture!='flat':
        for i in range(2):
            response=calls[(t['trial_id'],'manager'+str(i))]['response']
            obj,status=parse(response['text'],job['world']['tie_order']+['NONE'],manager=True)
            if response['finish_reason']=='length':obj=None;status='truncated'
            objects.append(obj);statuses.append(status)
            summaries.append({'manager':i,'summary':obj if obj is not None else response['text'],'parse_status':status})
    job['summary_objects']=objects;job['summary_statuses']=statuses
    visible=job['reports'] if architecture in ('flat','bypass') else []
    return {'trial':t,'stage':'root','prompt':make_prompt(job['world'],visible,t['policy'],
        summaries=summaries if architecture!='flat' else None,public_registry=registry(job['required']+job['reports']),
        public_ancestry=ancestry_registry(job['reports']),extra_evidence=job.get('extra_evidence'))}


def score_job(job,pair,calls):
    t=job['trial'];root=calls[(t['trial_id'],'root')];response=root['response']
    score=score_root(response,job['world'],oracle(job['world']),job['required'],job['reports'])
    if any(s!='valid' for s in job['summary_statuses']):score.update(correct=False,operational_failure=True)
    obj,_=parse(response['text'],job['world']['tie_order']+['NONE'])
    if response['finish_reason']=='length':obj=None
    current=[c for (trial_id,_),c in calls.items() if trial_id==t['trial_id']]
    sums={k:sum(c['response'][k] for c in current) for k in ('input_tokens','output_tokens','allocated_inference_seconds')}
    if t['organization']=='flat':
        summaries=[parse(canonical(lossless_summary(job['reports'])),job['world']['tie_order'],manager=True)[0]]
    else:summaries=job['summary_objects']
    transport=transport_metrics(job['world'],job['required'],summaries,score['correct'],job['target_key'])
    for metric in ('scope_transfer_count','incompatible_scope_merge_count','unconsolidated_equivalent_count'):
        transport['summary_'+metric]=sum(score_assertions(o,job['required'],job['reports'])[metric] for o in summaries) if t['organization']!='flat' else None
    if t['organization']=='bypass':
        delivered=possible_decisions(job['world'],job['required'],job['reports'])
        transport['root_raw_report_access_sufficient']=delivered=={oracle(job['world'])['answer']}
    unique=job.get('designated_unique_key')
    if unique:
        expected=next(c.asserted_value for r in job['required'] for c in r.claims() if c.key==unique)
        transport['unique_clause_emitted_correct']=any(o and any(k==unique and same_value(v,expected) for k,v,_ in o['assertions']) for o in summaries)
        transport['unique_clause_retained']=unique in transport['transport_retained_keys']
    if 'injected_key' in job:score.update(false_finding_metrics(obj,job['injected_key'],job['true_value']))
    if 'false_numeric_key' in job['audit']:
        value=job['audit']['true_numeric_value']
        score.update(injected_value_metrics(obj,job['audit']['false_numeric_key'],value,value+1))
    if 'superseded_keys' in job:
        score['superseded_assertions_emitted']=sum(k in job['superseded_keys'] for k,v,refs in obj['assertions']) if obj else None
    return {**t,'kind':pair['evaluation']['kind'],'family':pair['evaluation']['family'],
        'decision_changed':pair['evaluation']['decision_changed'],'aliases':job['aliases'],
        'common_class':job['common_class'],'selected_scope':job['target_key'],
        **score,**transport,'audit':job['audit'],'displayed_reports':len(job['reports']),
        'distinct_claims':len(semantic_inventory(job['reports'])),
        'original_model_worker_calls':0,'distinct_evidence_sources':len({s for r in job['reports'] for c in r.claims() for s in c.source_identifiers}),
        'calls':len(current),'input_tokens':sums['input_tokens'],'output_tokens':sums['output_tokens'],
        'inference_seconds_allocated':sums['allocated_inference_seconds'],
        'request_hashes':[c['request_hash'] for c in current]}


def prepare(config,root):
    pairs=source_pairs(config);blocks=[];excluded=[]
    for pair in pairs:
        jobs,ineligible=plan_pair(pair,config);blocks.append((pair,jobs));excluded.extend([{'pair_id':pair['pair_id'],**r} for r in ineligible])
    manifest={'config':config,'base_pairs':len(pairs),'pairs_sha256':digest(pairs),
              'trajectories':sum(len(jobs) for _,jobs in blocks),
              'calls':sum(1 if j['trial']['organization'] in ('flat','lossless') else 3 for _,jobs in blocks for j in jobs),
              'ineligible':excluded,'per_pair_trajectories':{p['pair_id']:len(jobs) for p,jobs in blocks}}
    manifest['call_interpretation']='Logical decision-graph calls. Identical manager inputs are explicitly shared within world/repetition; physical accepted calls are separately inventoried.'
    immutable_json(root/'config.json',config);immutable_json(root/'pairs.json',pairs)
    immutable_json(root/'manifest.json',manifest)
    immutable_json(root/'planned-inputs.json',[{'trial':j['trial'],'reports':[asdict(r) for r in j['reports']],
        'aliases':j['aliases'],'target_key':j['target_key'],'audit':j['audit']} for _,jobs in blocks for j in jobs])
    suffix='' if config['status']=='frozen' else '-candidate-'+digest(config)[:12]
    immutable_json(Path('records/manifests')/(config['name']+suffix+'.json'),manifest)
    return manifest,blocks


def run(config,model=None):
    if config['status']!='frozen':raise ValueError('Targeted protocol must be frozen before inference')
    root=Path('artifacts/runs')/config['name']
    immutable_json(root/'implementation.json',{p.name:p.read_text() for p in Path(__file__).parent.glob('*.py')})
    manifest,blocks=prepare(config,root)
    model,loaded=reuse_or_load(config['model'],config,model)
    ledger=Ledger(root/config['model']);ledger.event('run_start',model_load_seconds=model.load_seconds if loaded else 0,settings=model.settings)
    for pair,jobs in blocks:
        if (root/config['model']/'scores'/(pair['pair_id']+'.json')).exists():continue
        managers=[]
        for job in jobs:managers.extend(manager_requests(job,pair,model))
        unique,mapping=shared_manager_requests(managers)
        accepted=execute_requests(unique,model,ledger)
        calls={destination:accepted[source] for destination,source in mapping.items()}
        roots=[root_request(job,calls) for job in jobs]
        calls.update(execute_requests(roots,model,ledger))
        scores=[score_job(job,pair,calls) for job in jobs]
        immutable_json(root/config['model']/'scores'/(pair['pair_id']+'.json'),scores)
        ledger.event('cluster_complete',pair_id=pair['pair_id'],trajectories=len(scores))
        print(canonical({'targeted_cluster_complete':pair['pair_id'],'trajectories':len(scores)}),flush=True)
    ledger.event('run_complete',base_pairs=len(blocks));ledger.close()
    return model
