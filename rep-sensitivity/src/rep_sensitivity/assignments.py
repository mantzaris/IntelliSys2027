"""Live-worker scope allocation and explicit minimal information access."""
from dataclasses import dataclass, asdict, replace
from .schema import digest


@dataclass(frozen=True)
class Assignment:
    identifier: str
    family: str
    resource: str | None
    candidates: tuple[str,...]
    source_identifier: str
    execution_identifier: str
    output_cap: int


def assign(world, policy, allowance='added', total_output_allowance=4096):
    if world['kind']!='schedule': raise ValueError('Live study is scheduling only')
    if policy not in ('nonoverlap','exact_overlap','near_overlap'): raise ValueError(policy)
    families=['precedence_release','resource','deadline_downtime','objective']
    tasks=[(f,None) for f in families]
    if policy=='exact_overlap': tasks += [('resource',None),('resource',None)]
    elif policy=='near_overlap': tasks += [('resource',r) for r in sorted(world['capacities'])[:2]]
    cap=total_output_allowance//len(tasks) if allowance=='fixed' else total_output_allowance//4
    source='world_'+digest(world)[:12]
    return [Assignment('worker'+str(i),f,r,tuple(world['tie_order']),source,
                       'execute_'+digest([source,policy,allowance,i])[:12],cap) for i,(f,r) in enumerate(tasks)]


def access_view(world,assignment):
    """Do not give workers peer reports, evaluator labels, or irrelevant task data."""
    ids=set(assignment.candidates)
    view={'kind':'schedule','semantics':'non-preemptive, half-open [start,start+duration)',
          'candidates':[c for c in world['candidates'] if c['identifier'] in ids],
          'jobs':[{'identifier':j['identifier'],'duration':j['duration']} for j in world['jobs']]}
    if assignment.family=='precedence_release':
        view['precedence']=world['precedence']
        for v,j in zip(view['jobs'],world['jobs']): v['release']=j['release']
    elif assignment.family=='resource':
        resources=[assignment.resource] if assignment.resource else list(world['capacities'])
        view['capacities']={r:world['capacities'][r] for r in resources}
        for v,j in zip(view['jobs'],world['jobs']): v['demands']={r:j['demands'].get(r,0) for r in resources}
    elif assignment.family=='deadline_downtime':
        view['downtime']=world['downtime']
        for v,j in zip(view['jobs'],world['jobs']): v.update(deadline=j['deadline'],demands=j['demands'])
    return view


def coverage(assignments,world):
    required={(f,c) for f in ('precedence_release','resource','deadline_downtime','objective') for c in world['tie_order']}
    delivered={(a.family,c) for a in assignments if a.resource is None for c in a.candidates}
    return {'required_assignments':len(required),'covered_assignments':len(required&delivered),
            'worker_calls':len(assignments),'total_output_cap':sum(a.output_cap for a in assignments),
            'warning':'Output allowance is not equal compute; actual input/output tokens and elapsed time must be measured.'}


def allocate_total_tokens(assignments,input_tokens,total_tokens):
    """Combined input/output allowance; this is not a claim of FLOP equivalence."""
    available=total_tokens-sum(input_tokens)
    if available < 32*len(assignments):
        raise ValueError('Token allowance cannot support all essential workers; do not drop coverage')
    cap=available//len(assignments)
    return [replace(a,output_cap=cap) for a in assignments]
