"""Turn-aligned observable action chains; no model execution or hidden-intent labels."""
from collections import defaultdict
import copy
import gzip
import json
import re
from pcc.environment import make_family,OPTIONS,score
from pcc.characters import cast
from pcc.memory import WorkingMemory
from supplements.exploration_003.descriptors import structural_validity,value_relation,reference_relation,valid_slot
from .common import *

DIRECT={'edit','recollect','propose'}

def typed_goal(action):
    slot=action.get('slot');value=action.get('value')
    return (slot,value) if valid_slot(slot) and value in OPTIONS[slot] else None

def normalize_claim(text,aliases):
    text=str(text or '')
    for i,alias in enumerate(aliases):text=re.sub(r'\b'+re.escape(alias)+r'\b',f'actor{i+1}',text,flags=re.I)
    return ' '.join(text.lower().split())

def phase(turn,switch):return 'before_switch' if turn<switch else 'at_switch' if turn==switch else 'after_switch'

def memory_before(previous_row):
    if previous_row is None:return None
    body=json.loads(previous_row['prompt'][-1]['content']);old=body['memory']
    memory=WorkingMemory(copy.deepcopy(old['state']),copy.deepcopy(old['evidence']),copy.deepcopy(old['notes']))
    memory.update(previous_row['generation'].get('parsed',{}))
    return memory.public()

def plan_relation(plan,goal):
    if goal is None or not isinstance(plan,list) or len(plan)<=goal[0]:return None
    value=plan[goal[0]]
    if value==goal[1]:return 'same'
    if value in OPTIONS[goal[0]]:return 'different'
    return 'unknown_value'

def generated_channel(action,aliases):
    generation=action.get('generation')
    if generation is not None and not generation.get('parsed'):return 'malformed'
    kind=action.get('kind')
    if kind=='peer':
        target=action.get('target')
        if target=='Jekyll':return 'peer_answerer'
        if target in aliases and target!=action['actor']:return 'peer_component'
        return 'peer_invalid_recipient'
    return kind if kind in DIRECT|{'pass'} else 'unknown'

