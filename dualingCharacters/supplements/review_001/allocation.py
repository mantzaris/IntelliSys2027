"""Outcome-blind, whole-module allocation from fixed profiling timings only."""
from .common import ROOT,HERE,ARTIFACTS,read,write
from pcc.resources import sha256,used_seconds


def costs(timing, families, common=False):
    load=timing['load_seconds'];factor=1.35
    return {'memory':load+factor*(timing['memory_seconds']*families/16+(timing['common_seconds']*families/16 if common else 0)),
            'conflict':load+factor*timing['rollout_seconds']*8,
            'routing':load+factor*timing['rollout_seconds']*6,
            'severity':load+factor*timing['memory_seconds']*(16*2*2*3)/(16*2*3*3),
            'balanced':load+factor*timing['rollout_seconds']*24}


def choose(timing, review_used, project_used):
    available=max(0,min(7200-review_used,96*3600-1800-project_used)-90)
    chosen=None
    for include_b in (True,False):
        for n in (240,120,64,32):
            estimates=costs(timing,n)
            required=estimates['memory']+(estimates['conflict'] if include_b else 0)
            if required<=available:
                chosen={'families':n,'common_input':False,'stages':['memory']+(['conflict'] if include_b else []),
                        'estimated_seconds':{k:estimates[k] for k in ['memory']+(['conflict'] if include_b else [])}}
                break
        if chosen:break
    if chosen is None:chosen={'families':0,'common_input':False,'stages':[],'estimated_seconds':{}}
    if 'conflict' in chosen['stages']:
        with_common=costs(timing,chosen['families'],True)
        extra=with_common['memory']-chosen['estimated_seconds']['memory']
        if sum(chosen['estimated_seconds'].values())+extra<=available:
            chosen['common_input']=True;chosen['estimated_seconds']['memory']=with_common['memory']
        for stage in ('routing','severity','balanced'):
            if sum(chosen['estimated_seconds'].values())+with_common[stage]<=available:
                chosen['stages'].append(stage);chosen['estimated_seconds'][stage]=with_common[stage]
    return {**chosen,'available_seconds_after_contingency_and_margin':available,'prior_review_seconds':review_used,
            'prior_project_seconds':project_used,'selection_basis':'Timing only; no diagnostic success/behavior outcomes inspected',
            'omitted_stages':{s:'resource gate; implementation retained' for s in ('memory','conflict','routing','severity','balanced') if s not in chosen['stages']}}


def review_seconds():
    latest={}
    path=ROOT/'artifacts/run_registry.jsonl'
    for line in path.read_text().splitlines():
        row=__import__('json').loads(line)
        if row['run_id'].startswith('review001-'):latest[row['run_id']]=row
    return sum(r['gpu_reserved_seconds'] for r in latest.values())


def freeze_allocation():
    from .inputs import selected_families
    path=ROOT/'artifacts/runs/review001-profile-17-v1/timing_only.json'
    result=choose(read(path),review_seconds(),used_seconds(ROOT/'artifacts/run_registry.jsonl'))
    result.update(timing_sha256=sha256(path),protocol_sha256=sha256(HERE/'PROTOCOL.md'),
                  bindings_sha256=sha256(ARTIFACTS/'bindings.json'),
                  selected_families=selected_families(result['families']) if result['families'] else [])
    destination=ARTIFACTS/'allocation.json'
    if destination.exists():return read(destination)
    write(destination,result);return result
