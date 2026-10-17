"""Objective-only repair of cached development summaries, with fresh root calls.

The 2x2 uses the original upstream single/exact report treatments. Repair is an
idealized information intervention, not another independent observation.
"""
from copy import deepcopy
from collections import defaultdict
from pathlib import Path
import gzip
import json
from .metrics import parse, same_value, score_root
from .numerical_audit import field_records, summarize_fields
from .reports import repeat, thaw
from .schema import canonical, digest
from .storage import Ledger, immutable_json
from .replay import execute_requests


def repair_objectives(summaries, branches):
    """Only source-branch objectives may change; no world/oracle is accepted."""
    result = deepcopy(summaries); edits = []
    for item in result:
        obj = item['summary']; branch = branches[item['manager']]
        if not isinstance(obj, dict) or item['parse_status'] != 'valid':
            raise ValueError('Malformed source summary is ineligible for this frozen diagnostic')
        sources = defaultdict(list)
        for report in branch:
            for claim in report.claims():
                if claim.task_identifier == 'objective': sources[claim.key].append((report, claim))
        for key, refs in sources.items():
            value = refs[0][1].asserted_value
            if type(value) not in (int, float) or not all(same_value(c.asserted_value, value) for _, c in refs):
                raise ValueError('Invalid or contradictory source objectives cannot be silently resolved')
            if any(c.scope()!=refs[0][1].scope() for _, c in refs): raise ValueError('Scope collision')
            identifiers = [r.identifier for r, _ in refs]; found = False
            for position, assertion in enumerate(obj['assertions']):
                if assertion[0] != key: continue
                found = True
                citations = assertion[2] if assertion[2] and all(r in identifiers for r in assertion[2]) else [identifiers[0]]
                # A legitimate integral float remains exactly as supplied; this
                # intervention repairs information, not numerical formatting.
                replacement = [key, assertion[1] if same_value(assertion[1], value) else value, citations]
                if canonical(replacement) != canonical(assertion):
                    edits.append({'manager':item['manager'], 'key':key, 'scope':refs[0][1].scope(),
                        'operation':'replace', 'position':position, 'before':deepcopy(assertion), 'after':replacement,
                        'source_reports':identifiers})
                    obj['assertions'][position] = replacement
            if not found:
                replacement = [key, value, [identifiers[0]]]
                edits.append({'manager':item['manager'], 'key':key, 'scope':refs[0][1].scope(), 'operation':'add',
                    'position':len(obj['assertions']), 'before':None, 'after':replacement, 'source_reports':identifiers})
                obj['assertions'].append(replacement)
            if key in obj['unresolved']:
                edits.append({'manager':item['manager'], 'key':key, 'scope':refs[0][1].scope(),
                    'operation':'remove_objective_unresolved_flag', 'before':key, 'after':None, 'source_reports':identifiers})
                obj['unresolved'] = [k for k in obj['unresolved'] if k != key]
    return result, edits


def plan(config):
    source = Path(config['source_run']); corpus = json.loads((source/'frozen-reports.json').read_text())
    pairs = [p for p in json.loads((source/'pairs.json').read_text()) if p['index'] in config['pair_indices']]
    if len(pairs) != len(config['pair_indices']): raise ValueError('Missing frozen source pair')
    jobs = []
    for pair in pairs:
        if pair['evaluation']['kind'] != 'schedule': raise ValueError('Scheduling only')
        scores = json.loads((source/config['model']/'scores'/(pair['pair_id']+'.json')).read_text())
        for wi in config['worlds']:
            world = pair['worlds'][wi]
            for condition in ('single', 'exact'):
                row = next(r for r in scores if (r['world'],r['policy'],r['organization'],r['condition'],r['repetition']) ==
                           (wi,'ordinary','hierarchical',condition,0))
                originals = thaw(corpus[pair['pair_id']]['reports'][wi])
                reports = repeat(originals,corpus[pair['pair_id']]['selected'],condition,pair['split'])
                report_map = {r.identifier:r for r in reports}; calls = {}
                for h in row['request_hashes']:
                    c = json.loads(gzip.decompress((source/config['model']/'calls'/(h+'.json.gz')).read_bytes()));calls[c['stage']]=c
                original_prompt = calls['root']['prompt']; header, payload_text = original_prompt.split('\nINPUT\n',1)
                payload = json.loads(payload_text); incoming = payload['intermediate_summaries']; branches = {}; source_hashes=[]
                for i in range(2):
                    c = calls['manager'+str(i)]; p = json.loads(c['prompt'].split('\nINPUT\n',1)[1])
                    branches[i] = [report_map[r['report']] for r in p['reports']]
                    if any(canonical(r.visible())!=canonical(v) for r,v in zip(branches[i],p['reports'])):
                        raise ValueError('Worker report differs from the actual historical manager input')
                    obj,status = parse(c['response']['text'],world['tie_order'],manager=True)
                    if status!='valid' or c['response']['finish_reason']=='length':raise ValueError('Invalid cached manager')
                    if canonical(obj)!=canonical(next(s['summary'] for s in incoming if s['manager']==i)):
                        raise ValueError('Historical manager/root transport changed')
                    source_hashes.append(c['request_hash'])
                repaired, edits = repair_objectives(incoming,branches)
                before = summarize_fields(field_records(reports,[s['summary'] for s in incoming]))
                for repair in (False,True):
                    arm = ('C' if condition=='single' else 'D') if repair else ('A' if condition=='single' else 'B')
                    supplied = repaired if repair else incoming
                    changed = {**payload,'intermediate_summaries':supplied}
                    prompt = header+'\nINPUT\n'+canonical(changed)
                    if not repair and prompt!=original_prompt:raise ValueError('Baseline root prompt changed')
                    trial={'suite':config['name'],'pair_id':pair['pair_id'],'world':wi,'model':config['model'],
                           'organization':'cached_hierarchy','policy':'ordinary','arm':arm,'repetition':0}
                    trial['trial_id']=digest(trial)[:24]
                    jobs.append({'trial':trial,'pair':pair,'world':world,'reports':reports,'prompt':prompt,'summaries':supplied,
                        'repair_edits':edits if repair else [],'source_summary_sha256':digest(incoming),
                        'source_manager_request_hashes':source_hashes,'source_root_request_hash':calls['root']['request_hash'],
                        'upstream_condition':condition,'selected_report':corpus[pair['pair_id']]['selected'],
                        'source_objective_loss':before['objective_preserved']!=before['objective_fields'],
                        'objective_fields_before':before,
                        'objective_fields_after':summarize_fields(field_records(reports,[s['summary'] for s in supplied]))})
    # Counterbalance arm/world positions within a bounded batch without response-
    # dependent sorting. Seed is shared across arms by the existing seed scheme.
    jobs.sort(key=lambda j:digest([config['ordering_seed'],j['trial']]))
    return pairs,jobs


