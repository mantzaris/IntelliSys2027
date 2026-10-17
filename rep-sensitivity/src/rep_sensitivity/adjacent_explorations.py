"""Small development-only coordinator feedback and explicit-origin relay studies.

No new worker observations, no outcome-based case selection, no active-run edits.
The source pairs and the deterministic construction of future feedback are frozen.
"""
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
import json

from .generation import field_changes, oracle
from .metrics import parse, score_root
from .numerical_audit import field_records, summarize_fields
from .policies import make_prompt
from .replay import execute_requests
from .reports import make_reports, registry, repeat
from .schema import canonical, digest, world_from_dict
from .storage import Ledger, immutable_json
from .verification import reference_verify


VERSION_RULE = (
    'The task authority publishes complete evidence snapshots. The explicitly designated '
    'current_version is authoritative and replaces the preceding snapshot in full. '
    'Any supplied previous public output is your own preceding public decision. '
    'It is not evidence and has no authority over the current snapshot. '
    'No additional independent worker observations are acquired in these rounds. '
    'Decide for the current snapshot, using the same decision rule in every round.'
)
RELAY_RULE = (
    'Presentation labels identify messengers only. All presentations sharing origin_report '
    'are the same original report, with one source and one verification execution. '
    'No relay independently verified the claim. Worker, relay, reviewer and senior analyst '
    'labels confer no additional reliability or decision authority. Copies add no new evidence.'
)


def harmless_world(initial, family, sign):
    """First lexicographic matched edit with identical executable predicate results.

    This selection uses task semantics, never model decisions. Numerical edits
    change a slack resource; identity edits reassign one nonbinding job resource.
    These residual scope differences from the consequential edit are recorded.
    """
    baseline = oracle(initial)
    candidates = []
    if family == 'numeric':
        for resource in sorted(initial['capacities']):
            w = deepcopy(initial)
            if w['capacities'][resource] + sign <= 0:
                continue
            w['capacities'][resource] += sign
            candidates.append(w)
    elif family == 'identity':
        for j in sorted(range(len(initial['jobs'])), key=lambda i: initial['jobs'][i]['identifier']):
            demand = initial['jobs'][j]['demands']
            if len(demand) != 1:
                continue
            for resource in sorted(set(initial['capacities']) - set(demand)):
                w = deepcopy(initial)
                w['jobs'][j]['demands'] = {resource: next(iter(demand.values()))}
                candidates.append(w)
    else:
        raise ValueError('Only the two prespecified scheduling edit families are supported')
    for w in candidates:
        result = oracle(w)
        # Peak diagnostics may differ, but every mandatory result and objective
        # must agree. Harmlessness is stronger than unchanged final choice.
        if result['answer'] == baseline['answer'] and all(
            result['candidates'][c]['mandatory'] == v['mandatory'] and
            result['candidates'][c]['objective'] == v['objective']
            for c, v in baseline['candidates'].items()
        ):
            return w
    raise ValueError('Frozen base has no eligible harmless edit; do not silently replace it')


