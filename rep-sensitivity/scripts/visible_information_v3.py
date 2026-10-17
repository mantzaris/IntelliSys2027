"""Separate representation validity from decision support by uncontested facts.

Strict v2 consistency is preserved. Disputed/ill-typed/unresolved fields remain
unknown, not repaired. A choice can still be invariant to EVERY admissible value
of those fields (e.g. exactly one candidate is known feasible). This does not
resolve the conflicting claims or make the full representation valid.
"""
try:
    from .visible_information_v2 import visible_state
except ImportError:
    from visible_information_v2 import visible_state


def support_from_state(state):
    answers=state['relaxed_possible_answers'];unique=len(answers)==1
    errors=bool(state['conflicting_scopes'] or state['invalid_value_scopes'])
    return {'representation_status':state['status'],'strict_global_consistency':state['consistent'],
        'uncontested_completion_answers':answers,
        'uncontested_unique_decision':answers[0] if unique else None,
        'decision_determined_from_uncontested_facts':unique,
        'determinate_despite_representation_errors':unique and errors,
        'representation_errors_leave_decision_undetermined':errors and not unique,
        'decision_status':'determinate_despite_representation_errors' if unique and errors else
                          'sufficient_consistent' if unique else 'underdetermined_from_uncontested_facts'}


def support_assessment(support,choice,operational_failure=False):
    unique=support['decision_determined_from_uncontested_facts']
    return {'agreement_with_uncontested_unique_decision':(choice==support['uncontested_unique_decision'] and not operational_failure) if unique else None,
        'violates_uncontested_unique_decision':unique and choice!=support['uncontested_unique_decision'] and not operational_failure,
        'choice_possible_under_uncontested_completions':choice in support['uncontested_completion_answers'] and not operational_failure,
        'decision_contract_agreement_v3':choice==(support['uncontested_unique_decision'] if unique else 'INSUFFICIENT') and not operational_failure}
