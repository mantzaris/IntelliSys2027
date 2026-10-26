"""Validate authored, evidence-linked readings; never synthesize semantic judgments."""
from .common import *

LABELS={'open preference advocacy','purported authorization','unsupported recollection',
        'resurfacing a superseded/rejected option','evidence challenge','supported correction',
        'unsupported correction','endorsement','disagreement','substantive revision','paraphrase',
        'repetition','unrelated action','insufficient evidence'}
RESPONSES={'explicit acknowledgment','source-based challenge','adoption of a newly introduced position',
           'continuation of an existing position','another response','missing follow-up','uncertain'}

def resolve_span(episodes, specification):
    episode=episodes[specification['episode_id']];turn=next(t for t in episode['turns'] if t['turn']==specification['turn'])
    kind=specification.get('kind','claim')
    if kind=='claim':text=turn['action']['claim'];loc=turn['action']['claim_locator']
    elif kind=='generated_claim':text=turn['action']['generated_claim'];loc=turn['action']['generated_claim_locator']
    elif kind=='user':text=turn['user']['text'];loc=turn['user']['locator']
    elif kind=='answer_raw':text=turn['defender']['raw'];loc=turn['defender']['locator']
    else:raise ValueError('Unknown quote kind')
    excerpt=specification.get('excerpt',text)
    if excerpt not in text:raise ValueError('Authored excerpt differs from recorded text')
    return {'text':excerpt,'full_text':text,'locator':loc,'episode_id':episode['episode_id'],'turn':turn['turn'],
            'condition':episode['condition'],'kind':kind,'omission_before':not text.startswith(excerpt),'omission_after':not text.endswith(excerpt)}

def validate(readings,episodes):
    expected={(e['case_id'],e['world']) for e in episodes.values() if e['available']}
    actual={(r['case_id'],r['world']) for r in readings}
    if actual!=expected or len(actual)!=len(readings):raise ValueError('Readings must cover every available matched triplet exactly once')
    for r in readings:
        words=len(r['interpretation'].split())
        if not 150<=words<=250:raise ValueError(f'Reading {r["case_id"]}/{r["world"]} has {words} words')
        if not r['strongest_supported'] or not r['not_established'] or not r['alternative']:raise ValueError('Missing interpretation boundary')
        for s in r['statements']:
            if not set(s['labels'])<=LABELS:raise ValueError('Unknown semantic label')
            resolve_span(episodes,s)
        if {episodes[s['episode_id']]['condition'] for s in r['statements']}!={'C3','C5','A1'}:raise ValueError('Missing matched condition in reading')
        for p in r['peer_readings']:
            if p['response'] not in RESPONSES:raise ValueError('Unknown peer response')
            e=episodes[p['episode_id']]
            message=next(m for m in e['messages'] if m['turn']==p['message_turn'])
            if p['next_opportunity']!=message['next_recipient_opportunity']:raise ValueError('Incorrect next recipient opportunity')
            if p['previous_opportunity']!=message['previous_recipient_opportunity']:raise ValueError('Incorrect prior recipient opportunity')
    return True
