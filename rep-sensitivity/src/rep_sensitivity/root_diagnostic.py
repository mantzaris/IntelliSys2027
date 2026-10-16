"""Root-only repetition with fixed incoming propositions; development diagnostic.

Every candidate objective is targeted in turn, without selecting a winner.
The model-summary arm copies supplied assertions even when they are wrong; the
lossless arm transports the original worker assertions without oracle correction.
"""
from collections import defaultdict
from copy import deepcopy
import gzip
import json
from pathlib import Path

from .analysis import average
from .generation import oracle
from .graphs import partition
from .mechanism import critical_keys
from .metrics import parse, score_root
from .models import reuse_or_load
from .pilot_interpretation import failure_locations
from .policies import make_prompt
from .replay import execute_requests
from .reports import thaw, registry, ancestry_registry
from .schema import canonical, digest
from .storage import Ledger, immutable_json
from .targeted_analysis import clustered_interval
from .targeted_replay import lossless_summary
from .targeted_audit import inventory


def supplied_inventory(summaries):
    return sorted({canonical([key, 'bool' if type(value) is bool else 'number', value])
        for item in summaries if item['summary'] for key, value, refs in item['summary']['assertions']})


def repeat_assertions(summaries, keys, dose=4, position='adjacent'):
    changed = deepcopy(summaries); additions = 0; done = set()
    for item in changed:
        obj = item['summary']
        if obj is None:
            continue
        out = []; tail = []
        for assertion in obj['assertions']:
            out.append(assertion)
            if assertion[0] in keys and assertion[0] not in done:
                copies = [deepcopy(assertion) for _ in range(dose-1)]
                (out if position == 'adjacent' else tail).extend(copies)
                additions += len(copies); done.add(assertion[0])
        obj['assertions'] = out + tail
    if supplied_inventory(changed) != supplied_inventory(summaries):
        raise ValueError('Root-only intervention changed distinct input propositions')
    return changed, additions


def prompt_for(job, summaries=None, padding=None):
    rs = job['reports']
    prompt = make_prompt(job['world'], [], 'ordinary', summaries=job['summaries'] if summaries is None else summaries,
        public_registry=registry(rs), public_ancestry=ancestry_registry(rs))
    if padding is not None:
        # Administrative material at the end is explicitly non-evidential. Its
        # position differs from adjacent assertion copies and is recorded.
        prompt += '\nAdministrative padding, no task findings: ' + padding
    return prompt


