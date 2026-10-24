"""Invariants that could otherwise manufacture an exploration difference."""
import copy
import json
import pytest
from pcc.environment import make_family,OPTIONS
from .descriptors import value_relation,reference_relation,structural_validity,unique_categories,short_sequences,state_transition,persistence
from .analysis import paired_difference,cost_prefix
from .packet import anonymize,selection,blank_ratings

def action(category=('edit','shared_state','current_original','explicit_current_support'),actor='A',**kw):
    return {'category':category,'actor':actor,'valid':True,'kind':'edit','typed_goal':[0,'Harbor'],
        'tactic':['edit','shared_state','explicit_current_support'],'role':'Generic',**kw}

def test_temporal_truth_not_final_target():
    scenario=make_family('pilot',0,16)[0];event=scenario.events[7];slot,value=event.updates[0]
    assert value_relation(scenario,7,slot,value)!='current_revised'
    assert value_relation(scenario,8,slot,value)=='current_revised'
    old=scenario.truth_at(1).values[slot]
    assert value_relation(scenario,8,slot,old)=='superseded_commitment'

def test_hypothetical_never_authorizes():
    authorized,hypothetical=make_family('pilot',0,16);slot,value=authorized.events[7].updates[0]
    assert value_relation(authorized,8,slot,value)=='current_revised'
    assert value_relation(hypothetical,8,slot,value)=='rejected_option'

def test_source_visibility_and_authorship():
    s=make_family('pilot',0,16)[0];a={'slot':0,'value':s.truth_at(1).values[0],'source':1}
    assert reference_relation(s,1,a,{'sources':[s.messages[0].public()]})=='explicit_current_support'
    assert reference_relation(s,1,a,{'sources':[]})=='reference_unavailable'
    assert reference_relation(s,1,{**a,'source':0},{'sources':[s.prior_assistant_proposal.public()]})=='assistant_reference'

def test_canonicalization_excludes_incidental_names_and_slots():
    # Two different fields/options have exactly the same relational descriptor.
    s=make_family('pilot',0,16)[0]
    assert value_relation(s,1,0,s.truth_at(1).values[0])==value_relation(s,1,5,s.truth_at(1).values[5])
    a=action();b=action(actor='EntirelyDifferentName')
    assert unique_categories([a,b],2)==unique_categories([a],1)

def test_invalid_and_pass_consume_prefix_budget():
    a=action();bad=action(category=None,valid=False);passed=action(category=None,kind='pass')
    assert len(unique_categories([bad,passed,a],2))==0
    assert len(unique_categories([bad,passed,a],3))==1
    with pytest.raises(ValueError):unique_categories([a],2)

def test_unavailable_api_and_empty_claim_invalid():
    a={'kind':'edit','slot':0,'value':'Harbor','claim':'A claim','communication_slot':True}
    assert not structural_validity(a)[0]
    assert not structural_validity({**a,'communication_slot':False,'claim':''})[0]
    assert not structural_validity({**a,'communication_slot':False,'slot':True})[0]

def test_sequences_do_not_bridge_passes_or_episode_boundaries():
    a,b=action(),action(actor='B');invalid=action(category=None,valid=False)
    assert len(short_sequences([a,b],2))==1
    assert not short_sequences([a,invalid,b],3)
    assert not short_sequences([a],1)

def test_paired_alignment_requires_both_worlds():
    a=[{'family_id':'f','world':'authorized','x':1}]
    with pytest.raises(ValueError):paired_difference(a,a,'x')
    b=a+[{'family_id':'f','world':'hypothetical','x':2}]
    with pytest.raises(ValueError):paired_difference(a,b,'x')

def test_paired_world_mean_is_unit():
    a=[{'family_id':f,'world':w,'x':int(w=='authorized')} for f in ('a','b') for w in ('authorized','hypothetical')]
    b=[{**x,'x':0} for x in a]
    result=paired_difference(a,b,'x');assert result['families']==2 and result['difference']==.5

def test_strict_cost_prefix_preserves_order():
    actions=[{'input_tokens':5,'output_tokens':2},{'input_tokens':10,'output_tokens':1},{'input_tokens':1,'output_tokens':1}]
    chosen,spent=cost_prefix(actions,10);assert len(chosen)==1 and spent==7
    with pytest.raises(ValueError):cost_prefix([{'input_tokens':None,'output_tokens':1}],10)

def test_transition_uses_current_truth():
    before=['Harbor']*6;after=['Garden']*6;truth=['Garden']*6
    assert state_transition(before,after,truth,0)=='incorrect_to_correct'
    assert state_transition(before,after,['Harbor']*6,0)=='correct_to_incorrect'
    assert state_transition(None,after,truth,0)=='missing_state'

def test_persistence_does_not_count_truth_reclassification_as_tactic():
    a=action();b=action(category=('edit','shared_state','superseded_commitment','explicit_current_support'))
    result=persistence([a,b])[0]
    assert result['same_goal']==1 and result['same_goal_tactic_changes']==0

def test_anonymization_retains_substance():
    item={'speaker':'Rowan','claim':'Rowan suggests Harbor; Hyde agrees.'}
    result=anonymize(item,{'Rowan':'Speaker 1','Hyde':'Component'})
    assert result=={'speaker':'Speaker 1','claim':'Speaker 1 suggests Harbor; Component agrees.'}

def test_packet_balanced_without_outcome_fields():
    cells=[{'id':c,'condition':c,'cohort':'primary_mechanism','family_ids':[f'f{i}' for i in range(8)]} for c in ('C3','C4','C5','C6','A1','A2','A3')]
    rows=selection(cells);assert len(rows)==56
    for c in cells:
        rs=[r for r in rows if r['cell']==c['id']]
        assert len({r['family_id'] for r in rs})==8
        assert sum(r['world']=='authorized' for r in rs)==4

def test_existing_human_ratings_preserved(tmp_path):
    path=tmp_path/'ratings.csv';items=[{'item_id':'x'}];blank_ratings(path,items)
    text=path.read_text().replace('x,','x,correction',1);path.write_text(text)
    blank_ratings(path,items);assert path.read_text()==text
    with pytest.raises(ValueError):blank_ratings(path,[{'item_id':'y'}])
