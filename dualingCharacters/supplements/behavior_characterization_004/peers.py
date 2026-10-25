"""Reconstruct delivered inboxes; typed follow-ups are candidates, not semantics."""
from collections import defaultdict
import json
import re
from .records import DIRECT,plan_relation

def signature(message):
    return json.dumps({k:message.get(k) for k in ('from','claim','slot','value','source')},sort_keys=True,separators=(',',':'))

def typed_response(action,goal):
    if action is None:return 'missing_opportunity'
    if goal is None:return 'message_untyped'
    if not action['valid']:return 'invalid_action'
    other=action['goal']
    if other is None:return 'other_or_untyped'
    if tuple(other)==tuple(goal):return 'same_goal'
    if other[0]==goal[0]:return 'different_value_same_slot'
    return 'other_or_untyped'

def reconstruct(episode,capacity=6):
    actions=episode['actions'];aliases={a['actor'] for a in actions};pending=defaultdict(list)
    messages=[];by_ordinal={};checks=[]
    for a in actions:
        expected=pending[a['actor']];inbox=a['inbox']
        expected_signatures=[m['_signature'] for m in expected]
        actual_signatures=[signature(m) for m in inbox] if inbox is not None else None
        matched=actual_signatures==expected_signatures if inbox is not None else None
        checks.append({'ordinal':a['ordinal'],'actor':a['actor'],'expected_messages':len(expected),
            'observed_messages':len(inbox) if inbox is not None else None,'queue_matches':matched})
        for message in expected:
            message['observed_at_ordinal']=a['ordinal'];message['visible']=True if matched else None
            message['visibility_status']='visible' if matched else 'queue_reconstruction_disagreement'
        pending[a['actor']]=[]
        if a['kind']!='peer':continue
        target=a['target'];component=target in aliases and target!=a['actor'];answerer=target=='Jekyll'
        row={'ordinal':a['ordinal'],'turn':a['turn'],'sender':a['actor'],'sender_role':a['role'],'recipient':target,
            'recipient_type':'component' if component else 'answerer' if answerer else 'invalid',
            'communication_slot':a['communication_slot'],'structurally_valid':a['valid'],'delivered':a['applied'],
            'goal':a['goal'],'claim_truncated':a['claim_truncated'],'generated_characters':a['claim_generated_characters'],
            'delivered_characters':a['claim_delivered_characters'],'visible':None,'observed_at_ordinal':None,
            'visibility_status':'not_delivered' if a['applied'] is not True else 'no_later_recipient_observation',
            'answerer_note_visible':a['answerer_note_visible'],'following_defender_adoption':a['following_adoption']}
        row['_signature']=signature({'from':a['actor'],'claim':a['claim'],'slot':a['slot'],'value':a['value'],'source':a['source']})
        messages.append(row);by_ordinal[a['ordinal']]=row
        if component and a['applied'] is True:
            pending[target].append(row)
            if len(pending[target])>capacity:
                evicted=pending[target].pop(0);evicted['visible']=False;evicted['visibility_status']='evicted_before_observation'
        elif answerer:
            row['visible']=a['answerer_note_visible'];row['visibility_status']='answerer_note_visible' if a['answerer_note_visible'] else 'not_visible_to_answerer'
        else:row['visible']=False
    for row in messages:
        sender=next(a for a in actions if a['ordinal']==row['ordinal'])
        recipient_actions=[a for a in actions if a['actor']==row['recipient']] if row['recipient_type']=='component' else []
        past=[a for a in recipient_actions if a['ordinal']<row['ordinal']]
        future=[a for a in recipient_actions if a['ordinal']>row['ordinal']]
        before=past[-1] if past else None;first=future[0] if future else None;second=future[1] if len(future)>1 else None
        row.update(previous_recipient_opportunity=before['ordinal'] if before else None,
            next_recipient_opportunity=first['ordinal'] if first else None,
            second_recipient_opportunity=second['ordinal'] if second else None,
            next_turn_lag=first['turn']-row['turn'] if first else None,
            previous_response=typed_response(before,row['goal']),next_response=typed_response(first,row['goal']),
            second_response=typed_response(second,row['goal']),
            next_same_slot_type=(first['communication_slot']==before['communication_slot']) if first and before else None,
            next_applied_matching_direct=bool(first and first['valid'] and first['kind'] in DIRECT and first['applied'] is True and typed_response(first,row['goal'])=='same_goal'),
            next_mentions_sender=bool(first and re.search(r'\b'+re.escape(row['sender'])+r'\b',first['claim'],re.I)),
            next_defender_adoption=plan_relation(first['following_plan'],row['goal']) if first else None,
            semantic_response_status='not_human_rated')
        row['paired_reference_eligible']=row['recipient_type']=='component' and row['visible'] is True and row['goal'] is not None and before is not None and first is not None
        row.pop('_signature')
    return messages,checks