def plan(config, source):
    source = Path(source)
    pairs = [p for p in json.loads((source/'pairs.json').read_text()) if p['index'] in config['pair_indices']]
    if len(pairs) != len(config['pair_indices']):
        raise ValueError('Missing source base pair')
    corpus = json.loads((source/'frozen-reports.json').read_text())
    jobs = []; excluded = []
    for pair in pairs:
        if pair['evaluation']['kind'] != 'schedule':
            raise ValueError('Primary scheduling diagnostic only')
        old = json.loads((source/'qwen3'/'scores'/(pair['pair_id']+'.json')).read_text())
        for wi in config['worlds']:
            world = pair['worlds'][wi]; reports = thaw(corpus[pair['pair_id']]['reports'][wi])
            source_row = next(r for r in old if (r['world'], r['policy'], r['organization'], r['condition'], r['repetition'])
                              == (wi, 'ordinary', 'hierarchical', 'single', 0))
            summaries = []; source_hashes = []
            for key in source_row['request_hashes']:
                call = json.loads(gzip.decompress((source/'qwen3'/'calls'/(key+'.json.gz')).read_bytes()))
                if call['stage'] == 'root':
                    continue
                obj, status = parse(call['response']['text'], world['tie_order'], manager=True)
                if call['response']['finish_reason'] == 'length':
                    obj = None; status = 'truncated'
                summaries.append({'manager': int(call['stage'][-1]), 'summary': obj, 'parse_status': status})
                source_hashes.append(key)
            summaries.sort(key=lambda s: s['manager'])
            branches = partition(reports, pair['seed'])
            lossless = [{'manager': i, 'summary': parse(canonical(lossless_summary(b)), world['tie_order'], manager=True)[0],
                         'parse_status': 'valid'} for i, b in enumerate(branches)]
            objectives = sorted([r.claim for r in reports if r.claim.task_identifier == 'objective'], key=lambda c: c.candidate_identifier)
            keys = critical_keys(world, reports)
            decisive = sorted(keys)[pair['seed'] % len(keys)]
            for transport, incoming in [('frozen_summaries', summaries), ('lossless', lossless)]:
                fixed_hash = digest(incoming)
                anchor = objectives[pair['seed'] % len(objectives)].key
                arms = [('F', set(), 'adjacent')]
                arms += [('objective'+str(i), {c.key}, 'adjacent') for i, c in enumerate(objectives)]
                arms += [('constraint', {decisive}, 'adjacent'), ('uniform_objectives', {c.key for c in objectives}, 'adjacent'),
                         ('neutral', {anchor}, 'adjacent'), ('end', {anchor}, 'end')]
                for arm, selected, position in arms:
                    changed, additions = repeat_assertions(incoming, selected, config['presentations'], position)
                    if selected and additions == 0:
                        excluded.append({'pair_id': pair['pair_id'], 'world': wi, 'transport': transport, 'arm': arm,
                                         'reason': 'Selected proposition absent from the fixed incoming summaries'})
                        continue
                    for rep in range(config['stochastic_repetitions']):
                        trial = {'suite': config['name'], 'pair_id': pair['pair_id'], 'world': wi, 'model': config['model'],
                                 'organization': transport, 'policy': 'ordinary', 'arm': arm, 'repetition': rep}
                        trial['trial_id'] = digest(trial)[:24]
                        jobs.append({'trial': trial, 'pair': pair, 'world': world, 'reports': reports,
                            'summaries': incoming if arm == 'neutral' else changed, 'fixed_summaries': incoming,
                            'padding_reference': changed if arm == 'neutral' else None,
                            'incoming_sha256': fixed_hash, 'historical_manager_request_hashes': source_hashes if transport == 'frozen_summaries' else [],
                            'selected_keys': sorted(selected), 'added_presentations': additions,
                            'baseline_selected_presentations': sum(a[0] in selected for s in incoming if s['summary'] for a in s['summary']['assertions']),
                            'objective_anchor_key': anchor,
                            'manipulation': 'non-evidential padding at end' if arm == 'neutral' else position})
    return pairs, jobs, excluded


def materialize_prompt(job, token_ids):
    prompt = prompt_for(job)
    residual = 0
    if job['padding_reference'] is not None:
        target = len(token_ids(prompt_for(job, summaries=job['padding_reference'])))
        lo, hi = 0, max(1, target)
        candidates = []
        while lo <= hi:
            n = (lo+hi)//2
            p = prompt_for(job, padding='. '*n); count = len(token_ids(p)); candidates.append((abs(count-target), n, count, p))
            if count < target: lo = n+1
            else: hi = n-1
        _, _, count, prompt = min(candidates)
        residual = count-target
    job['input_token_count'] = len(token_ids(prompt))
    job['padding_token_residual'] = residual
    return prompt