def build_cases(config):
    source = json.loads((Path(config['source_run']) / 'pairs.json').read_text())
    by_index = {p['index']: p for p in source}
    cases = []
    for ordinal, (index, reverse) in enumerate(zip(config['pair_indices'], config['reverse_updates'])):
        p = by_index[index]
        if p['split'] != 'development' or not p['evaluation']['decision_changed']:
            raise ValueError('Only fixed consequential development source pairs are eligible')
        initial = deepcopy(p['worlds'][int(reverse)])
        changed = deepcopy(p['worlds'][1-int(reverse)])
        capacity_delta = next((changed['capacities'][r]-v for r, v in initial['capacities'].items()
                               if changed['capacities'][r] != v), 1)
        harmless = harmless_world(initial, p['evaluation']['family'], capacity_delta)
        edits = {u: field_changes(initial, w) for u, w in [('consequential', changed), ('harmless', harmless)]}
        initial['version'] = '1'
        changed['version'] = harmless['version'] = '2'
        worlds = {'initial': initial, 'consequential': changed, 'harmless': harmless}
        truth = {u: oracle(w) for u, w in worlds.items()}
        for u, w in worlds.items():
            ref = reference_verify(world_from_dict(w))
            if ref['answer'] != truth[u]['answer'] or any(
                ref['feasible'][cid] != v['feasible'] or ref['objective'][cid] != v['objective']
                for cid, v in truth[u]['candidates'].items()
            ):
                raise ValueError('Independent checker disagreement')
        if truth['initial']['answer'] == truth['consequential']['answer'] or truth['initial']['answer'] != truth['harmless']['answer']:
            raise ValueError('Update label invalid')
        if any(truth['initial']['candidates'][c]['objective'] != v['objective']
               for c, v in truth['consequential']['candidates'].items()):
            raise ValueError('Repeated objective must stay identical across worlds')
        reports = {u: make_reports(w, 'development', p['seed']) for u, w in worlds.items()}
        target = min(truth['initial']['candidates'], key=lambda c: (truth['initial']['candidates'][c]['objective'], initial['tie_order'].index(c)))
        cases.append({'pair_id': p['pair_id'], 'index': index, 'ordinal': ordinal,
                      'family': p['evaluation']['family'], 'source_pair_sha256': digest(p),
                      'reverse': reverse, 'worlds': worlds, 'truth': truth,
                      'reports': reports, 'edits': edits, 'target_candidate': target})
    return cases


def trial(config, case, experiment, arm, world, round_number=1):
    t = {'suite': config['name'], 'pair_id': case['pair_id'], 'model': config['model'],
         'experiment': experiment, 'arm': arm, 'world': world, 'round': round_number,
         'policy': 'ordinary', 'organization': 'coordinator', 'repetition': round_number-1}
    t['trial_id'] = digest(t)[:24]
    return t


def public_feedback(call, choices, round_number):
    """Replay only the preceding public choice and required candidate assessments.

    No rationale, evaluator correction, probability interpretation or resampling.
    Malformed completed outputs yield an explicit missing public decision marker.
    """
    obj, status = parse(call['response']['text'], choices+['NONE'])
    if call['response']['finish_reason'] == 'length':
        obj, status = None, 'truncated'
    return {'previous_round': round_number, 'evidence_version': '1', 'parse_status': status,
            'choice': obj['choice'] if obj else None,
            'candidate_assessments': obj.get('candidate_assessments', []) if obj else []}


def feedback_prompt(case, update, round_number, context=None):
    state = update if round_number == 3 else 'initial'
    world = case['worlds'][state]
    prompt = make_prompt(world, case['reports'][state], 'ordinary')
    header, body = prompt.split('\nINPUT\n', 1)
    payload = json.loads(body)
    payload['task_authority'] = {'current_version': world['version'], 'round': round_number,
        'replaces_version': '1' if round_number == 3 else None,
        'changed_fields': case['edits'][update] if round_number == 3 else []}
    if context is not None:
        payload['context_only_not_current_evidence'] = context
    return header+'\n'+VERSION_RULE+'\nINPUT\n'+canonical(payload)


def length_control(case, update, round_number, feedback, token_ids):
    target = len(token_ids(feedback_prompt(case, update, round_number, feedback)))
    candidates = []
    lo, hi = 0, target
    while lo <= hi:
        n = (lo+hi)//2
        context = {'neutral_material': '. '*n, 'meaning': 'Non-evidential display padding.'}
        prompt = feedback_prompt(case, update, round_number, context)
        count = len(token_ids(prompt)); candidates.append((abs(count-target), n, count, prompt))
        if count < target:
            lo = n+1
        else:
            hi = n-1
    _, _, count, prompt = min(candidates)
    return prompt, count-target