def input_inventory(jobs):
    return [{k:j[k] for k in ('trial','source_summary_sha256','source_manager_request_hashes','source_root_request_hash',
        'upstream_condition','selected_report','source_objective_loss','objective_fields_before','objective_fields_after','repair_edits')} |
        {'prompt_sha256':digest(j['prompt'])} for j in jobs]


def run(config, model=None, root='artifacts/runs'):
    if config['status']!='frozen':raise ValueError('Freeze first')
    from .models import reuse_or_load
    pairs,jobs=plan(config); inventory=input_inventory(jobs)
    if digest(inventory)!=config['input_inventory_sha256']:raise ValueError('Frozen inputs changed')
    directory=Path(root)/config['name'];source=Path(config['source_run'])
    immutable_json(directory/'manifest.json',{'config':config,'base_pairs':len(pairs),'trajectories':len(jobs),'calls':len(jobs),
        'pairs_sha256':digest(pairs),'input_inventory_sha256':digest(inventory),
        'source_manifest_sha256':digest(json.loads((source/'manifest.json').read_text())),
        'historical_manager_calls':len({h for j in jobs for h in j['source_manager_request_hashes']})})
    immutable_json(directory/'pairs.json',pairs);immutable_json(directory/'inputs.json',inventory)
    immutable_json(directory/'implementation.json',{p.name:p.read_text() for p in Path(__file__).parent.glob('*.py')})
    model,loaded=reuse_or_load(config['model'],config,model);ledger=Ledger(directory/config['model'])
    ledger.event('run_start',settings=model.settings,model_load_seconds=model.load_seconds if loaded else 0,engine_reused=not loaded)
    calls=execute_requests([{'trial':j['trial'],'stage':'root','prompt':j['prompt']} for j in jobs],model,ledger)
    for pair in pairs:
        path=directory/config['model']/'scores'/(pair['pair_id']+'.json')
        if path.exists():continue
        rows=[]
        for j in jobs:
            if j['pair']['pair_id']!=pair['pair_id']:continue
            c=calls[j['trial']['trial_id'],'root'];response=c['response']
            score=score_root(response,j['world'],pair['evaluation']['oracle'][j['trial']['world']],j['reports'])
            rows.append({**j['trial'],'kind':'schedule','family':pair['evaluation']['family'],
                'decision_changed':pair['evaluation']['decision_changed'],**score,
                'source_objective_loss':j['source_objective_loss'],'source_summary_sha256':j['source_summary_sha256'],
                'objective_fields_before':j['objective_fields_before'],'objective_fields_after':j['objective_fields_after'],
                'repair_operations':len(j['repair_edits']),'request_hashes':[c['request_hash']],
                'input_tokens':response['input_tokens'],'output_tokens':response['output_tokens'],
                'inference_seconds_allocated':response['allocated_inference_seconds']})
        immutable_json(path,rows);ledger.event('cluster_complete',pair_id=pair['pair_id'],trajectories=len(rows))
    ledger.event('run_complete',base_pairs=len(pairs),trajectories=len(jobs));ledger.close()
