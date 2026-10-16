"""Bounded fresh scheduling confirmation: selective versus balanced objectives.

Reuses typed reports, hierarchy, batching, ledger and scoring. No new agent
framework, evaluator hints or model-generated paraphrases are introduced.
"""
from collections import defaultdict
from dataclasses import asdict
import json
from pathlib import Path
import time
from .generation import generate_pair
from .controls import semantic_inventory
from .models import reuse_or_load
from .replay import execute_requests
from .reports import make_reports
from .schema import digest, canonical
from .storage import Ledger, immutable_json
from .targeted_design import repeat_selected
from .targeted_replay import manager_requests, root_request, score_job, shared_manager_requests

ARMS=('single','selective_exact','selective_paraphrase','balanced_exact','balanced_paraphrase')


def pairs_for(config):
    pairs=[generate_pair('heldout',i,2) for i in config['pair_indices']]
    if [p['pair_id'] for p in pairs]!=config['pair_ids']:raise ValueError('Frozen pair identities changed')
    if any(p['evaluation']['kind']!='schedule' for p in pairs):raise ValueError('Scheduling confirmation only')
    return pairs


def plan_pair(pair, config, model):
    position=config['pair_indices'].index(pair['index'])%3
    selected_candidate=sorted(c['identifier'] for c in pair['worlds'][0]['candidates'])[position]
    jobs=[]
    for wi in config['worlds']:
        world=pair['worlds'][wi];rs=make_reports(world,'heldout',pair['seed'])
        objectives=[r for r in rs if r.claim.task_identifier=='objective']
        selected=next(r for r in objectives if r.claim.candidate_identifier==selected_candidate)
        for arm in ARMS:
            shown=list(rs)
            if arm!='single':
                for target in (objectives if arm.startswith('balanced') else [selected]):
                    shown=repeat_selected(shown,target,config['presentations'],arm.endswith('paraphrase'),'heldout')
            if semantic_inventory(shown)!=semantic_inventory(rs):raise ValueError('Repetition changed distinct information')
            for rep in range(config['stochastic_repetitions']):
                trial={'suite':config['name'],'pair_id':pair['pair_id'],'world':wi,'model':model,
                       'arm':arm,'repetition':rep,'organization':'hierarchical','policy':'ordinary'}
                trial['trial_id']=digest(trial)[:24]
                jobs.append({'trial':trial,'reports':shown,'required':rs,'world':world,'target_key':selected.claim.key,
                    'aliases':[],'common_class':'objective','audit':{'target_candidate':selected_candidate,
                        'target_sorted_id_position':position,'target_rule':'rank cycles 0/1/2 over frozen base order; identical candidate across worlds; no correctness-dependent selection',
                        'repeated_scope_keys':sorted(r.claim.key for r in (objectives if arm.startswith('balanced') else [selected])) if arm!='single' else [],
                        'original_worker_executions':len({r.claim.verification_execution_identifier for r in rs}),
                        'added_displayed_reports':len(shown)-len(rs)}})
    return jobs


def prepare(config):
    pairs=pairs_for(config)
    plans=[(p,{m:plan_pair(p,config,m) for m in config['models']}) for p in pairs]
    trajectories=sum(len(jobs) for _,models in plans for jobs in models.values())
    manifest={'config':config,'base_pairs':len(pairs),'pairs_sha256':digest(pairs),
        'trajectories':trajectories,'logical_calls':3*trajectories,
        'planned_inputs_sha256':digest([{'trial':j['trial'],'reports':[asdict(r) for r in j['reports']],'audit':j['audit']}
            for _,models in plans for jobs in models.values() for j in jobs]),
        'per_model_trajectories':{m:sum(len(models[m]) for _,models in plans) for m in config['models']},
        'comparison':'Five hierarchical ordinary-synthesis arms; identical required information. Balanced repeats three objectives and adds more tokens than selective emphasis. This contrast does not isolate balance from length/dose; root diagnostic neutral controls are separate.'}
    return manifest,plans


def run(config,alias,budget_seconds):
    if config['status']!='frozen' or alias not in config['models']:raise ValueError('Frozen eligible model required')
    start=time.monotonic();directory=Path('artifacts/runs',config['name'])
    manifest,plans=prepare(config)
    immutable_json(directory/'manifest.json',manifest)
    immutable_json(directory/'pairs.json',[p for p,_ in plans])
    immutable_json(directory/'implementation.json',{p.name:p.read_text() for p in Path(__file__).parent.glob('*.py')})
    model,_=reuse_or_load(alias,config)
    ledger=Ledger(directory/alias)
    ledger.event('run_start',settings=model.settings,model_load_seconds=model.load_seconds,
                 remaining_wall_budget_seconds=budget_seconds)
    for pair,models in plans:
        score_path=directory/alias/'scores'/(pair['pair_id']+'.json')
        if score_path.exists():continue
        # Stop only between complete clusters. A hard outer wall cap records any
        # interrupted in-flight call as ambiguous; accepted calls remain cached.
        if time.monotonic()-start>=budget_seconds:
            ledger.event('budget_exhausted',completed=False);ledger.close();return False
        jobs=models[alias];managers=[]
        for job in jobs:managers.extend(manager_requests(job,pair,model))
        unique,mapping=shared_manager_requests(managers)
        accepted=execute_requests(unique,model,ledger)
        calls={dest:accepted[src] for dest,src in mapping.items()}
        roots=[root_request(job,calls) for job in jobs]
        calls.update(execute_requests(roots,model,ledger))
        rows=[score_job(job,pair,calls) for job in jobs]
        immutable_json(score_path,rows)
        ledger.event('cluster_complete',pair_id=pair['pair_id'],trajectories=len(rows))
        print(canonical({'objective_cluster_complete':pair['pair_id'],'model':alias,'trajectories':len(rows)}),flush=True)
    ledger.event('run_complete',base_pairs=len(plans));ledger.close();return True
