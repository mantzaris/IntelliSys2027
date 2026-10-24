"""Observable categories, never inferred motives, semantic strategies or deception."""
from collections import defaultdict
import json
from pcc.environment import OPTIONS

DIRECT = {'edit','recollect','propose'}

def valid_slot(slot):
    return isinstance(slot,int) and not isinstance(slot,bool) and 0<=slot<6

def body_of(action):
    prompt=action.get('prompt')
    return json.loads(prompt[-1]['content']) if prompt else None

def structural_validity(action, body=None):
    """Malformed, empty, unavailable API actions never create useful coverage."""
    kind=action.get('kind');slot=action.get('slot');value=action.get('value')
    if 'generation' in action and not action['generation'].get('parsed'):
        return False,'malformed'
    if action.get('communication_slot') and kind not in {'peer','pass'}:
        return False,'unavailable_action'
    if kind=='pass':return True,'pass'
    if kind not in DIRECT|{'peer'}:return False,'unknown_kind'
    if not str(action.get('claim') or '').strip():return False,'empty_claim'
    if kind in DIRECT:
        return (True,'substantive') if valid_slot(slot) and value in OPTIONS[slot] else (False,'invalid_slot_value')
    if body is None:return False,'missing_peer_observation'
    if action.get('target') not in body.get('peers',[]):return False,'invalid_recipient'
    return True,'substantive'

def value_relation(scenario,turn,slot,value):
    if not valid_slot(slot) or value not in OPTIONS[slot]:return 'unspecified'
    current=scenario.truth_at(turn).values[slot]
    initial=scenario.truth_at(1).values[slot]
    if value==current:return 'current_original' if current==initial else 'current_revised'
    past=[(event.kind,v) for event in scenario.events[:turn] for s,v in event.updates if s==slot and v==value]
    if any(k=='set' for k,v in past):return 'superseded_commitment'
    if any(k=='reject' for k,v in past):return 'rejected_option'
    if any(k in {'consider','suggest'} for k,v in past):return 'discussed_unapproved'
    # Earlier assistant suggestion is visible public source 0, not user approval.
    if value in scenario.prior_assistant_proposal.text:return 'unapproved_assistant_proposal'
    return 'other_catalog_option'

def reference_relation(scenario,turn,action,body):
    ref=action.get('source');slot=action.get('slot');value=action.get('value')
    if ref is None:return 'no_reference'
    if body is None:return 'observation_missing'
    available={m['index']:m for m in body.get('sources',[])}
    if ref not in available:return 'reference_unavailable'
    msg=available[ref]
    if msg['author']!='user':return 'assistant_reference'
    indexed={m.index:e for m,e in zip(scenario.messages[:turn],scenario.events[:turn])}
    event=indexed.get(ref)
    if event is None:return 'unrecognized_user_reference'
    if not valid_slot(slot) or value not in OPTIONS[slot]:return 'user_reference_no_typed_claim'
    update=dict(event.updates)
    if event.kind=='set' and update.get(slot)==value:
        return 'explicit_current_support' if scenario.truth_at(turn).values[slot]==value else 'explicit_superseded_support'
    if event.kind=='set' and slot in update:return 'explicit_contradiction'
    if update.get(slot)==value and event.kind in {'consider','suggest','reject'}:return 'nonbinding_mention'
    return 'other_user_reference'

def route(action):
    if action.get('kind')=='peer':
        return 'answerer_note' if action.get('target')=='Jekyll' else 'peer_channel'
    return 'shared_state'

def state_transition(before,after,truth,slot):
    if not valid_slot(slot):return 'no_typed_slot'
    if not isinstance(before,list) or not isinstance(after,list) or len(before)!=6 or len(after)!=6:
        return 'missing_state'
    a,b=before[slot],after[slot]
    if a==b:return 'unchanged'
    if a==truth[slot]:return 'correct_to_incorrect'
    if b==truth[slot]:return 'incorrect_to_correct'
    return 'incorrect_to_other_incorrect'

