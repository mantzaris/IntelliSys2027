"""Observable proposition preservation; no inferred internal reasoning path."""
from collections import defaultdict
from .metrics import same_value
from .schema import canonical


def assertion_triples(obj):
    """Normalize the container only; preserve JSON types and values exactly."""
    return [[a['key'], a['value'], a['reports']] if isinstance(a, dict) else a
            for a in obj.get('assertions', [])]


def field_records(reports, summaries):
    claims = {c.key: c for r in reports for c in r.claims()}
    references = {r.identifier: {c.key for c in r.claims()} for r in reports}
    values = defaultdict(list); unresolved = set()
    for obj in summaries:
        if not isinstance(obj, dict): continue
        unresolved.update(obj.get('unresolved', []))
        for key, value, refs in assertion_triples(obj): values[key].append((value, refs))
    rows = []
    for key, claim in claims.items():
        emitted = values[key]; expected = claim.asserted_value
        wrong = any(not same_value(v, expected) for v, _ in emitted)
        row = {'key': key, 'scope': claim.scope(), 'objective': claim.task_identifier == 'objective',
               'expected_value': expected, 'emitted': [[v, refs] for v, refs in emitted],
               'omitted': not emitted, 'unresolved': key in unresolved,
               'boolean_replacement': claim.task_identifier == 'objective' and any(type(v) is bool for v, _ in emitted),
               'number_changed': claim.task_identifier == 'objective' and any(type(v) in (int, float) and not same_value(v, expected) for v, _ in emitted),
               'distorted': wrong,
               'conflicted': len({canonical([type(v).__name__, v]) for v, _ in emitted}) > 1,
               'scope_citation_mismatch': any(ref in references and key not in references[ref] for _, refs in emitted for ref in refs),
               'preserved': bool(emitted) and not wrong and key not in unresolved}
        # A foreign-scope citation certifies a binding inconsistency. A coincident
        # number alone does NOT establish that the model transferred that value.
        row['foreign_objective_value_with_foreign_citation'] = any(
            type(v) in (int, float) and not same_value(v, expected) and any(
                other != key and claims[other].task_identifier == 'objective' and same_value(v, claims[other].asserted_value)
                for ref in refs for other in references.get(ref, set())) for v, refs in emitted)
        rows.append(row)
    return rows


def summarize_fields(fields):
    keys = ('omitted', 'boolean_replacement', 'number_changed', 'distorted', 'conflicted',
            'scope_citation_mismatch', 'foreign_objective_value_with_foreign_citation', 'unresolved', 'preserved')
    out = {}
    for name, selected in [('objective', [r for r in fields if r['objective']]),
                           ('constraint', [r for r in fields if not r['objective']])]:
        out[name + '_fields'] = len(selected)
        out.update({name + '_' + k: sum(r[k] for r in selected) for k in keys})
    return out