def run(config):
    if config['status'] != 'frozen':
        raise ValueError('Freeze before inference')
    root = Path('artifacts/runs')/config['name']
    pairs, jobs, excluded = plan(config, config['source_run'])
    manifest = {'config': config, 'base_pairs': len(pairs), 'trajectories': len(jobs), 'calls': len(jobs),
                'excluded': excluded, 'pairs_sha256': digest(pairs),
                'source_manifest_sha256': digest(json.loads((Path(config['source_run'])/'manifest.json').read_text())),
                'input_design_sha256': digest([{'trial': j['trial'], 'incoming': j['incoming_sha256'], 'prompt': prompt_for(j)} for j in jobs]),
                'historical_manager_calls': len({h for j in jobs for h in j['historical_manager_request_hashes']}),
                'interpretation': 'New root calls only. Fixed historical summaries are reused, not fresh manager computation. Lossless transport is an idealized diagnostic.'}
    immutable_json(root/'manifest.json', manifest)
    immutable_json(root/'pairs.json', pairs)
    immutable_json(root/'implementation.json', {p.name: p.read_text() for p in Path(__file__).parent.glob('*.py')})
    model, loaded = reuse_or_load(config['model'], config)
    ledger = Ledger(root/config['model'])
    ledger.event('run_start', settings=model.settings, model_load_seconds=model.load_seconds)
    for pair in pairs:
        path = root/config['model']/'scores'/(pair['pair_id']+'.json')
        if path.exists(): continue
        block = [j for j in jobs if j['pair']['pair_id'] == pair['pair_id']]
        requests = [{'trial': j['trial'], 'stage': 'root', 'prompt': materialize_prompt(j, model.token_ids)} for j in block]
        calls = execute_requests(requests, model, ledger); scores = []
        for j in block:
            call = calls[(j['trial']['trial_id'], 'root')]; response = call['response']
            score = score_root(response, j['world'], oracle(j['world']), j['reports'])
            if any(s['parse_status'] != 'valid' for s in j['summaries']):
                score.update(correct=False, operational_failure=True)
            obj, _ = parse(response['text'], j['world']['tie_order']+['NONE'])
            if response['finish_reason'] == 'length': obj = None
            diagnostics = failure_locations(j['world'], j['reports'], [s['summary'] for s in j['summaries']], obj,
                                            score['correct'], score['operational_failure'])
            scores.append({**j['trial'], 'kind': 'schedule', 'family': pair['evaluation']['family'],
                'decision_changed': pair['evaluation']['decision_changed'], **score, **diagnostics,
                'incoming_sha256': j['incoming_sha256'], 'selected_keys': j['selected_keys'],
                'baseline_selected_presentations': j['baseline_selected_presentations'],
                'added_presentations': 0 if j['trial']['arm']=='neutral' else j['added_presentations'],
                'objective_anchor_key': j['objective_anchor_key'], 'manipulation': j['manipulation'],
                'padding_token_residual': j['padding_token_residual'],
                'historical_manager_request_hashes': j['historical_manager_request_hashes'],
                'input_tokens': response['input_tokens'], 'output_tokens': response['output_tokens'],
                'inference_seconds_allocated': response['allocated_inference_seconds'], 'request_hashes': [call['request_hash']]})
        immutable_json(path, scores)
        ledger.event('cluster_complete', pair_id=pair['pair_id'], trajectories=len(scores))
    ledger.event('run_complete', base_pairs=len(pairs)); ledger.close()


