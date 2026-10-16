"""Information-availability checks for deliberately lossy report admission."""
from itertools import product


def possible_decisions(world,required_reports,delivered_reports):
    """Answers compatible with visible reports; absent facts are never filled by truth.

    Required scopes come from orchestration, not assertion values. This small
    enumeration treats contradictory/missing Boolean results as unknown and
    includes objective order/tie representatives when objective values are absent.
    """
    scopes={c.key:c for r in required_reports for c in r.claims()}
    values={key:set() for key in scopes}
    for r in delivered_reports:
        if r.operation_type=='administrative':continue
        for c in r.claims():
            if c.key in values:values[c.key].add((type(c.asserted_value).__name__,c.asserted_value))
    states={};objectives={}
    for cid in world['tie_order']:
        mandatory=[];objective=None
        for key,c in scopes.items():
            if c.candidate_identifier!=cid:continue
            seen=values[key]
            if c.task_identifier=='objective':
                if len(seen)==1 and next(iter(seen))[0] in ('int','float'):objective=next(iter(seen))[1]
            else:
                mandatory.append(next(iter(seen))[1] if len(seen)==1 and next(iter(seen))[0]=='bool' else None)
        states[cid]=[False] if False in mandatory else ([True] if mandatory and all(v is True for v in mandatory) else [False,True])
        objectives[cid]=objective
    known=sorted({v for v in objectives.values() if v is not None})
    representatives=sorted({0,*known,(max(known)+1 if known else 1),
                            *((a+b)/2 for a,b in zip(known,known[1:]))})
    candidates=world['tie_order'];answers=set()
    for feasibility in product(*(states[c] for c in candidates)):
        eligible=[c for c,v in zip(candidates,feasibility) if v]
        if not eligible:answers.add('NONE');continue
        for costs in product(*([objectives[c]] if objectives[c] is not None else representatives for c in eligible)):
            answers.add(min(zip(eligible,costs),key=lambda item:(item[1],candidates.index(item[0])))[0])
    return answers
