"""Smaller live-worker study with logged access and preserved essential coverage."""
from dataclasses import asdict, replace
from pathlib import Path
from .assignments import assign, access_view, coverage, allocate_total_tokens,bind_executions
from .generation import generate
from .metrics import parse, score_root,same_value
from .models import reuse_or_load
from .policies import CONTRACT, make_prompt
from .reports import make_reports, registry, render
from .schema import canonical,digest,Report
from .storage import Ledger,immutable_json
from .replay import execute_requests
from .information import possible_decisions


def run_live(config,alias,model=None):
    if config.get('status') not in ('frozen','development_live') or config.get('interface_version')!=7:
        raise ValueError('Live protocol must be frozen after replay validation')
    model,loaded_here=reuse_or_load(alias,config,model)
    directory=Path('artifacts/runs')/config['name'];ledger=Ledger(directory/alias)
    ledger.event('run_start',settings=model.settings,model_load_seconds=model.load_seconds if loaded_here else 0,
                 engine_reused=not loaded_here)
    split='live_development' if config['status']=='development_live' else 'live'
    pairs=[p for p in generate(split,config['generated_pairs'],config.get('benchmark_version',2)) if p['evaluation']['kind']=='schedule']
    immutable_json(directory/'pairs.json',pairs);immutable_json(directory/'config.json',config)
    immutable_json(directory/'implementation.json',{p.name:p.read_text() for p in Path(__file__).parent.glob('*.py')})
    immutable_json(directory/'manifest.json',{'config':config,'pairs_sha256':digest(pairs),
                   'count_scope':'per_model; calls are planned maxima before explicit resource failures','models':config.get('models',[alias]),
                   'trajectories':len(pairs)*len(config['worlds'])*5*config['stochastic_repetitions'],
                   'calls':len(pairs)*len(config['worlds'])*33*config['stochastic_repetitions'],
                   'total_trajectories':len(pairs)*len(config['worlds'])*5*config['stochastic_repetitions']*len(config.get('models',[alias])),
                   'total_calls':len(pairs)*len(config['worlds'])*33*config['stochastic_repetitions']*len(config.get('models',[alias]))})
    for pair in pairs:
        jobs=[];all_worker_requests=[]
        for world_index in config['worlds']:
            world=pair['worlds'][world_index]
            truth_reports=make_reports(world,'live',pair['seed'])
            for allocation,allowance in [('nonoverlap','added'),('exact_overlap','fixed'),('near_overlap','fixed'),
                                         ('exact_overlap','added'),('near_overlap','added')]:
                for repetition in range(config['stochastic_repetitions']):
                    trial={'pair_id':pair['pair_id'],'world':world_index,'allocation':allocation,'allowance':allowance,
                           'model':alias,'repetition':repetition,'suite':config['name']}
                    trial['trial_id']=digest(trial)[:24]
                    tasks=bind_executions(assign(world,allocation,allowance,config['worker_total_output_allowance']),trial)
                    def worker_request(task):
                        scopes=[r for r in truth_reports if r.claim.task_identifier==task.family and
                                (task.resource is None or r.claim.entity_identifier==task.resource)]
                        visible=access_view(world,task)
                        view={'data':visible,'registry':registry(scopes)}
                        prompt=('Verify only your assigned scope using the supplied task data. Compute every assigned finding; '
                                'do not choose a final candidate. Use choice=null and probabilities={}. '
                                'Cite your assigned source identifier in reports. '+CONTRACT+'\n'+canonical({
                                    'assignment':asdict(task),'access':view}))
                        return {'trial':trial,'stage':task.identifier,'prompt':prompt,'max_output_tokens':task.output_cap},view
                    def prompt_tokens(task):
                        request,_=worker_request(task)
                        return len(model.tokenizer.encode(model.prepare(request['prompt']),add_special_tokens=False))
                    baseline=bind_executions(assign(world,'nonoverlap','added',config['worker_total_output_allowance']),
                                             {**trial,'allocation':'nonoverlap','allowance':'added'})
                    total_budget=sum(prompt_tokens(a)+a.output_cap for a in baseline)
                    if allowance=='fixed':
                        for _ in range(5):
                            tasks=allocate_total_tokens(tasks,[prompt_tokens(a) for a in tasks],total_budget)
                        if sum(prompt_tokens(a)+a.output_cap for a in tasks)>total_budget:
                            tasks=[replace(a,output_cap=a.output_cap-1) for a in tasks]
                        assert sum(prompt_tokens(a)+a.output_cap for a in tasks)<=total_budget
                    requests=[];views={}
                    for task in tasks:
                        request,view=worker_request(task);requests.append(request);views[task.identifier]=view
                    all_worker_requests.extend(requests)
                    jobs.append({'trial':trial,'world':world,'world_index':world_index,'truth_reports':truth_reports,
                                 'tasks':tasks,'views':views,'total_budget':total_budget,
                                 'allocated_budget':sum(prompt_tokens(a)+a.output_cap for a in tasks)})
        # Batch independent workers across arms; no worker can read another output.
        worker_calls=execute_requests(all_worker_requests,model,ledger)
        for job in jobs:
            trial,world,truth_reports,tasks=(job[k] for k in ('trial','world','truth_reports','tasks'))
            reports=[];failures=[];unknown_scope_assertions=0;unsupported_sources=0
            for task in tasks:
                call=worker_calls[(trial['trial_id'],task.identifier)]
                obj,status=parse(call['response']['text'],world['tie_order']+['NONE'],manager=True)
                if call['response']['finish_reason']=='length':obj=None;status='truncated'
                if obj is None:failures.append(task.identifier);continue
                scopes={r.claim.key:r.claim for r in truth_reports if r.claim.task_identifier==task.family and
                        (task.resource is None or r.claim.entity_identifier==task.resource)}
                for i,(key,value,refs) in enumerate(obj['assertions']):
                    unsupported_sources+=not refs or any(ref!=task.source_identifier for ref in refs)
                    if key not in scopes:
                        unknown_scope_assertions+=1
                        continue  # Retained in raw output and counted; no invented scope is admitted.
                    # Provenance comes from actual orchestrator access, not invented model sources.
                    claim=replace(scopes[key],asserted_value=value,source_identifiers=(task.source_identifier,),
                                  verification_execution_identifier=task.execution_identifier)
                    rid=task.identifier+'_'+str(i)
                    reports.append(Report(rid,claim,render(claim,'live')))
            job.update(reports=reports,failures=failures,unknown_scope_assertions=unknown_scope_assertions,
                       unsupported_sources=unsupported_sources)
            prompt=make_prompt(world,reports,config['manager_policy'],public_registry=registry(truth_reports))
            job['root_prompt']=prompt
            job['root_input_tokens']=len(model.tokenizer.encode(model.prepare(prompt),add_special_tokens=False))
        baseline_root_inputs={(j['world_index'],j['trial']['repetition']):j['root_input_tokens'] for j in jobs
                              if j['trial']['allocation']=='nonoverlap'}
        root_requests=[]
        for job in jobs:
            trial=job['trial']
            worker_spent=sum(c['response']['input_tokens']+c['response']['output_tokens']
                             for (tid,stage),c in worker_calls.items() if tid==trial['trial_id'])
            baseline_total=job['total_budget']+baseline_root_inputs[(job['world_index'],trial['repetition'])]+config['max_output_tokens']
            root_cap=config['max_output_tokens']
            if trial['allowance']=='fixed':root_cap=min(root_cap,baseline_total-worker_spent-job['root_input_tokens'])
            root_cap=min(root_cap,config['max_context_tokens']-job['root_input_tokens'])
            job.update(worker_spent=worker_spent,baseline_trajectory_allowance=baseline_total,root_cap=root_cap)
            if root_cap<64:
                # No raw input is dropped or shortened to hide resource displacement.
                job['root_not_executed']='insufficient_trajectory_token_allowance_or_context'
                ledger.event('root_not_executed',trial_id=trial['trial_id'],reason=job['root_not_executed'],
                             root_input_tokens=job['root_input_tokens'],remaining_output_allowance=root_cap)
            else:
                job['root_not_executed']=None
                root_requests.append({'trial':trial,'stage':'root','prompt':job['root_prompt'],'max_output_tokens':root_cap})
        roots=execute_requests(root_requests,model,ledger)
        for job in jobs:
            trial,world,world_index,truth_reports,tasks,reports,failures=(job[k] for k in
                ('trial','world','world_index','truth_reports','tasks','reports','failures'))
            root_call=roots.get((trial['trial_id'],'root'))
            # An unexecuted root is a resource failure, never a fabricated model call.
            response=root_call['response'] if root_call else {'text':'','finish_reason':'not_executed'}
            score=score_root(response,world,pair['evaluation']['oracle'][world_index],truth_reports,reference_reports=reports)
            if not root_call:score.update(parse_status='resource_displacement',operational_failure=True,correct=False)
            if failures:score['correct']=False;score['operational_failure']=True
            possible=possible_decisions(world,truth_reports,reports)
            supported=len(possible)==1 and score['choice'] in possible
            score.update(information_available_for_unique_answer=len(possible)==1,
                         possible_answers_from_worker_assertions=sorted(possible),
                         epistemically_appropriate_choice=score['choice']==(next(iter(possible)) if len(possible)==1 else 'INSUFFICIENT'),
                         root_supported_correct=score['correct'] and supported,
                         unsupported_truth_hit=score['correct'] and not supported)
            calls=[c for (tid,stage),c in worker_calls.items() if tid==trial['trial_id']]+([root_call] if root_call else [])
            result={**trial,**score,'assignment_coverage':coverage(tasks,world),
                    'worker_unknown_scope_assertions':job['unknown_scope_assertions'],
                    'worker_unsupported_source_assertions':job['unsupported_sources'],
                    'worker_incorrect_claims':sum(not same_value(r.claim.asserted_value,t.claim.asserted_value)
                        for r in reports for t in truth_reports if r.claim.key==t.claim.key),
                    'baseline_total_worker_token_allowance':job['total_budget'],
                    'allocated_total_worker_token_allowance':job['allocated_budget'],
                    'baseline_total_trajectory_token_allowance':job['baseline_trajectory_allowance'],
                    'closed_worker_tokens_plus_root_allowance':job['worker_spent']+(job['root_input_tokens']+job['root_cap'] if root_call else 0),
                    'planned_root_input_tokens':job['root_input_tokens'],'allocated_root_output_tokens':max(0,job['root_cap']),
                    'root_not_executed':job['root_not_executed'],
                    'delivered_claims':len({r.claim.key for r in reports}),
                    'required_claims':len({r.claim.key for r in truth_reports}),
                    'worker_failures':failures,'actual_access':job['views'],
                    'worker_reports':[asdict(r) for r in reports],
                    'calls':len(calls),'request_hashes':[c['request_hash'] for c in calls],
                    'input_tokens':sum(c['response']['input_tokens'] for c in calls),
                    'output_tokens':sum(c['response']['output_tokens'] for c in calls),
                    'inference_seconds_allocated':sum(c['response']['allocated_inference_seconds'] for c in calls)}
            immutable_json(directory/alias/'scores'/(trial['trial_id']+'.json'),result)
            ledger.event('live_trial_complete',trial_id=trial['trial_id'])
        ledger.event('live_cluster_complete',pair_id=pair['pair_id'],trajectories=len(jobs))
    ledger.event('run_complete',base_pairs=len(pairs))
    ledger.close()
    return model