def action_features(action,row,previous,scenario,aliases,ordinal,actor_index):
    turn=action['turn'];body=json.loads(action['prompt'][-1]['content']) if action.get('prompt') else None
    current= scenario.truth_at(turn);prior=scenario.truth_at(turn-1)
    if current.target(scenario.spec)!=row['target']:raise ValueError('Current-turn oracle mismatch')
    reconstructed=memory_before(previous)
    before=body['memory'] if body else reconstructed
    if body is not None and reconstructed!=before:raise ValueError('Pre-memory reconstruction disagrees with actual character observation')
    after=json.loads(row['prompt'][-1]['content'])['memory']
    valid,reason=structural_validity(action,body);goal=typed_goal(action);kind=action.get('kind')
    available={m['index']:m for m in body.get('sources',[])} if body else None
    ref=action.get('source');ref_class=reference_relation(scenario,turn,action,body)
    ref_available=ref in available if available is not None and ref is not None else None
    original_claim=str((action.get('generation',{}).get('parsed') or {}).get('claim',action.get('claim','')) or '')
    claim=str(action.get('claim') or '');normalized=normalize_claim(claim,aliases)
    own_history=body.get('own_history',[]) if body else []
    latest_observed_plan=own_history[-1].get('latest_observed_plan') if own_history else None
    canonical=current.evidence[goal[0]] if goal else None
    value_current=goal[1]==current.values[goal[0]] if goal else None
    canon_available=canonical in available if available is not None and canonical is not None else None
    lexical={name:bool(re.search(pattern,normalized)) for name,pattern in {
        'authorization_vocabulary':r'\b(approv\w*|authoriz\w*|confirm\w*|agreed|decided|binding|committed|locked)\b',
        'advocacy_vocabulary':r'\b(prefer\w*|recommend\w*|propos\w*|suggest\w*|optimal)\b',
        'correction_vocabulary':r'\b(correct\w*|contradict\w*|incorrect|inaccurate|unsupported|mistake\w*)\b',
        'authorization_negation':r"\b(not|never|no|haven't|hasn't|isn't)\W+(?:\w+\W+){0,3}(approv\w*|authoriz\w*|confirm\w*|agreed|decided|binding|committed|locked)\b"}.items()}
    changes={name:(before[name]!=after[name] if before is not None else None) for name in ('state','evidence','notes')}
    if before is not None and action.get('memory_changed') is not None and (before!=after)!=action['memory_changed']:
        raise ValueError('Recorded memory-change flag disagrees with actual prompts')
    previous_plan=previous['generation'].get('parsed',{}).get('plan') if previous else None
    following_plan=row['generation'].get('parsed',{}).get('plan')
    field_before=before['state'][goal[0]] if before is not None and goal else None
    field_after=after['state'][goal[0]] if goal else None
    transition=('missing_or_untyped' if before is None or goal is None else
        'unchanged' if field_before==field_after else 'correct_to_incorrect' if field_before==current.values[goal[0]] else
        'incorrect_to_correct' if field_after==current.values[goal[0]] else 'incorrect_to_other_incorrect')
    return {'turn':turn,'ordinal':ordinal,'actor':action['actor'],'actor_index':actor_index,'role':action.get('role'),
        'kind':kind,'channel':generated_channel(action,aliases),'goal':goal,'slot':action.get('slot'),'value':action.get('value'),
        'source':ref,'target':action.get('target'),'claim':claim,'normalized_claim':normalized,
        'claim_generated_characters':len(original_claim),'claim_delivered_characters':len(claim),'claim_truncated':original_claim!=claim,
        'valid':valid,'validity_reason':reason,'applied':action.get('applied'),'rejected_reason':action.get('rejected_reason'),
        'communication_slot':action.get('communication_slot'),'event_kind':scenario.events[turn-1].kind,'phase':phase(turn,scenario.switch_turn),
        'actual_user_revision':scenario.events[turn-1].kind=='set' and current.values!=prior.values,
        'state_changed':changes['state'],'evidence_changed':changes['evidence'],'notes_changed':changes['notes'],
        'pre_memory_origin':'character_observation' if body else 'previous_defender_observation_plus_update',
        'transition':transition,'following_adoption':plan_relation(following_plan,goal),'following_plan':following_plan,
        'answerer_note_visible':any(n.get('author')==action['actor'] and n.get('claim')==claim and n.get('kind')=='peer' for n in after['notes']) if kind=='peer' and action.get('target')=='Jekyll' else None,
        'previous_plan_relation':plan_relation(previous_plan,goal),'following_success':row['metrics']['success'],
        'previous_success_at_current_truth':score(previous['generation'].get('parsed',{}),current,scenario.spec)['success'] if previous else None,
        'latest_observed_plan':latest_observed_plan,'history_records':len(own_history),'inbox':body.get('inbox',[]) if body else None,
        'reference_class':ref_class,'reference_available':ref_available,
        'reference_author':available[ref]['author'] if ref_available else None,
        'reference_exists_in_transcript':isinstance(ref,int) and not isinstance(ref,bool) and 0<=ref<=2*turn-1 if ref is not None else None,
        'indexed_reference_author':('user' if ref%2 else 'assistant') if isinstance(ref,int) and not isinstance(ref,bool) and 0<=ref<=2*turn-1 else None,
        'value_relation':value_relation(scenario,turn,action.get('slot'),action.get('value')),
        'value_current':value_current,'canonical_reference':canonical,'canonical_visible':canon_available,
        'canonical_mismatch':ref!=canonical if goal and ref is not None else None,
        'current_value_inappropriate_citation':bool(value_current and ref_class in {'reference_unavailable','assistant_reference','explicit_contradiction'}) if goal and ref is not None else None,
        'contradictory_value_with_source_visible':bool(value_current is False and canon_available) if goal and canon_available is not None else None,
        'assigned_slot':action.get('assigned_slot'),'owned_option':action.get('owned_option'),
        'owned_goal_endorsed':bool(valid and kind in DIRECT and goal==(action.get('assigned_slot'),action.get('owned_option'))),
        'owned_option_current':action.get('owned_option')==current.values[action['assigned_slot']] if valid_slot(action.get('assigned_slot')) else None,
        'input_tokens':action.get('generation',{}).get('input_tokens'),'output_tokens':action.get('generation',{}).get('output_tokens'),
        'generator_call':int('generation' in action),**lexical}

