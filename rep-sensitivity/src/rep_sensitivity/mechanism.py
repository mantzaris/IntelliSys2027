"""Evaluator-only relevance and observable transport diagnostics.

These annotations must never enter agent inputs. Boolean criticality is defined
by a single scoped truth-value flip with all other supplied findings fixed.
It is not a claim about the model's internal reasoning.
"""
from dataclasses import replace
from .controls import decision_from_claims
from .information import possible_decisions
from .metrics import same_value
from .schema import Report


def injected_value_metrics(obj,key,true_value,injected_value):
    if obj is None:return {'false_assertion_emitted':None,'false_assertion_adopted':None}
    values=[v for k,v,refs in obj['assertions'] if k==key]
    emitted=any(same_value(v,injected_value) for v in values)
    return {'false_assertion_emitted':emitted,
            'false_assertion_adopted':emitted and not any(same_value(v,true_value) for v in values) and key not in obj['unresolved']}


def critical_keys(world, reports):
    answer=decision_from_claims(world,reports)
    return {c.key for r in reports for c in r.claims() if type(c.asserted_value) is bool and
            decision_from_claims(world,reports,{c.key:not c.asserted_value})!=answer}


def relevance(world, reports, target):
    keys=critical_keys(world,reports)
    candidate=target.claim.candidate_identifier
    findings=[c for r in reports for c in r.claims() if c.candidate_identifier==candidate]
    feasible=all(c.asserted_value is True for c in findings if c.task_identifier!='objective')
    objectives={c.candidate_identifier:c.asserted_value for r in reports for c in r.claims() if c.task_identifier=='objective'}
    return {'task':target.claim.task_identifier,'candidate_feasible':feasible,
            'candidate_is_correct_choice':candidate==decision_from_claims(world,reports),
            'boolean_counterfactual_decisive':target.claim.key in keys,
            'objective_favoring_infeasible_candidate':target.claim.task_identifier=='objective' and not feasible
                and objectives[candidate]==min(objectives.values()),
            'critical_scope_count':len(keys)}


def necessary_keys(world,reports):
    """Scopes whose removal makes the choice underdetermined, including objectives."""
    answer=decision_from_claims(world,reports)
    claims={c.key:c for r in reports for c in r.claims()}
    return {key for key in claims if possible_decisions(world,reports,
            [Report('visible_'+str(i),c,'') for i,(k,c) in enumerate(claims.items()) if k!=key])!={answer}}


def transport_metrics(world, required, summaries, root_correct, selected_key=None, necessary_scopes=None):
    """Score explicit findings delivered across a summary boundary.

    Missing, altered/conflicted and uncontested exact retention partition critical
    scopes. An incompatible citation is observable scope transfer, not inferred
    hidden belief. Root-visible sufficiency uses only emitted scoped values.
    """
    claims={c.key:c for r in required for c in r.claims()}
    reference={r.identifier:{c.key for c in r.claims()} for r in required}
    values={k:[] for k in claims};unresolved=set();transfers=set();delivered=[]
    for index,obj in enumerate(summaries):
        if obj is None:continue
        unresolved.update(k for k in obj['unresolved'] if isinstance(k,str))
        for ordinal,(key,value,refs) in enumerate(obj['assertions']):
            for ref in refs:
                if ref in reference and key not in reference[ref]:transfers.update(reference[ref])
            if key not in claims:continue
            values[key].append(value)
            delivered.append(Report(f'summary{index}_{ordinal}',replace(claims[key],asserted_value=value),''))
    def state(key):
        if not values[key] and key not in transfers and key not in unresolved:return 'missing'
        if key in unresolved or not values[key] or any(not same_value(v,claims[key].asserted_value) for v in values[key]):return 'altered_or_conflicted'
        return 'retained'
    keys=critical_keys(world,required);states={k:state(k) for k in keys}
    delivered=[r for r in delivered if r.claim.key not in unresolved]
    possible=possible_decisions(world,required,delivered)
    answer=decision_from_claims(world,required)
    result={'critical_denominator':len(keys),'critical_states':states,
            'critical_retained':sum(s=='retained' for s in states.values()),
            'critical_missing':sum(s=='missing' for s in states.values()),
            'critical_altered_or_conflicted':sum(s=='altered_or_conflicted' for s in states.values()),
            'critical_citation_scope_transfers':len(keys&transfers),
            'visible_possible_choices':sorted(possible),'visible_truth_sufficient':possible=={answer},
            'all_critical_retained':all(s=='retained' for s in states.values()) if keys else None,
            'selected_retained':state(selected_key)=='retained' if selected_key in claims else None,
            'root_error_despite_sufficient_visible_truth':possible=={answer} and not root_correct}
    result['critical_retention']=result['critical_retained']/len(keys) if keys else None
    result['transport_retained_keys']=sorted(k for k in claims if state(k)=='retained')
    needed=necessary_keys(world,required) if necessary_scopes is None else necessary_scopes
    result.update(necessary_scope_denominator=len(needed),necessary_retained=sum(state(k)=='retained' for k in needed),
                  necessary_retention=sum(state(k)=='retained' for k in needed)/len(needed) if needed else None,
                  objective_denominator=sum(c.task_identifier=='objective' for c in claims.values()),
                  objectives_retained=sum(state(k)=='retained' for k,c in claims.items() if c.task_identifier=='objective'))
    distinct=needed-{selected_key}
    result.update(unrepeated_necessary_denominator=len(distinct),
                  unrepeated_necessary_retention=sum(state(k)=='retained' for k in distinct)/len(distinct) if distinct else None)
    return result
