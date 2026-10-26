"""Extract exact selected records once; never fabricate speech from action fields."""
from collections import defaultdict
import copy
from pcc.environment import make_family
from pcc.characters import cast
from supplements.behavior_characterization_004.records import action_features, memory_before
from supplements.behavior_characterization_004.peers import reconstruct
from .common import *

def locator(path, file_hash, line, field, decoded=None):
    result = {'file': path, 'sha256': file_hash, 'record': line, 'field': field}
    if decoded is not None: result['decoded'] = decoded
    return result

def get_value(record, location):
    value = record
    for step in location['field']: value = value[step]
    if 'decoded' in location:
        value = json.loads(value)
        for step in location['decoded']: value = value[step]
    return value

def source_text_loc(path, sha, line, body, source_index):
    index = next(i for i, m in enumerate(body['sources']) if m['index'] == source_index)
    return locator(path, sha, line, ['prompt', 1, 'content'], ['sources', index, 'text'])

def validate_pair(episodes):
    groups = defaultdict(list)
    for episode in episodes: groups[episode['case_id'], episode['world']].append(episode)
    for group in groups.values():
        actual = [e for e in group if e['available']]
        if len({e['condition'] for e in actual}) != len(actual): raise ValueError('Duplicate matched cell')
        if actual:
            scripts = [[(t['user']['index'], t['user']['text']) for t in e['turns']] for e in actual]
            if any(s != scripts[0] for s in scripts): raise ValueError('Matched conditions have different user scripts')

