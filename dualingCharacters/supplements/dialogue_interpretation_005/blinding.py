"""Consistent, disclosed identity substitution without leaking author metadata."""
import re
from .common import rank

FORBIDDEN_KEYS={'condition','seed','role','old_window_id','case_id','run_id','model_revision','family_id',
                'main_paper_theme','biography','interpretation','labels','strongest_supported'}

def substitutions(episode):
    # Original neutral aliases are changed consistently across quotes, notes and history.
    return {**{a['alias']:a['neutral'] for a in episode['actors']},'Jekyll':'Answerer',
            'Hyde':'Component','Rival':'Component','Traditionalist':'Component','Provocateur':'Component'}

def anonymize(value,mapping):
    if isinstance(value,str):
        for old,new in sorted(mapping.items(),key=lambda p:-len(p[0])):
            value=re.sub(r'\b'+re.escape(old)+r'\b',new,value)
        return value
    if isinstance(value,list):return [anonymize(x,mapping) for x in value]
    if isinstance(value,dict):return {k:anonymize(v,mapping) for k,v in value.items() if k not in FORBIDDEN_KEYS and k not in {'locator','metrics'} and not k.endswith(('_locator','_role'))}
    return value

def reviewer_episode(episode):
    mapping=substitutions(episode)
    safe={'item_id':episode['episode_id'],'catalog':episode['catalog'],'turns':episode['turns'],
          'source_bank':episode['source_bank'],'messages':episode['messages'],
          'speakers':[a['neutral'] for a in episode['actors']],
          'identity_note':'Speaker aliases were substituted consistently; condition, seed, biography and AI readings are withheld. Actual claims are otherwise unchanged.'}
    out=anonymize(safe,mapping)
    # Raw JSON strings contain identities too; substitutions above apply uniformly.
    return out

def review_order(items):return sorted(items,key=lambda e:rank('dialogue005-review-order-v1',e['item_id']))
