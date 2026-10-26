"""Fresh-clone tests use small invented fixtures, never substitutes for scientific data."""
import pytest
from .selection import choose
from .extraction import get_value,validate_pair
from .annotations import resolve_span
from .blinding import anonymize
from .statistics import expand,METRICS

def mapping():
    return [{'seed':seed,'family_id':f'train-{i:04}','world':'authorized' if i%2 else 'hypothetical',
             'condition':c,'item_id':f'{seed}-{i}-{c}'} for seed in [17,29,43] for i in range(4) for c in ['C3','C5']]

def test_selection_preserves_anchor_pairs_and_adds_only_four_worlds():
    cases=choose(mapping());assert len(cases)==12
    assert sum(c['opposite_world_included'] for c in cases)==4
    episodes=[e for c in cases for e in c['episodes']]
    assert len(episodes)==48 and sum(e['anchor'] for e in episodes)==36
    assert len({e['episode_id'] for e in episodes})==48
    assert choose(list(reversed(mapping())))==cases

def test_missing_or_duplicate_anchor_fails():
    with pytest.raises(ValueError):choose(mapping()[:-1])
    with pytest.raises(ValueError):choose(mapping()+[mapping()[0]])

def test_decoded_source_locator():
    assert get_value({'prompt':[{'content':'{"sources":[{"text":"exact"}]}'}]},
        {'field':['prompt',0,'content'],'decoded':['sources',0,'text']})=='exact'

def test_wrong_script_pair_is_not_matched():
    e={'available':True,'case_id':'x','world':'authorized','condition':'C3','turns':[{'user':{'index':1,'text':'approved'}}]}
    other={**e,'condition':'C5','turns':[{'user':{'index':1,'text':'hypothetical'}}]}
    with pytest.raises(ValueError):validate_pair([e,other])

def test_quotes_are_not_paraphrased():
    e={'x':{'episode_id':'x','condition':'C3','turns':[{'turn':1,'action':{'claim':'I propose it.','claim_locator':{}}}]}}
    assert resolve_span(e,{'episode_id':'x','turn':1,'excerpt':'propose'})['omission_before']
    with pytest.raises(ValueError):resolve_span(e,{'episode_id':'x','turn':1,'excerpt':'I approved it.'})

def test_blinding_hides_metadata_preserves_substantive_claim():
    out=anonymize({'condition':'C5','role':'Hyde','sender_role':'Generic','seed':17,'claim':'Morgan says it is approved.','locator':{'file':'C5'}}, {'Morgan':'Speaker 1'})
    assert out=={'claim':'Speaker 1 says it is approved.'}

def test_counts_keep_invalid_opportunities_and_missing_denominators():
    r={'condition':'C3','seed':'17','family_id':'fixture'}
    for metric in METRICS:r.update({metric+'_n':'0',metric+'_d':'24'})
    r['peer_before_goal_match_d']='0'
    rows=expand([r]);assert rows[0]['denominator']==24
    assert next(x for x in rows if x['metric']=='peer_before_goal_match')['rate'] is None
    with pytest.raises(ValueError):expand([r,r])