def load_cell(cell):
    """Stream large local traces; cache only against raw and scientific hashes."""
    folder=ROOT/'artifacts/runs'/cell['run_id'];cache=CACHE/'cells'/(cell['id']+'.json.gz');meta=cache.with_suffix('.meta.json')
    expected={'raw_hashes':cell['raw_hashes'],'science_sha256':sha256(HERE/'SCIENTIFIC_MANIFEST.json')}
    for name,digest in cell['raw_hashes'].items():
        if sha256(folder/name)!=digest:raise ValueError('Locked raw source changed: '+name)
    if cache.exists() and meta.exists():
        recorded=read(meta)
        if recorded.get('inputs')==expected and recorded.get('cache_sha256')==sha256(cache):
            with gzip.open(cache,'rt') as f:return json.load(f)
    raw_actions={};action_name=next((n for n in cell['raw_hashes'] if n.startswith(cell['prefix']+'_characters.jsonl')),None)
    if action_name:
        for a in stream(folder/action_name):
            key=a['family_id'],a['world'],a['turn']
            if key in raw_actions:raise ValueError('Duplicate action')
            raw_actions[key]=a
    scenarios={};casts={}
    for family in cell['family_ids']:
        for scenario in make_family(family.split('-')[0],int(family.split('-')[-1]),cell['horizon']):scenarios[family,scenario.world]=scenario
        casts[family]=cast(cell['condition'],family,cell['seed'])
    episodes={};previous={};turn_name=next(n for n in cell['raw_hashes'] if n in {cell['prefix']+'.jsonl',cell['prefix']+'.jsonl.gz'})
    for row in stream(folder/turn_name):
        key=row['family_id'],row['world'];scenario=scenarios[key];turn=row['turn'];actors=casts[key[0]];aliases=[a.alias for a in actors]
        if scenario.truth_at(turn).target(scenario.spec)!=row['target']:raise ValueError('Temporal truth mismatch')
        episode=episodes.setdefault(key,{'family_id':key[0],'world':key[1],'actions':[],
            'actors':[{'actor':a.alias,'role':a.role,'assigned_slot':a.slot,'owned_option':a.owned_option,'actor_index':i} for i,a in enumerate(actors)],
            'defender_input_tokens':0,'defender_output_tokens':0,'defender_calls':0,'switch_turn':scenario.switch_turn})
        episode['defender_input_tokens']+=row['generation']['input_tokens'];episode['defender_output_tokens']+=row['generation']['output_tokens'];episode['defender_calls']+=1
        action=raw_actions.pop((*key,turn),None)
        if action:
            ordinal=len(episode['actions'])+1;actor_index=aliases.index(action['actor']) if aliases else 0
            if actors and (actor_index!=(ordinal-1)%len(actors) or actors[actor_index].role!=action['role']):raise ValueError('Unexpected role scheduling')
            episode['actions'].append(action_features(action,row,previous.get(key),scenario,aliases,ordinal,actor_index))
        if turn==cell['horizon']:episode['final_success']=row['metrics']['success']
        previous[key]=row
    if raw_actions:raise ValueError('Unjoined action records')
    result=[episodes[key] for key in sorted(episodes)];cache.parent.mkdir(parents=True,exist_ok=True)
    with gzip.open(cache,'wt') as f:json.dump(result,f,separators=(',',':'))
    write(meta,{'inputs':expected,'cache_sha256':sha256(cache)})
    return result
