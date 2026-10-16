"""Smaller live-worker study with logged access and preserved essential coverage."""
from dataclasses import asdict, replace
from pathlib import Path
from .assignments import assign, access_view, coverage, allocate_total_tokens
from .generation import generate
from .metrics import parse, score_root
from .models import LocalModel
from .policies import CONTRACT, make_prompt
from .reports import make_reports, registry, render
from .schema import canonical,digest,Report
from .storage import Ledger,immutable_json
from .replay import execute_requests


def run_live(config,alias):
    if config.get('status') not in ('frozen','development_live') or config.get('interface_version')!=5:
        raise ValueError('Live protocol must be frozen after replay validation')
    model=LocalModel(alias,config['max_context_tokens'],config['max_output_tokens'],
                     config['temperature'],config['top_p'],config['batch_size'],True)
    directory=Path('artifacts/runs')/config['name'];ledger=Ledger(directory/alias)
    pairs=[p for p in generate('live',config['generated_pairs']) if p['evaluation']['kind']=='schedule']
    immutable_json(directory/'pairs.json',pairs);immutable_json(directory/'config.json',config)
    for pair in pairs:
        for world_index in config['worlds']:
            world=pair['worlds'][world_index]
            truth_reports=make_reports(world,'live',pair['seed'])
            for allocation,allowance in [('nonoverlap','added'),('exact_overlap','fixed'),('near_overlap','fixed'),
                                         ('exact_overlap','added'),('near_overlap','added')]:
                for repetition in range(config['stochastic_repetitions']):
                    trial={'pair_id':pair['pair_id'],'world':world_index,'allocation':allocation,'allowance':allowance,
                           'model':alias,'repetition':repetition,'suite':config['name']}
                    trial['trial_id']=digest(trial)[:24]
                    tasks=assign(world,allocation,allowance,config['worker_total_output_allowance'])
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
                    baseline=assign(world,'nonoverlap','added',config['worker_total_output_allowance'])
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
                    worker_calls=execute_requests(requests,model,ledger)
                    reports=[];failures=[]
                    for task in tasks:
                        call=worker_calls[(trial['trial_id'],task.identifier)]
                        obj,status=parse(call['response']['text'],world['tie_order']+['NONE'],manager=True)
                        if call['response']['finish_reason']=='length':obj=None;status='truncated'
                        if obj is None:failures.append(task.identifier);continue
                        scopes={r.claim.key:r.claim for r in truth_reports if r.claim.task_identifier==task.family and
                                (task.resource is None or r.claim.entity_identifier==task.resource)}
                        for i,(key,value,refs) in enumerate(obj['assertions']):
                            if key not in scopes: continue  # Log unknown claims in raw output; no scope fabrication.
                            claim=replace(scopes[key],asserted_value=value,source_identifiers=(task.source_identifier,),
                                          verification_execution_identifier=task.execution_identifier)
                            rid=task.identifier+'_'+str(i)
                            reports.append(Report(rid,claim,render(claim,'live')))
                    # The root sees actual worker assertions, never oracle assertion values.
                    prompt=make_prompt(world,reports,config['manager_policy'],public_registry=registry(truth_reports))
                    roots=execute_requests([{'trial':trial,'stage':'root','prompt':prompt}],model,ledger)
                    root_call=roots[(trial['trial_id'],'root')]
                    score=score_root(root_call['response'],world,pair['evaluation']['oracle'][world_index],truth_reports,reference_reports=reports)
                    if failures:score['correct']=False;score['operational_failure']=True
                    calls=list(worker_calls.values())+[root_call]
                    result={**trial,**score,'assignment_coverage':coverage(tasks,world),
                            'baseline_total_worker_token_allowance':total_budget,
                            'allocated_total_worker_token_allowance':sum(prompt_tokens(a)+a.output_cap for a in tasks),
                            'delivered_claims':len({r.claim.key for r in reports}),
                            'required_claims':len({r.claim.key for r in truth_reports}),
                            'worker_failures':failures,'actual_access':views,
                            'worker_reports':[asdict(r) for r in reports],
                            'input_tokens':sum(c['response']['input_tokens'] for c in calls),
                            'output_tokens':sum(c['response']['output_tokens'] for c in calls),
                            'inference_seconds_allocated':sum(c['response']['allocated_inference_seconds'] for c in calls)}
                    immutable_json(directory/alias/'scores'/(trial['trial_id']+'.json'),result)
                    ledger.event('live_trial_complete',trial_id=trial['trial_id'])
