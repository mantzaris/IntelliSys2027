"""Exploratory interpretation of a completed pilot, without changing raw scores.

All sampling units are whole base problems. Scope keys bind the complete public
registry proposition; this scores explicit output, not unobserved reasoning.
"""
from collections import defaultdict
from dataclasses import replace
import csv
import gzip
import json
from pathlib import Path

from .analysis import average, load_complete
from .generation import oracle
from .mechanism import necessary_keys, relevance, transport_metrics
from .metrics import parse, same_value, score_assertions
from .reports import repeat, thaw
from .schema import canonical, digest
from .targeted_analysis import clustered_interval


FAILURE_LABELS = (
    'necessary_fact_omitted', 'necessary_value_wrong_or_conflicted',
    'necessary_fact_unresolved', 'summary_scope_miscitation',
    'visible_false_constraint_ignored', 'complete_constraints_delivered_invalid_choice',
    'feasible_but_not_preferred', 'strictly_suboptimal_objective', 'tie_break_error',
    'correct_choice_erroneous_support', 'response_contract_failure',
    'root_error_despite_sufficient_visible_truth',
)


def failure_locations(world, reports, summaries, root, correct, operational_failure, needed=None):
    """Multi-label observations, never a mutually exclusive causal taxonomy.

    A wrong value at a known key is observable; its origin (miscalculation,
    misreading, scope transfer) usually is not. Scope transfer is certified only
    by an incompatible report citation. Missing free-text interpretations are
    not invented. A numeric value at a different key cannot retain this key.
    """
    truth = oracle(world)
    claims = {c.key: c for r in reports for c in r.claims()}
    for r in reports:
        for c in r.claims():
            if claims[c.key].scope() != c.scope():
                raise ValueError('Scope-key collision')
    needed = necessary_keys(world, reports) if needed is None else needed
    values = defaultdict(list)
    unresolved = set()
    for obj in summaries:
        if obj is None:
            continue
        unresolved.update(k for k in obj['unresolved'] if isinstance(k, str))
        for key, value, refs in obj['assertions']:
            values[key].append(value)
    retained = {k for k, c in claims.items() if values[k] and k not in unresolved
                and all(same_value(v, c.asserted_value) for v in values[k])}
    absent = needed - set(k for k, v in values.items() if v) - unresolved
    altered = {k for k in needed if any(not same_value(v, claims[k].asserted_value) for v in values[k])}
    choice = root['choice'] if root else None
    candidate = truth['candidates'].get(choice)
    mandatory = {k for k, c in claims.items() if c.candidate_identifier == choice
                 and c.task_identifier != 'objective'}
    false_delivered = {k for k in mandatory & retained if claims[k].asserted_value is False}
    feasible_wrong = bool(candidate and candidate['feasible'] and choice != truth['answer'])
    objectives = {c.candidate_identifier: c.asserted_value for c in claims.values() if c.task_identifier == 'objective'}
    strictly_worse = feasible_wrong and objectives[choice] > objectives[truth['answer']]
    supporting = score_assertions(root, reports)
    support_errors = any(supporting[k] for k in (
        'incorrect_emitted_claims', 'scope_transfer_count', 'unsupported_reference_count'))
    transport = transport_metrics(world, reports, summaries, correct, necessary_scopes=needed)
    return {
        'necessary_fact_omitted': bool(absent),
        'necessary_value_wrong_or_conflicted': bool(altered),
        'necessary_fact_unresolved': bool(needed & unresolved),
        'summary_scope_miscitation': any(score_assertions(o, reports)['scope_transfer_count'] for o in summaries),
        'visible_false_constraint_ignored': bool(candidate and not candidate['feasible'] and false_delivered),
        'complete_constraints_delivered_invalid_choice': bool(candidate and not candidate['feasible'] and mandatory <= retained),
        'feasible_but_not_preferred': feasible_wrong,
        'strictly_suboptimal_objective': bool(strictly_worse),
        'tie_break_error': feasible_wrong and not strictly_worse,
        'correct_choice_erroneous_support': bool(correct and support_errors),
        'response_contract_failure': bool(operational_failure),
        'root_error_despite_sufficient_visible_truth': transport['root_error_despite_sufficient_visible_truth'],
        'necessary_missing_keys': sorted(absent), 'necessary_altered_keys': sorted(altered),
        'necessary_unresolved_keys': sorted(needed & unresolved),
        'retained_keys_strict': sorted(retained),
        'necessary_retention': transport['necessary_retention'],
        'objective_retention': transport['objectives_retained'] / transport['objective_denominator'],
        'visible_truth_sufficient': transport['visible_truth_sufficient'],
    }