def consensus_prompt(case, world_number, arm):
    state = 'initial' if world_number == 0 else 'consequential'
    world = case['worlds'][state]
    reports = case['reports'][state]
    chosen = next(r for r in reports if r.claim.task_identifier == 'objective' and
                  r.claim.candidate_identifier == case['target_candidate'])
    essential = [r for r in reports if r != chosen]
    position = [0, 5, 11, len(essential)][case['ordinal'] % 4]
    essential.insert(position, chosen)
    selected = canonical(['objective', chosen.claim.candidate_identifier, chosen.claim.entity_identifier])
    supplied = repeat(essential, selected, 'single' if arm == 'single' else 'exact', 'development')
    header, body = make_prompt(world, supplied, 'ordinary').split('\nINPUT\n', 1)
    payload = json.loads(body)
    displayed = [r for r in payload['reports'] if r['key'] == chosen.claim.key]
    roles = ['reviewer', 'senior analyst', 'reviewer', 'senior analyst']
    rotate = case['ordinal'] % 4
    labels = ['agent_'+digest([case['pair_id'], i])[:4] for i in range(4)]
    for i, r in enumerate(displayed):
        r['presentation'] = {'origin_report': chosen.identifier,
            'displayed_agent': labels[rotate] if arm in ('single', 'same_worker') else labels[(i+rotate) % 4],
            'role_label': roles[(i+rotate) % 4] if arm == 'authority_labels' else 'relay',
            'independent_reverification': False,
            'relationship': 'original' if i == 0 else 'explicit_copy'}
    return header+'\n'+RELAY_RULE+'\nINPUT\n'+canonical(payload), supplied


def inventory(config, cases):
    # Future generated feedback cannot be prehashed. Pin its constructor/source
    # and dependencies; accepted calls record the fully materialized prompt.
    return [{'pair_id': c['pair_id'], 'source_pair_sha256': c['source_pair_sha256'],
             'world_sha256': {k: digest(v) for k, v in c['worlds'].items()},
             'report_sha256': {k: digest([asdict(r) for r in v]) for k, v in c['reports'].items()},
             'initial_prompt_sha256': digest(feedback_prompt(c, 'consequential', 1)),
             'update_prompt_sha256': {u: digest(feedback_prompt(c, u, 3)) for u in ('consequential','harmless')},
             'consensus_prompt_sha256': {f'{w}/{a}': digest(consensus_prompt(c, w, a)[0])
                 for w in (0,1) for a in config['consensus_arms']},
             'target_candidate': c['target_candidate'], 'edits': c['edits']} for c in cases]


def score_call(call, case, state, reports):
    response = call['response']; truth = case['truth'][state]
    score = score_root(response, case['worlds'][state], truth, reports)
    obj, _ = parse(response['text'], case['worlds'][state]['tie_order']+['NONE'])
    if score['operational_failure']:
        obj = None
    candidate = truth['candidates'].get(score['choice'])
    return {**call['trial'], **score, 'family': case['family'], 'current_state': state,
        'current_evidence_status': 'sufficient_consistent',
        'visible_supported_choice': truth['answer'],
        'agrees_with_visible_supported_choice': score['correct'],
        'feasible_but_suboptimal': bool(candidate and candidate['feasible'] and not score['correct']),
        'target_candidate': case['target_candidate'], 'selected_target': score['choice'] == case['target_candidate'],
        'representation': summarize_fields(field_records(reports, [obj] if obj else [])),
        'request_hashes': [call['request_hash']],
        'input_tokens': response['input_tokens'], 'output_tokens': response['output_tokens'],
        'inference_seconds_allocated': response['allocated_inference_seconds']}


