"""Narrow one-proposition fresh-verification diagnostic with shared source data."""
from dataclasses import asdict,replace
from pathlib import Path
from .assignments import Assignment,access_view,worker_instruction
from .generation import generate_pair,oracle
from .live import WORKER_CONTRACT
from .metrics import parse,score_root,same_value
from .models import reuse_or_load
from .policies import make_prompt
from .replay import execute_requests
from .reports import make_reports,render,registry,ancestry_registry
from .schema import canonical,digest,Report
from .storage import immutable_json,Ledger
from .targeted_design import repeat_selected


def worker_request(pair,world,target,trial,index,cap,procedure):
    c=target.claim;source=c.source_identifiers[0]
    execution='e'+digest([trial['trial_id'],index])[:12]
    task=Assignment('verification'+str(index),c.task_identifier,c.entity_identifier if c.task_identifier=='resource' else None,
                    (c.candidate_identifier,),source,execution,cap)
    view=access_view(world,task);view['scope_registry']={c.key:c.scope()}
    prompt=('You compute one assigned verification finding. '+worker_instruction(task.family)+' '+
            ('Use integer unit-time occupancy checks.' if procedure=='integer_slots' else 'Use execution-event boundaries to check active intervals.')+
            ' '+WORKER_CONTRACT+'\n'+canonical({'assignment':asdict(task),'access':view}))
    return {'trial':trial,'stage':'worker'+str(index),'prompt':prompt,'max_output_tokens':cap},task,view


def worker_report(saved,task,target):
    response=saved['response'];obj,status=parse(response['text'],[],manager=True)
    if response['finish_reason']=='length':obj=None;status='truncated'
    values=[v for k,v,refs in obj['assertions'] if k==target.claim.key and type(v) is bool] if obj else []
    values=list(set(values))
    if len(values)!=1 or (obj and target.claim.key in obj['unresolved']):return None,{'valid':False,'value':None,'status':status}
    c=replace(target.claim,asserted_value=values[0],verification_execution_identifier=task.execution_identifier,
              parent_report_identifiers=(),operation_type='verification')
    report=Report('r'+digest(task.execution_identifier)[:9],c,render(c,'development'))
    return report,{'valid':True,'value':values[0],'correct':same_value(values[0],target.claim.asserted_value),'status':status,
        'unsupported_scope_assertions':sum(k!=target.claim.key for k,v,refs in obj['assertions']),
        'unsupported_source_citations':sum(any(ref!=task.source_identifier for ref in refs) for k,v,refs in obj['assertions'])}