def run():
    selection = read(HERE/'SELECTION.json'); census = read(HERE/'EVIDENCE_CUTOFF.json')
    output = CACHE/'episodes.json'; raw_output = CACHE/'selected_records.jsonl.gz'
    keys = {'selection': digest(HERE/'SELECTION.json'), 'census': digest(HERE/'EVIDENCE_CUTOFF.json'),
            'extractor': digest(Path(__file__)), 'feature_code': digest(ROOT/'supplements/behavior_characterization_004/records.py'),
            'peer_code': digest(ROOT/'supplements/behavior_characterization_004/peers.py')}
    bindings = census['bound_dialogue_runs']
    for bound in bindings.values():
        for path, sha in bound.get('raw_files', {}).items(): verified(ROOT/path, sha)
    meta = CACHE/'EXTRACTION_CACHE.json'
    if meta.exists() and output.exists() and raw_output.exists():
        cached = read(meta)
        if cached['inputs'] == keys and digest(output) == cached['episodes_sha256'] and digest(raw_output) == cached['selected_records_sha256']:
            print('Using source-hash-validated selected episode cache'); return
    choices = defaultdict(list)
    for case in selection['cases']:
        for e in case['episodes']: choices[e['run_id']].append(dict(e, case_id=case['case_id']))
    episodes = []; selected_records = []; quotes = []
    for run_id, requested in choices.items():
        bound = bindings[run_id]
        if not bound['available']:
            episodes.extend(dict(e, available=False, reason=bound['reason']) for e in requested); continue
        needed = {(e['family_id'], e['world']) for e in requested}; rows = defaultdict(list); actions = defaultdict(list)
        files = {}
        for path, sha in bound['raw_files'].items():
            if '_interventions' in path or '_summary' in path: continue
            action_file = '_characters' in path; files['action' if action_file else 'turn'] = (path, sha)
            for line, record in stream(ROOT/path):
                key = record['family_id'], record['world']
                if key not in needed: continue
                (actions if action_file else rows)[key].append((line, record))
                selected_records.append({'file': path, 'file_sha256': sha, 'record': line, 'value': record})
        for choice in requested:
            key = choice['family_id'], choice['world']; chronological = rows[key]; action_rows = actions[key]
            if [r['turn'] for _,r in chronological] != list(range(1,17)): raise ValueError('Incomplete/out-of-order turns')
            if [r['turn'] for _,r in action_rows] != bound['schedule']: raise ValueError('Incomplete action schedule')
            scenario = next(s for s in make_family('train', int(key[0].split('-')[-1]), 16) if s.world == key[1])
            characters = cast(choice['condition'], key[0], choice['seed']); aliases = [a.alias for a in characters]
            episode = dict(choice, available=True, model_revision=bound['model_revision'],
                actors=[{'alias':a.alias,'neutral':f'Speaker {i+1}','role':a.role,'slot':a.slot,'owned_option':a.owned_option} for i,a in enumerate(characters)],
                catalog=None, turns=[], source_bank={}, features=[])
            by_turn = {a['turn']:(line,a) for line,a in action_rows}; previous=None
            for line, row in chronological:
                turn = row['turn']; body = json.loads(row['prompt'][1]['content']); path,sha=files['turn']
                if row['target'] != scenario.truth_at(turn).target(scenario.spec): raise ValueError('Temporal truth mismatch')
                if row['condition'] != choice['condition'] or row['seed'] != choice['seed']: raise ValueError('Run identity mismatch')
                user = next(m for m in body['sources'] if m['index'] == body['latest_user_index'])
                if user['text'] != scenario.messages[turn-1].text: raise ValueError('Saved user source disagrees with script')
                for m in body['sources']:
                    existing = episode['source_bank'].get(str(m['index']))
                    if existing and existing['text'] != m['text']: raise ValueError('Immutable source changed')
                    episode['source_bank'].setdefault(str(m['index']), dict(m, locator=source_text_loc(path,sha,line,body,m['index'])))
                episode['catalog']=body['catalog']
                t={'turn':turn,'event_kind':scenario.events[turn-1].kind,'user':dict(user,locator=source_text_loc(path,sha,line,body,user['index'])),
                   'defender':{'parsed':row['generation']['parsed'],'raw':row['generation']['raw'],
                               'locator':locator(path,sha,line,['generation','raw']), 'metrics':row['metrics'],
                               'input_tokens':row['generation']['input_tokens'],'output_tokens':row['generation']['output_tokens']},
                   'defender_observation':body,'defender_observation_locator':locator(path,sha,line,['prompt',1,'content']),
                   'analyst_only_target':row['target'],'target_locator':locator(path,sha,line,['target']),
                   'memory_after_answer':memory_before(row),'action':None}
                episode['source_bank'][str(2*turn)]={'index':2*turn,'author':'assistant','text':row['generation']['raw'],'locator':t['defender']['locator']}
                quotes.extend([{'episode_id':choice['episode_id'],'kind':'user','text':user['text'],'locator':t['user']['locator']},
                               {'episode_id':choice['episode_id'],'kind':'answer_raw','text':row['generation']['raw'],'locator':t['defender']['locator']}])
                if turn in by_turn:
                    aline,a=by_turn[turn];apath,asha=files['action'];obs=json.loads(a['prompt'][1]['content'])
                    feature=action_features(a,row,previous,scenario,aliases,len(episode['features'])+1,aliases.index(a['actor']))
                    episode['features'].append(feature)
                    generated=(a['generation'].get('parsed') or {}).get('claim','')
                    action={'opportunity':feature['ordinal'],'actor':a['actor'],'neutral_speaker':f'Speaker {aliases.index(a["actor"])+1}',
                        'kind':a['kind'],'slot':a['slot'],'value':a['value'],'source':a['source'],'target':a.get('target'),
                        'claim':a['claim'],'generated_claim':generated,'truncated':generated!=a['claim'],
                        'applied':a['applied'],'rejected_reason':a.get('rejected_reason'),
                        'communication_slot':a['communication_slot'],'observation':obs,
                        'memory_before':obs['memory'],'memory_before_answer':body['memory'],
                        'locator':locator(apath,asha,aline,[]),'claim_locator':locator(apath,asha,aline,['claim']),
                        'generated_claim_locator':locator(apath,asha,aline,['generation','parsed','claim']),
                        'observation_locator':locator(apath,asha,aline,['prompt',1,'content']),
                        'input_tokens':a['generation']['input_tokens'],'output_tokens':a['generation']['output_tokens']}
                    t['action']=action
                    for m in obs['sources']:
                        existing=episode['source_bank'].get(str(m['index']))
                        if existing and existing['text']!=m['text']:raise ValueError('Character source differs')
                        episode['source_bank'].setdefault(str(m['index']),dict(m,locator=source_text_loc(apath,asha,aline,obs,m['index'])))
                    quotes.append({'episode_id':choice['episode_id'],'kind':'logged_claim','text':a['claim'],'locator':action['claim_locator']})
                    if generated!=a['claim']:quotes.append({'episode_id':choice['episode_id'],'kind':'generated_claim','text':generated,'locator':action['generated_claim_locator']})
                episode['turns'].append(t);previous=row
            messages,checks=reconstruct({'actions':episode['features']},bound['config']['history_actions'])
            if any(c['queue_matches'] is not True for c in checks): raise ValueError('Actual inbox mismatch')
            episode['messages']=messages;episode['inbox_checks']=checks
            episodes.append(episode)
    validate_pair(episodes)
    CACHE.mkdir(parents=True,exist_ok=True)
    with gzip.GzipFile(filename=str(raw_output),mode='wb',mtime=0) as handle:
        for record in selected_records:handle.write((json.dumps(record,ensure_ascii=False,separators=(',',':'))+'\n').encode())
    write(output,episodes);write(CACHE/'QUOTATIONS.json',quotes)
    write(meta,{'inputs':keys,'episodes_sha256':digest(output),'selected_records_sha256':digest(raw_output)})
    write(REPORTS/'EXTRACTION.json',{'available_episodes':sum(e['available'] for e in episodes),'anchor_episodes':sum(e['available'] and e['anchor'] for e in episodes),
        'complete_turns':sum(len(e.get('turns',[])) for e in episodes),'actions':sum(len(e.get('features',[])) for e in episodes),
        'unique_families':len({e['family_id'] for e in episodes}),'records':len(selected_records),'quote_entries':len(quotes),
        'episodes_path':relative(output),'episodes_sha256':digest(output),'selected_records_path':relative(raw_output),
        'selected_records_sha256':digest(raw_output),'quote_manifest_path':relative(CACHE/'QUOTATIONS.json'),
        'quote_manifest_sha256':digest(CACHE/'QUOTATIONS.json'),'inbox_disagreements':0,
        'sources':{p:s for b in bindings.values() for p,s in b.get('raw_files',{}).items()}})
    print({k:v for k,v in read(REPORTS/'EXTRACTION.json').items() if k in ['available_episodes','anchor_episodes','complete_turns','actions','records']})

if __name__ == '__main__':run()