def analyze(directory, output):
    directory = Path(directory); output = Path(output); output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((directory/'manifest.json').read_text())
    rows = [r for p in sorted((directory/'qwen3'/'scores').glob('*.json')) for r in json.loads(p.read_text())]
    if len(rows) != manifest['trajectories']:
        raise ValueError('Wait for all prespecified root diagnostic trajectories')
    strata = {r['pair_id']: (r['family'], r['decision_changed']) for r in rows}
    cells = defaultdict(dict)
    for r in rows:
        cells[(r['pair_id'], r['world'], r['organization'], r['repetition'])][r['arm']] = r
    estimates = []
    for transport in ('frozen_summaries', 'lossless'):
        for arm in ('objective0', 'objective1', 'objective2', 'all_objective_targets', 'constraint', 'uniform_objectives', 'end', 'neutral'):
            vals = defaultdict(list); costs = defaultdict(list)
            for (pid, wi, org, rep), arms in cells.items():
                if org != transport: continue
                targets = ['objective0', 'objective1', 'objective2'] if arm == 'all_objective_targets' else [arm]
                effects = [int(arms[a]['correct'])-int(arms['F']['correct']) for a in targets if a in arms]
                if effects: vals[pid].append(average(effects))
            estimates.append({'transport': transport, 'contrast': arm+' - F',
                'matched_contexts': sum(map(len, vals.values())),
                **clustered_interval({p: average(v) for p, v in vals.items()}, strata)})
    # Compare evidential emphasis to equal-length padding and placement to its
    # identical target, rather than comparing different objective candidates.
    for transport in ('frozen_summaries', 'lossless'):
        for name in ('evidence_minus_neutral', 'end_minus_adjacent'):
            values = defaultdict(list)
            for (pid, wi, org, rep), arms in cells.items():
                if org != transport: continue
                anchor = arms['F']['objective_anchor_key']
                objective_arm = next((a for a in ('objective0','objective1','objective2')
                                      if a in arms and arms[a]['selected_keys']==[anchor]), None)
                other = 'neutral' if name=='evidence_minus_neutral' else 'end'
                if objective_arm and other in arms:
                    delta = int(arms[objective_arm]['correct'])-int(arms[other]['correct'])
                    values[pid].append(delta if name=='evidence_minus_neutral' else -delta)
            estimates.append({'transport': transport, 'contrast': name,
                'matched_contexts': sum(map(len, values.values())),
                **clustered_interval({p:average(v) for p,v in values.items()}, strata)})
    interaction = defaultdict(list)
    for pid, wi, org, rep in cells:
        if org != 'lossless' or (pid, wi, 'frozen_summaries', rep) not in cells: continue
        a, b = cells[(pid, wi, org, rep)], cells[(pid, wi, 'frozen_summaries', rep)]
        common = [t for t in ('objective0', 'objective1', 'objective2') if t in a and t in b]
        if common:
            interaction[pid].append(average((int(a[t]['correct'])-int(a['F']['correct']))-
                (int(b[t]['correct'])-int(b['F']['correct'])) for t in common))
    aggregate = []
    for org, arm in sorted({(r['organization'], r['arm']) for r in rows}):
        selected = [r for r in rows if (r['organization'], r['arm']) == (org, arm)]
        correct = sum(r['correct'] for r in selected)
        aggregate.append({'transport': org, 'arm': arm, 'trajectories': len(selected),
            'base_pairs': len({r['pair_id'] for r in selected}), 'correct': correct, 'accuracy': correct/len(selected),
            **{k: sum(r[k] for r in selected) for k in ('invalid_selection', 'feasible_but_not_preferred',
                'necessary_fact_omitted', 'necessary_value_wrong_or_conflicted', 'visible_false_constraint_ignored',
                'correct_choice_erroneous_support', 'operational_failure', 'input_tokens', 'output_tokens', 'inference_seconds_allocated')},
            'allocated_seconds_per_correct': sum(r['inference_seconds_allocated'] for r in selected)/correct if correct else None})
    result = {'complete': True, 'status': 'exploratory_development_diagnostic', 'independent_base_pairs': manifest['base_pairs'],
              'trajectories': len(rows), 'calls': len(rows), 'manifest_sha256': digest(manifest),
              'analysis_source_sha256': digest(Path(__file__).read_text()), 'estimates': estimates, 'aggregate': aggregate,
              'physical_resource_inventory': inventory(directory, rows),
              'objective_repetition_by_transport_interaction': clustered_interval({p: average(v) for p, v in interaction.items()}, strata),
              'limitations': 'Six independent bases, one per family/change stratum: intervals withheld. Model summaries contain their original mistakes; matched effects hold incoming distinct propositions fixed. Between-transport differences are interventions, not identified causal mediation. Historical manager cost is excluded from marginal root-only cost.',
              'resource_totals': {k: sum(r[k] for r in rows) for k in ('input_tokens', 'output_tokens', 'inference_seconds_allocated')}}
    (output/'analysis.json').write_text(json.dumps(result, indent=2)+'\n')
    return result