def run(config, model=None, root='artifacts/runs'):
    if config['status'] != 'frozen':
        raise ValueError('Freeze before inference')
    cases = build_cases(config); inputs = inventory(config, cases)
    if len(cases) != 4 or config.get('execution_mode', 'both') not in ('both', 'feedback_only'):
        raise ValueError('Only the frozen four-base allocation is allowed')
    consensus_calls = 32 if config.get('execution_mode', 'both') == 'both' else 0
    if digest(inputs) != config['input_inventory_sha256']:
        raise ValueError('Frozen inputs changed')
    directory = Path(root)/config['name']
    immutable_json(directory/'manifest.json', {'config': config, 'base_pairs': len(cases),
        'calls': 72+consensus_calls, 'feedback_calls': 72, 'consensus_calls': consensus_calls,
        'input_inventory_sha256': digest(inputs),
        'source_manifest_sha256': digest(json.loads((Path(config['source_run'])/'manifest.json').read_text()))})
    immutable_json(directory/'inputs.json', inputs)
    immutable_json(directory/'implementation.json', {p.name: p.read_text() for p in Path(__file__).parent.glob('*.py')})
    from .models import reuse_or_load
    model, loaded = reuse_or_load(config['model'], config, model)
    for key in ('revision','tokenizer_revision','chat_template_sha256','chat_template_date','reasoning_mode','precision','quantization'):
        config_key='model_revision' if key=='revision' else key
        if config_key in config and model.settings.get(key)!=config[config_key]:
            raise ValueError('Frozen model/tokenizer/inference metadata changed: '+key)
    ledger = Ledger(directory/config['model'])
    ledger.event('run_start', settings=model.settings, model_load_seconds=model.load_seconds if loaded else 0)
    previous = {}; all_rows = []
    for round_number in (1,2,3):
        jobs = []
        for c in cases:
            for update in ('consequential', 'harmless'):
                feedback = public_feedback(previous[c['pair_id'], update], c['worlds']['initial']['tie_order'], round_number-1) if round_number > 1 else None
                for arm in config['feedback_arms']:
                    t = trial(config, c, 'feedback', arm, update, round_number)
                    residual = None
                    if arm == 'length_control' and feedback is not None:
                        prompt, residual = length_control(c, update, round_number, feedback, model.token_ids)
                    else:
                        prompt = feedback_prompt(c, update, round_number, feedback if arm == 'feedback' else None)
                    jobs.append({'trial': t, 'stage': 'root', 'prompt': prompt, 'case': c, 'padding_token_residual': residual})
        jobs.sort(key=lambda j: digest([config['ordering_seed'], j['trial']]))
        outputs = execute_requests(jobs, model, ledger)
        rows = []
        for j in jobs:
            t = j['trial']; c = j['case']; call = outputs[t['trial_id'], 'root']
            state = t['world'] if round_number == 3 else 'initial'
            row = score_call(call, c, state, c['reports'][state])
            row.update(padding_token_residual=j['padding_token_residual'],
                prior_feedback_call_hash=previous[c['pair_id'], t['world']]['request_hash'] if round_number > 1 and t['arm'] != 'fresh' else None)
            rows.append(row)
        # Only the feedback arm's own prior output enters the next round. The
        # length arm receives its token count, never its decision or assessments.
        previous = {(j['case']['pair_id'], j['trial']['world']): outputs[j['trial']['trial_id'], 'root']
                    for j in jobs if j['trial']['arm'] == 'feedback'}
        immutable_json(directory/config['model']/'scores'/f'feedback-round-{round_number}.json', rows)
        all_rows.extend(rows)
    ledger.event('experiment_complete', experiment='feedback', calls=72, base_pairs=len(cases))
    if not consensus_calls:
        ledger.event('run_complete', calls=72, base_pairs=len(cases)); ledger.close(); return
    jobs = []
    for c in cases:
        for w in (0,1):
            for arm in config['consensus_arms']:
                prompt, reports = consensus_prompt(c, w, arm)
                jobs.append({'trial': trial(config, c, 'consensus', arm, w), 'stage': 'root',
                             'prompt': prompt, 'case': c, 'reports': reports})
    jobs.sort(key=lambda j: digest([config['ordering_seed'], j['trial']]))
    outputs = execute_requests(jobs, model, ledger)
    rows = [score_call(outputs[j['trial']['trial_id'], 'root'], j['case'],
                       'initial' if j['trial']['world'] == 0 else 'consequential', j['reports']) for j in jobs]
    immutable_json(directory/config['model']/'scores'/'consensus.json', rows)
    ledger.event('experiment_complete', experiment='consensus', calls=32, base_pairs=len(cases))
    ledger.event('run_complete', calls=104, base_pairs=len(cases)); ledger.close()
