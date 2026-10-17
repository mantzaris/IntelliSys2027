"""Reproduce numeric transport from immutable COMPLETE pilot/validation calls.

Never reads main-test responses. Detailed per-field records remain outside Git.
"""
from collections import defaultdict, Counter
from pathlib import Path
import gzip
import json
import numpy as np
from rep_sensitivity.metrics import parse, same_value
from rep_sensitivity.numerical_audit import assertion_triples, field_records, summarize_fields
from rep_sensitivity.pilot_interpretation import paired_effect, write_csv
from rep_sensitivity.reports import repeat, thaw, registry
from rep_sensitivity.schema import canonical, digest
from rep_sensitivity.storage import utcnow
from visible_information_v2 import visible_state, assess_choice


def audit(suite):
    root = Path('artifacts/runs', suite)
    manifest = json.loads((root/'manifest.json').read_text())
    pairs = {p['pair_id']: p for p in json.loads((root/'pairs.json').read_text())}
    corpus = json.loads((root/'frozen-reports.json').read_text())
    impl = json.loads((root/'implementation.json').read_text())
    archived = {}; exec(compile(impl['metrics.py'], suite + '/metrics.py', 'exec'), archived)
    rows = []; details = []; examples = []; checks = Counter(); fingerprints = {}
    for model in manifest['config']['models']:
        events = [json.loads(x) for x in (root/model/'events.jsonl').read_text().splitlines()]
        if not any(e['event'] == 'run_complete' for e in events): raise ValueError('Incomplete source')
        scores = [r for p in sorted((root/model/'scores').glob('*.json')) for r in json.loads(p.read_text())]
        for row in scores:
            if row['organization'] != 'hierarchical': continue
            pair = pairs[row['pair_id']]; world = pair['worlds'][row['world']]
            originals = thaw(corpus[row['pair_id']]['reports'][row['world']])
            reports = repeat(originals, corpus[row['pair_id']]['selected'], row['condition'], pair['split'])
            report_map = {r.identifier: r for r in reports}
            calls = {}
            for h in row['request_hashes']:
                raw = (root/model/'calls'/(h+'.json.gz')).read_bytes()
                c = json.loads(gzip.decompress(raw)); calls[c['stage']] = c
                fingerprints[str(root/model/'calls'/(h+'.json.gz'))] = digest(c)
            root_payload = json.loads(calls['root']['prompt'].split('\nINPUT\n', 1)[1])
            checks['root_scope_registry_mismatches'] += canonical(root_payload['scope_registry']) != canonical(registry(reports))
            root_obj, root_status = parse(calls['root']['response']['text'], world['tie_order']+['NONE'])
            raw_choice = root_obj['choice'] if root_obj else None
            expected_correct = raw_choice == pair['evaluation']['oracle'][row['world']]['answer'] and not row['operational_failure']
            checks['primary_choice_score_disagreements'] += raw_choice != row['choice'] or expected_correct != row['correct']
            transported = root_payload['intermediate_summaries']; summaries = []
            summary_objective_errors = 0; summary_objective_denominator = 0; stages = []
            for i in range(2):
                c = calls['manager'+str(i)]; prompt_payload = json.loads(c['prompt'].split('\nINPUT\n', 1)[1])
                branch = [report_map[r['report']] for r in prompt_payload['reports']]
                checks['manager_inputs'] += 1
                checks['source_to_manager_report_mismatches'] += sum(canonical(r.visible()) != canonical(v) for r, v in zip(branch, prompt_payload['reports']))
                checks['manager_registry_mismatches'] += canonical(prompt_payload['scope_registry']) != canonical(registry(branch))
                obj, status = parse(c['response']['text'], world['tie_order']+['NONE'], manager=True)
                old_obj, old_status = archived['parse'](c['response']['text'], world['tie_order']+['NONE'], manager=True)
                checks['archived_parser_disagreements'] += canonical([obj, status]) != canonical([old_obj, old_status])
                checks['manager_output_truncations'] += c['response']['finish_reason'] == 'length'
                raw_obj = json.loads(c['response']['text']) if obj is not None else None
                checks['raw_to_parsed_assertion_changes'] += bool(obj is not None and canonical(assertion_triples(raw_obj)) != canonical(obj['assertions']))
                delivered = next(s for s in transported if s['manager'] == i)
                checks['parsed_to_root_summary_changes'] += canonical(delivered['summary']) != canonical(obj if obj is not None else c['response']['text'])
                summaries.append(obj)
                fs = field_records(branch, [obj]); objs = [f for f in fs if f['objective']]
                summary_objective_denominator += bool(objs)
                summary_objective_errors += bool(objs) and any(not f['preserved'] for f in objs)
                stages.append({'manager': i, 'request_hash': c['request_hash'], 'raw_response_text': c['response']['text'],
                    'source_objectives': [{'report': r.identifier, 'value': r.claim.asserted_value, 'scope': r.claim.scope(), 'key': r.claim.key,
                                           'actual_manager_input': next(x for x in prompt_payload['reports'] if x['report'] == r.identifier)}
                                          for r in branch if r.claim.task_identifier == 'objective'],
                    'raw_objective_assertions': [a for a in assertion_triples(raw_obj) if '/objective/' in a[0]] if raw_obj else [],
                    'parsed_objective_assertions': [a for a in obj['assertions'] if '/objective/' in a[0]] if obj else [],
                    'actual_root_objective_assertions': [a for a in delivered['summary']['assertions'] if '/objective/' in a[0]] if isinstance(delivered['summary'],dict) else [],
                    'fields': [f for f in fs if f['objective']]})
            fields = field_records(reports, summaries); counts = summarize_fields(fields)
            all_correct = all(f['preserved'] for f in fields)
            state = visible_state(world, reports, transported) if world['kind'] == 'schedule' else None
            visible_correct = (state['unique_supported_decision'] and not state['unknown_scope_keys'] and
                not any(f['distorted'] for f in fields) and state['justified_answers'] == [row['oracle_choice']]) if state else all_correct
            choice = row['choice']; candidate = pair['evaluation']['oracle'][row['world']]['candidates'].get(choice)
            record = {**{k:row[k] for k in ('pair_id', 'model', 'world', 'policy', 'condition', 'repetition', 'organization',
                        'kind', 'family', 'decision_changed', 'correct', 'choice', 'invalid_selection', 'operational_failure')},
                'suite': suite, 'trial_id': row['trial_id'], **counts, 'summaries': 2,
                'summaries_with_objectives': summary_objective_denominator, 'summaries_with_objective_loss': summary_objective_errors,
                'objective_retention': counts['objective_preserved']/counts['objective_fields'],
                'all_propositions_preserved': all_correct, 'sufficient_correct_visible': visible_correct,
                'wrong_despite_sufficient_correct_visible': visible_correct and not row['correct'],
                'sufficient_visible_denominator': int(bool(state and state['unique_supported_decision'])),
                'violates_sufficient_visible': bool(state and assess_choice(state, choice, row['operational_failure'])['sufficient_information_violated']),
                'visible_status': state['status'] if state else 'workflow_complete_proposition_check_only',
                'feasible_but_not_preferred': bool(candidate and candidate['feasible'] and not row['correct']),
                'any_objective_loss': counts['objective_preserved'] != counts['objective_fields'],
                'any_boolean_objective': counts['objective_boolean_replacement'] > 0,
                'selected_report': corpus[row['pair_id']]['selected']}
            rows.append(record); details.append({**record, 'fields': fields, 'visible_information': state})
            # Deterministic representatives: influential single/exact/paraphrase;
            # first intact, Boolean, changed-number and omission per source/model.
            tags = []
            if row['pair_id']=='e765f8bb5f0e2aad' and row['policy']=='ordinary' and row['world']==0 and row['repetition']==0:
                tags.append('influential_'+row['condition'])
            for tag, present in [('intact', not record['any_objective_loss']), ('boolean', record['any_boolean_objective']),
                                 ('wrong_number', counts['objective_number_changed']>0), ('omission', counts['objective_omitted']>0)]:
                if present and not any(e['tag']==tag and e['model']==model for e in examples): tags.append(tag)
            for tag in tags:
                examples.append({'tag':tag, **record, 'manager_stages':[s for s in stages if s['source_objectives']],
                    'root_request_hash':calls['root']['request_hash'],
                    'root_output_excerpt':{'choice':root_obj['choice'],'objective_assertions':[a for a in root_obj['assertions'] if '/objective/' in a[0]],
                                           'candidate_assessments':root_obj.get('candidate_assessments')} if root_obj else None,
                    'raw_root_prompt_sha256':digest(calls['root']['prompt'])})
    return rows, details, examples, {'suite':suite, 'implementation_sha256':digest(impl),
        'source_manifest_sha256':digest(manifest), 'raw_call_inventory_sha256':digest(fingerprints),
        'policies_sha256':digest(impl['policies.py']), 'manager_inputs':checks['manager_inputs'], 'checks':dict(checks)}