def paired_effect(rows, condition, metric='correct'):
    cells = defaultdict(dict)
    for row in rows:
        key = tuple(row[k] for k in ('pair_id', 'model', 'world', 'organization', 'policy', 'repetition'))
        if row['condition'] in ('single', condition):
            if row['condition'] in cells[key]:
                raise ValueError('Duplicate paired cell')
            cells[key][row['condition']] = row
    clusters = defaultdict(list)
    matched = []
    for key, arms in cells.items():
        if set(arms) != {'single', condition}:
            raise ValueError('Incomplete paired cell')
        a, b = arms['single'][metric], arms[condition][metric]
        if a is None or b is None:
            continue
        clusters[key[0]].append(float(b) - float(a))
        matched.append((arms['single'], arms[condition]))
    values = {pid: average(xs) for pid, xs in clusters.items()}
    strata = {r['pair_id']: (r['family'], r['decision_changed']) for r in rows}
    summary = clustered_interval(values, strata)
    before = defaultdict(list); after = defaultdict(list)
    for a, b in matched:
        before[a['pair_id']].append(float(a[metric])); after[b['pair_id']].append(float(b[metric]))
    loo = {pid: average(v for p, v in values.items() if p != pid) for pid in values} if len(values) > 1 else {}
    return {**summary, 'baseline': average(average(xs) for xs in before.values()),
            'repeated': average(average(xs) for xs in after.values()),
            'matched_cells': len(matched), 'trajectories': 2 * len(matched),
            'improvements': sum(b[metric] > a[metric] for a, b in matched),
            'regressions': sum(b[metric] < a[metric] for a, b in matched),
            'unchanged': sum(b[metric] == a[metric] for a, b in matched),
            'base_positive': sum(v > 0 for v in values.values()),
            'base_negative': sum(v < 0 for v in values.values()),
            'base_zero': sum(v == 0 for v in values.values()),
            'leave_one_base_out_min': min(loo.values()) if loo else None,
            'leave_one_base_out_max': max(loo.values()) if loo else None,
            'base_effects': values, 'leave_one_base_out': loo}


def paired_world_rows(rows):
    groups = defaultdict(dict)
    for r in rows:
        key = tuple(r[k] for k in ('pair_id', 'model', 'organization', 'policy', 'condition', 'repetition'))
        if r['world'] in groups[key]:
            raise ValueError('Duplicate world')
        groups[key][r['world']] = r
    result = []
    for worlds in groups.values():
        if set(worlds) != {0, 1}:
            raise ValueError('Both worlds required')
        a, b = worlds[0], worlds[1]
        if a['decision_changed'] != (a['oracle_choice'] != b['oracle_choice']):
            raise ValueError('Incorrect world-change label')
        result.append({**a, 'world': 'both', 'correct': bool(a['correct'] and b['correct']),
                       'answer_changed': a['choice'] != b['choice'],
                       'same_wrong_answer': a['choice'] == b['choice'] and not (a['correct'] and b['correct'])})
    return result


def annotated_pilot(source):
    manifest, rows, incomplete = load_complete(source)
    if incomplete or len(rows) != manifest['trajectories']:
        raise ValueError('Only the complete frozen pilot is eligible')
    pairs = {p['pair_id']: p for p in json.loads((source / 'pairs.json').read_text())}
    corpus = json.loads((source / 'frozen-reports.json').read_text())
    calls = {}; needed_cache = {}; annotated = []
    for row in rows:
        pair = pairs[row['pair_id']]; world = pair['worlds'][row['world']]
        originals = thaw(corpus[pair['pair_id']]['reports'][row['world']])
        reports = repeat(originals, corpus[pair['pair_id']]['selected'], row['condition'], pair['split'])
        selected = next(r for r in originals if canonical([r.claim.task_identifier, r.claim.candidate_identifier,
                         r.claim.entity_identifier]) == corpus[pair['pair_id']]['selected'])
        parsed = {}; finish = []
        for key in row['request_hashes']:
            if key not in calls:
                calls[key] = json.loads(gzip.decompress((source / row['model'] / 'calls' / (key + '.json.gz')).read_bytes()))
            call = calls[key]
            obj, status = parse(call['response']['text'], world['tie_order'] + ['NONE'], manager=call['stage'] != 'root')
            if call['response']['finish_reason'] == 'length':
                obj = None
            parsed[call['stage']] = obj; finish.append(call['response']['finish_reason'])
        coordinate = (row['pair_id'], row['world'])
        if coordinate not in needed_cache:
            needed_cache[coordinate] = necessary_keys(world, originals)
        if row['organization'] == 'hierarchical':
            summaries = [parsed.get('manager0'), parsed.get('manager1')]
        else:
            summaries = [{'assertions': [[c.key, c.asserted_value, [r.identifier]] for r in reports for c in r.claims()], 'unresolved': []}]
        rel = relevance(world, originals, selected)
        annotated.append({**row, 'selected_task': rel['task'], 'selected_scope': selected.claim.key,
            'selected_candidate': selected.claim.candidate_identifier,
            'selected_candidate_feasible': rel['candidate_feasible'],
            'selected_candidate_is_correct_choice': rel['candidate_is_correct_choice'],
            'selected_boolean_decisive': rel['boolean_counterfactual_decisive'],
            'any_truncation': 'length' in finish,
            **failure_locations(world, reports, summaries, parsed['root'], row['correct'], row['operational_failure'], needed_cache[coordinate])})
    return manifest, annotated, calls


