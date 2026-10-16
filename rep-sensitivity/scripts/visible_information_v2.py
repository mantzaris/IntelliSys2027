"""Strict report-interface semantics; no evaluator values repair missing inputs.

Scheduling objectives are nonnegative integers. Feasibility is a conjunction of
public mandatory scopes. This is the report-level abstraction, not enumeration
of unseen schedules: correlated underlying constraints cannot be reconstructed
without their task data. Inconsistent assertions have no consistent completion;
a separately named relaxed set treats only disputed/invalid scopes as unknown.
"""
from collections import defaultdict
from itertools import product
import math


def _answers(candidates, scopes, known, kind):
    states = {}; objectives = {}
    for cid in candidates:
        checks = [known.get(k) for k, c in scopes.items()
                  if c.candidate_identifier == cid and c.task_identifier != 'objective']
        states[cid] = [False] if False in checks else ([True] if checks and all(v is True for v in checks) else [False, True])
        objective_keys = [k for k,c in scopes.items() if c.candidate_identifier == cid and c.task_identifier == 'objective']
        if len(objective_keys) != 1: raise ValueError('Exactly one public objective scope per candidate required')
        objectives[cid] = known.get(objective_keys[0])
    # Enough integer representatives in every open interval to preserve all
    # weak orderings of up to N unknown objectives, including ties and zero.
    fixed = sorted({v for v in objectives.values() if v is not None})
    if kind != 'schedule': raise ValueError('This scorer is validated only for integer scheduling objectives')
    representatives = set(fixed)
    lower = 0
    for upper in fixed:
        representatives.update(range(lower, min(int(upper), lower + len(candidates))))
        lower = int(upper) + 1
    representatives.update(range(lower, lower + len(candidates)))
    answers = set()
    for feasibility in product(*(states[c] for c in candidates)):
        eligible = [c for c, good in zip(candidates, feasibility) if good]
        if not eligible: answers.add('NONE'); continue
        domains = [[objectives[c]] if objectives[c] is not None else sorted(representatives) for c in eligible]
        for values in product(*domains):
            answers.add(min(zip(eligible, values), key=lambda x: (x[1], candidates.index(x[0])))[0])
    return sorted(answers)


def visible_state(world, required, summaries):
    scopes = {c.key: c for r in required for c in r.claims()}
    references = {r.identifier: {c.key for c in r.claims()} for r in required}
    values = defaultdict(set); unresolved = set(); unknown = set(); invalid = set(); miscited = set()
    for entry in summaries:
        obj = entry.get('summary')
        if not isinstance(obj, dict): continue
        unresolved.update(k for k in obj.get('unresolved', []) if isinstance(k, str))
        for key, value, refs in obj.get('assertions', []):
            if key not in scopes: unknown.add(key); continue
            if any(ref in references and key not in references[ref] for ref in refs): miscited.add(key)
            objective = scopes[key].task_identifier == 'objective'
            valid = (type(value) in (int, float) and math.isfinite(value) and value >= 0 and value == int(value)) if objective else type(value) is bool
            if not valid: invalid.add(key); continue
            values[key].add(value)
    conflicts = {k for k, vs in values.items() if len(vs) > 1}
    known = {k: next(iter(vs)) for k, vs in values.items() if len(vs) == 1 and k not in invalid | unresolved}
    relaxed = _answers(world['tie_order'], scopes, known, world['kind'])
    missing = set(scopes) - set(values) - invalid
    # Unresolved flags with a single supplied value do not create a contradiction,
    # but they prevent treating that value as established.
    consistent = not conflicts and not invalid
    possible = relaxed if consistent else []
    justified = possible if len(possible) == 1 else []
    status = ('contradictory' if conflicts else 'invalid_values' if invalid else
              'sufficient_consistent' if len(possible) == 1 else 'incomplete_multiple_answers')
    return {'status': status, 'consistent': consistent, 'possible_answers': possible,
            'justified_answers': justified, 'expected_response': justified[0] if justified else 'INSUFFICIENT',
            'relaxed_possible_answers': relaxed, 'conflicting_scopes': sorted(conflicts),
            'invalid_value_scopes': sorted(invalid), 'missing_scopes': sorted(missing),
            'unresolved_scopes': sorted(unresolved), 'unknown_scope_keys': sorted(unknown),
            'miscited_scopes': sorted(miscited), 'unique_supported_decision': len(justified) == 1}


def assess_choice(state, choice, operational_failure=False):
    unique = state['unique_supported_decision']
    return {'agreement_with_unique_supported_decision': (choice == state['justified_answers'][0] and not operational_failure) if unique else None,
            'choice_possible_under_some_completion': choice in state['possible_answers'] if state['consistent'] else None,
            'choice_justified_under_every_completion': choice in state['justified_answers'] if state['consistent'] else None,
            'insufficient_response': choice == 'INSUFFICIENT' and not operational_failure,
            'visible_contract_agreement': choice == state['expected_response'] and not operational_failure,
            'sufficient_information_violated': unique and choice != state['justified_answers'][0] and not operational_failure}