def run(config,model=None):
    root=Path('artifacts/runs')/config['name'];alias=config['model']
    if config['status']!='frozen':raise ValueError('Fresh diagnostic requires prospective freeze')
    pairs=[generate_pair('development',i,2) for i in config['pair_indices']]
    immutable_json(root/'config.json',config);immutable_json(root/'pairs.json',pairs)
    immutable_json(root/'implementation.json',{p.name:p.read_text() for p in Path(__file__).parent.glob('*.py')})
    immutable_json(root/'manifest.json',{'config':config,'base_pairs':len(pairs),'trajectories':5*len(pairs),
        'maximum_physical_calls':12*len(pairs),'logical_calls_before_resource_displacement':16*len(pairs),
        'diagnostic_only':'Narrow resource predicate. Whole-live competence failed previously. No additional source observations or emitted witnesses; assigned procedures do not prove internal algorithm use.'})
    model,loaded=reuse_or_load(alias,config,model);ledger=Ledger(root/alias)
    ledger.event('run_start',settings=model.settings,model_load_seconds=model.load_seconds if loaded else 0)
    for pair in pairs:
        destination=root/alias/'scores'/(pair['pair_id']+'.json')
        if destination.exists():continue
        world=pair['worlds'][0];required=make_reports(world,'development',pair['seed'])
        resource_reports=sorted((r for r in required if r.claim.task_identifier=='resource'),key=lambda r:r.identifier)
        target=resource_reports[pair['seed']%len(resource_reports)]
        others=[r for r in required if r.identifier!=target.identifier]
        base={'suite':config['name'],'pair_id':pair['pair_id'],'model':alias,'world':0,'repetition':0,'arm':'original'}
        base['trial_id']=digest(base)[:24]
        request,task,view=worker_request(pair,world,target,base,0,config['worker_output_cap'],'event_boundaries')
        initial=execute_requests([request],model,ledger)[(base['trial_id'],'worker0')]
        report,initial_diagnostic=worker_report(initial,task,target)
        immutable_json(root/alias/'access'/(base['trial_id']+'.json'),{'assignment':asdict(task),'access':view,'peer_reports':False})
        rows=[];baseline_allowance=None
        for arm in ('original','copies','paraphrases','fresh_added','fresh_fixed'):
            trial={**base,'arm':arm};trial.pop('trial_id',None);trial['trial_id']=digest(trial)[:24]
            workers=[initial];diagnostics=[initial_diagnostic];reports=others+([report] if report else [])
            displacement=None
            if arm in ('copies','paraphrases') and report:
                reports=repeat_selected(reports,report,4,paraphrase=arm=='paraphrases')
            if arm.startswith('fresh'):
                reqs=[];tasks=[];views=[]
                for index in range(1,4):
                    r,t,v=worker_request(pair,world,target,trial,index,config['worker_output_cap'],
                                         'integer_slots' if index%2 else 'event_boundaries')
                    reqs.append(r);tasks.append(t);views.append(v)
                if arm=='fresh_fixed':
                    spent=initial['response']['input_tokens']+initial['response']['output_tokens']
                    remaining=baseline_allowance-spent-sum(len(model.token_ids(r['prompt'])) for r in reqs)
                    if remaining<32*len(reqs):displacement='worker inputs cannot fit matched trajectory allowance'
                    else:
                        cap=min(config['worker_output_cap'],remaining//len(reqs))
                        while True:
                            triples=[worker_request(pair,world,target,trial,index,cap,
                                'integer_slots' if index%2 else 'event_boundaries') for index in range(1,4)]
                            reqs,tasks,views=map(list,zip(*triples))
                            allowance=sum(len(model.token_ids(r['prompt']))+cap for r in reqs)
                            if allowance<=baseline_allowance-spent:break
                            cap-=1
                            if cap<32:displacement='worker inputs cannot fit matched trajectory allowance';break
                if displacement is None:
                    saved=execute_requests(reqs,model,ledger)
                    for index,(r,t,v) in enumerate(zip(reqs,tasks,views),1):
                        c=saved[(trial['trial_id'],'worker'+str(index))];workers.append(c)
                        emitted,diagnostic=worker_report(c,t,target);diagnostics.append(diagnostic)
                        if emitted:reports.append(emitted)
                        immutable_json(root/alias/'access'/(trial['trial_id']+'-'+str(index)+'.json'),
                            {'assignment':asdict(t),'access':v,'peer_reports':False,'effective_output_cap':r['max_output_tokens'],
                             'assigned_procedure':'integer_slots' if index%2 else 'event_boundaries'})
            prompt=make_prompt(world,reports,'ordinary',public_registry=registry(required),public_ancestry=ancestry_registry(reports),
                extra_evidence={'world':world,'authority_rule':'The task data are authoritative. Worker findings may contain errors; duplicates do not establish independent observations.'})
            root_cap=config['max_output_tokens'];root_call=None
            if arm=='fresh_fixed' and displacement is None:
                spent=sum(c['response']['input_tokens']+c['response']['output_tokens'] for c in workers)
                root_cap=min(root_cap,baseline_allowance-spent-len(model.token_ids(prompt)))
                if root_cap<32:displacement='complete root input cannot fit matched trajectory allowance'
            if displacement is None:
                root_call=execute_requests([{'trial':trial,'stage':'root','prompt':prompt,'max_output_tokens':root_cap}],model,ledger)[(trial['trial_id'],'root')]
                score=score_root(root_call['response'],world,oracle(world),required,reports)
            else:score={'correct':False,'operational_failure':True,'choice':None,'parse_status':'resource_displacement'}
            if any(not d['valid'] for d in diagnostics):score.update(correct=False,operational_failure=True)
            calls=workers+([root_call] if root_call else [])
            if arm=='original':
                baseline_allowance=sum(c['response']['input_tokens']+c['settings']['request_max_output_tokens'] for c in calls)
            total=sum(c['response']['input_tokens']+c['response']['output_tokens'] for c in calls)
            if arm=='fresh_fixed' and total>baseline_allowance:raise RuntimeError('Matched-resource allowance exceeded')
            rows.append({**trial,**score,'kind':'schedule','family':pair['evaluation']['family'],'decision_changed':pair['evaluation']['decision_changed'],
                'initial_worker':initial_diagnostic,'worker_diagnostics':diagnostics,'worker_calls':len(workers),'distinct_evidence_sources':1,
                'fresh_correct_after_initial_error':not initial_diagnostic.get('correct',False) and any(d.get('correct',False) for d in diagnostics[1:]),
                'additional_errors':sum(d.get('valid',False) and not d.get('correct',False) for d in diagnostics[1:]),
                'resource_displacement':displacement,'baseline_trajectory_token_allowance':baseline_allowance,
                'root_output_cap':root_cap if root_call else None,'total_tokens':total,
                'input_tokens':sum(c['response']['input_tokens'] for c in calls),'output_tokens':sum(c['response']['output_tokens'] for c in calls),
                'inference_seconds_allocated':sum(c['response']['allocated_inference_seconds'] for c in calls),
                'request_hashes':[c['request_hash'] for c in calls]})
        immutable_json(destination,rows);ledger.event('cluster_complete',pair_id=pair['pair_id'],trajectories=len(rows))
    ledger.event('run_complete',base_pairs=len(pairs));ledger.close();return model