def write_csv(path, rows):
    with path.open('w', newline='') as f:
        fields = list(dict.fromkeys(k for r in rows for k in r))
        writer = csv.DictWriter(f, fields, lineterminator='\n')
        writer.writeheader(); writer.writerows(rows)


def summarize(source, output):
    source = Path(source); output = Path(output); output.mkdir(parents=True, exist_ok=True)
    manifest, rows, calls = annotated_pilot(source)
    comparisons = []
    dimensions = {'overall': (), 'policy': ('policy',), 'family': ('family',),
                  'world': ('world',), 'change': ('decision_changed',), 'target': ('selected_task',)}
    for dimension, extra in dimensions.items():
        groups = defaultdict(list)
        for r in rows:
            groups[tuple(r[k] for k in ('model', 'kind', 'organization', *extra))].append(r)
        for key, group in sorted(groups.items()):
            for condition in ('exact', 'paraphrase'):
                comparisons.append({'dimension': dimension, **dict(zip(('model', 'kind', 'organization', *extra), key)),
                    'condition': condition, 'policy_aggregation': 'equal ordinary/checklist' if 'policy' not in extra else key[-1],
                    'target_rule': 'frozen unchanged report selected before evaluation; selected_task strata separately reported',
                    **paired_effect(group, condition)})
    pair_rows = paired_world_rows(rows)
    world_results = []
    for kind in ('schedule', 'workflow'):
        for organization in ('flat', 'hierarchical'):
            for change in (False, True):
                group = [r for r in pair_rows if (r['kind'], r['organization'], r['decision_changed']) == (kind, organization, change)]
                for condition in ('exact', 'paraphrase'):
                    estimate = paired_effect(group, condition)
                    world_results.append({'kind': kind, 'organization': organization, 'decision_changed': change,
                        'condition': condition, 'outcome': 'both worlds correct',
                        **estimate, 'trajectories': 2 * estimate['trajectories'],
                        'unit': 'a matched cell now contains two worlds per arm'})
    failure_groups = defaultdict(list)
    for r in rows:
        failure_groups[(r['kind'], r['organization'], r['policy'], r['condition'])].append(r)
    failure_counts = []
    for key, group in sorted(failure_groups.items()):
        failure_counts.append({**dict(zip(('kind', 'organization', 'policy', 'condition'), key)),
            'trajectories': len(group), 'base_pairs': len({r['pair_id'] for r in group}),
            'correct': sum(r['correct'] for r in group), 'invalid_selection': sum(r['invalid_selection'] for r in group),
            **{label: sum(r[label] for r in group) for label in FAILURE_LABELS},
            'any_truncation': sum(r['any_truncation'] for r in group)})
    result = {'analysis_version': 'pilot-interpretation-v2', 'status': 'completed_exploratory',
        'source_manifest_sha256': digest(manifest),
        'source_scores_sha256': json.loads(Path('results/pilot-v7/analysis.json').read_text())['source_scores_sha256'],
        'analysis_source_sha256': digest(Path(__file__).read_text()),
        'model': manifest['config']['models'], 'base_pairs': len({r['pair_id'] for r in rows}),
        'trajectories': len(rows), 'accepted_calls': len(calls),
        'aggregation': 'Equal base-cluster means of matched world/policy/stochastic-repetition cells. Accuracy effects are repeated minus single. Family by change-status stratified 10000-replicate percentile bootstrap, seed 20271015. Whole clusters retain all worlds, policies and repetitions. Singleton stratum intervals withheld.',
        'leave_one_out': 'Descriptive equal-remaining-base mean, not repeated significance tests or a new inferential population.',
        'failure_label_denominator': 'All trajectories in the stated row, including malformed completed outputs. Multi-label counts overlap. Flat retention means supplied facts, with no summary boundary.',
        'scope_contract': 'A key binds entity, predicate, criterion parameters, units, applicability and version in the public registry. Values must match at that key. Free-text rationale is not scored as an internal reasoning path. A wrong key with the same number does not preserve the original proposition. Citation mismatch is measured separately.',
        'annotation_limits': 'Deterministic labels refer to explicit keyed assertions and observable decisions. Attribution to attention, arithmetic, implicit scope confusion or causal mediation requires independent annotation/intervention; no such causal label is inferred here.',
        'comparisons': comparisons, 'paired_world': world_results, 'failure_locations': failure_counts}
    (output / 'analysis.json').write_text(json.dumps(result, indent=2) + '\n')
    for name, data in [('accuracy', comparisons), ('paired-world', world_results), ('failure-locations', failure_counts)]:
        write_csv(output / (name + '.csv'), [{k: v for k, v in r.items() if not isinstance(v, dict)} for r in data])
    detail = Path('artifacts/analyses/pilot-interpretation-v2'); detail.mkdir(parents=True, exist_ok=True)
    (detail / 'annotated-trajectories.json').write_text(json.dumps(rows, indent=2) + '\n')
    return result