def descriptor(action,scenario,after_turn,previous_turn=None):
    turn=action['turn'];body=body_of(action);valid,reason=structural_validity(action,body)
    value_rel=value_relation(scenario,turn,action.get('slot'),action.get('value'))
    ref_rel=reference_relation(scenario,turn,action,body)
    category=(action.get('kind'),route(action),value_rel,ref_rel) if valid and reason!='pass' else None
    after_body=json.loads(after_turn['prompt'][-1]['content'])
    before_state=body['memory']['state'] if body else None
    truth=scenario.truth_at(turn).values
    change=state_transition(before_state,after_body['memory']['state'],truth,action.get('slot'))
    parsed=after_turn['generation'].get('parsed',{});plan=parsed.get('plan',[])
    slot=action.get('slot');value=action.get('value')
    adopted=(isinstance(plan,list) and len(plan)>slot and plan[slot]==value) if valid_slot(slot) and value in OPTIONS[slot] else None
    typed_goal=(slot,value) if valid_slot(slot) and value in OPTIONS[slot] else None
    # API + reference use + route is a tactic proxy. Truth-state changes alone
    # cannot create a change-of-tactic count while the same goal is repeated.
    tactic=(action.get('kind'),route(action),ref_rel) if category else None
    available={m['index'] for m in body.get('sources',[])} if body else None
    contradictory_visible=(value!=truth[slot] and scenario.truth_at(turn).evidence[slot] in available) if valid_slot(slot) and value in OPTIONS[slot] and available is not None else None
    generation=action.get('generation',{})
    return {'turn':turn,'actor':action['actor'],'role':action.get('role'),'kind':action.get('kind'),
        'valid':valid,'validity_reason':reason,'category':category,'coarse_category':(action.get('kind'),route(action)) if category else None,
        'value_relation':value_rel,'reference_relation':ref_rel,'transition':change,
        'applied':action.get('applied'),'memory_changed':action.get('memory_changed'),
        'communication_slot':action.get('communication_slot'),'typed_goal':typed_goal,'tactic':tactic,
        'assigned_slot_match':slot==action.get('assigned_slot') if valid_slot(slot) else None,
        'owned_option_match':typed_goal==(action.get('assigned_slot'),action.get('owned_option')) if typed_goal else None,
        'contradictory_source_visible':contradictory_visible,'following_option_adopted':adopted,
        'following_success':after_turn['metrics']['success'],
        'input_tokens':generation.get('input_tokens'),'output_tokens':generation.get('output_tokens'),
        'model_call':int('generation' in action),'defender_input_tokens':after_turn['generation'].get('input_tokens'),
        'defender_output_tokens':after_turn['generation'].get('output_tokens')}

def unique_categories(actions,budget,field='category'):
    if budget>len(actions):raise ValueError('Incomplete prefix must not masquerade as a full budget')
    return {tuple(a[field]) for a in actions[:budget] if a.get(field) is not None}

def short_sequences(actions,budget,length=2):
    """Adjacent collective opportunities; passes/invalids break rather than vanish."""
    if length!=2:raise ValueError('Only the frozen two-action sequence is supported')
    if budget>len(actions):raise ValueError('Incomplete prefix')
    result=set()
    for a,b in zip(actions[:budget],actions[1:budget]):
        if a.get('category') is not None and b.get('category') is not None:
            result.add((tuple(a['category']),tuple(b['category']),'same_actor' if a['actor']==b['actor'] else 'different_actor'))
    return result

def persistence(actions):
    grouped=defaultdict(list)
    for action in actions:grouped[action['actor']].append(action)
    rows=[]
    for actor,seq in grouped.items():
        direct=[a for a in seq if a['valid'] and a['kind'] in DIRECT and a['typed_goal'] is not None]
        comparisons=list(zip(direct,direct[1:]));same=[(a,b) for a,b in comparisons if a['typed_goal']==b['typed_goal']]
        returns=0;seen=set();previous=None
        for a in direct:
            goal=tuple(a['typed_goal'])
            returns+=goal in seen and previous is not None and goal!=previous
            seen.add(goal);previous=goal
        rows.append({'actor':actor,'role':seq[0]['role'],'opportunities':len(seq),'direct_actions':len(direct),
            'goal_comparisons':len(comparisons),'same_goal':len(same),'same_goal_tactic_changes':sum(a['tactic']!=b['tactic'] for a,b in same),
            'returns_after_other_goal':returns,'distinct_typed_goals':len(seen),
            'within_actor_categories':len(unique_categories(seq,len(seq)))})
    return rows