def main():
    all_rows=[]; all_details=[]; examples=[]; source=[]
    for suite in ('pilot-v7','validation-v7'):
        rows, detail, ex, audit_record = audit(suite)
        all_rows.extend(rows); all_details.extend(detail); examples.extend(ex); source.append(audit_record)
    grouped=defaultdict(list)
    for r in all_rows:grouped[tuple(r[k] for k in ('suite','model','kind','policy','condition'))].append(r)
    groups=[]
    count_keys=[k for k in all_rows[0] if k.startswith(('objective_','constraint_')) and k!='objective_retention']
    count_keys += ['summaries','summaries_with_objectives','summaries_with_objective_loss','correct','invalid_selection','operational_failure',
        'all_propositions_preserved','sufficient_correct_visible','wrong_despite_sufficient_correct_visible','sufficient_visible_denominator',
        'violates_sufficient_visible','feasible_but_not_preferred','any_objective_loss','any_boolean_objective']
    for key, rs in sorted(grouped.items()):
        groups.append({**dict(zip(('suite','model','kind','policy','condition'),key)), 'base_pairs':len({r['pair_id'] for r in rs}),
            'trajectories':len(rs), **{k:sum(r[k] for r in rs) for k in count_keys},
            'base_pairs_with_boolean_objectives':len({r['pair_id'] for r in rs if r['any_boolean_objective']}),
            'base_pairs_with_any_objective_loss':len({r['pair_id'] for r in rs if r['any_objective_loss']}),
            'visible_status_counts':dict(Counter(r['visible_status'] for r in rs))})
    comparisons=[]
    for suite,model,kind in sorted({(r['suite'],r['model'],r['kind']) for r in all_rows}):
        for policies in (['ordinary'],['checklist'],['scope'],['ordinary','checklist']):
            rs=[r for r in all_rows if (r['suite'],r['model'],r['kind'])==(suite,model,kind) and r['policy'] in policies]
            if not rs:continue
            for after,before in [('exact','single'),('paraphrase','single'),('exact','paraphrase')]:
                trans=[{**r,'condition':'single' if r['condition']==before else 'treatment'} for r in rs if r['condition'] in (before,after)]
                for metric in ['correct','objective_retention']:
                    comparisons.append({'suite':suite,'model':model,'kind':kind,'policy':'+'.join(policies),'contrast':after+' - '+before,
                        'metric':metric,**paired_effect(trans,'treatment',metric)})
    changes=[]
    for kind in ('schedule','workflow'):
        for contrast in ('exact - single','paraphrase - single','exact - paraphrase'):
            pair=[next(x for x in comparisons if (x['suite'],x['model'],x['kind'],x['policy'],x['contrast'],x['metric'])==
                       (s,'qwen3',kind,'ordinary+checklist',contrast,'correct')) for s in ('pilot-v7','validation-v7')]
            rng=np.random.default_rng(20271017); sampled=[]
            for stage, effect in zip(('pilot-v7','validation-v7'),pair):
                strata=defaultdict(list)
                for pid,v in effect['base_effects'].items():
                    r=next(r for r in all_rows if r['suite']==stage and r['pair_id']==pid)
                    strata[r['family'],r['decision_changed']].append(v)
                draws=sum(np.sum(rng.choice(v,(10000,len(v)),replace=True),axis=1) for v in strata.values())/len(effect['base_effects'])
                sampled.append(draws)
            delta=sampled[1]-sampled[0]
            changes.append({'model':'qwen3','kind':kind,'policy':'ordinary+checklist','contrast':contrast,
                'definition':'validation repetition effect minus pilot repetition effect; independent base samples',
                'pilot_base_pairs':len(pair[0]['base_effects']),'validation_base_pairs':len(pair[1]['base_effects']),
                'pilot_effect':pair[0]['estimate'],'validation_effect':pair[1]['estimate'],
                'estimate':pair[1]['estimate']-pair[0]['estimate'],'lower':float(np.quantile(delta,.025)),'upper':float(np.quantile(delta,.975))})
    out=Path('results/numerical-pipeline-v1');out.mkdir(parents=True,exist_ok=True)
    result={'utc':utcnow(),'complete':True,'status':'exploratory_complete_source_reanalysis','gpu_calls':0,
        'sources':source,'independent_base_pairs':len({r['pair_id'] for r in all_rows}), 'hierarchical_trajectories':len(all_rows),
        'analysis_source_sha256':digest(Path(__file__).read_text()),'field_scorer_sha256':digest(Path('src/rep_sensitivity/numerical_audit.py').read_text()),
        'denominators':'Fields are unique candidate/full-scope propositions per trajectory, not emitted copies. Summaries with objectives count branches containing an original objective. Boolean/wrong-number/conflict/citation labels overlap. Preserved requires all emissions at the full key correct and no unresolved flag. Accuracy includes malformed completed outputs as errors. Whole-base family-by-change bootstrap retains worlds/policies/repetitions; models separate.',
        'scope_transfer_limit':'Foreign-scope numeric citation mismatch is a certified binding inconsistency; a number coinciding with another candidate alone is not evidence of mental transfer.',
        'sufficiency_limit':'Schedule sufficiency uses strict public report-interface completions, with no hidden value repair. Workflow wrong-despite-sufficient uses the conservative complete-correct-propositions subset only. These observational associations do not identify mediation.',
        'origin':'Raw model output already contains Boolean objectives; frozen prompts explicitly request numerical objectives but the shared assertion schema accepts Boolean or number. Parser normalization and root delivery are tested separately. No claim that the Boolean example caused this without an instruction intervention.',
        'stage_comparison_limit':'Exploratory independent-stage comparison of common Qwen ordinary/checklist settings; distinct splits vary templates, graph patterns, duration/parameter distributions and no-feasible cases. Not a randomized stage intervention.',
        'groups':groups,'comparisons':comparisons,'stage_effect_changes':changes}
    (out/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    (out/'representative-traces.json').write_text(json.dumps(examples,indent=2)+'\n')
    write_csv(out/'field-summary.csv',[{k:v for k,v in r.items() if not isinstance(v,dict)} for r in groups])
    detail=Path('artifacts/analyses/numerical-pipeline-v1');detail.mkdir(parents=True,exist_ok=True)
    (detail/'trajectories.json').write_text(json.dumps(all_rows)+'\n')
    (detail/'fields.json').write_text(json.dumps(all_details)+'\n')
    print(json.dumps({'sources':source,'hierarchical_trajectories':len(all_rows),'stage_effect_changes':changes}))


if __name__=='__main__':main()
