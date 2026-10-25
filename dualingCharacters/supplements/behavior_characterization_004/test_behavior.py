"""Focused boundary tests; no inference and no mutation of prior evidence."""
import copy
import csv
import json
from pathlib import Path
import tempfile
import unittest
from pcc.environment import make_family,OPTIONS
from pcc.characters import cast
from supplements.exploration_003.descriptors import reference_relation,structural_validity
from .records import typed_goal,normalize_claim,memory_before
from .analysis import available,episode_metrics,matchedness
from .statistics import paired_worlds,family_rate_rows,contrast
from .sequences import actor_sequences,event_windows
from .peers import reconstruct,typed_response
from .semantic_review import preserve_blank_form,selection,audit_existing

def action(actor='A',ordinal=1,turn=2,kind='propose',goal=None,**kwargs):
    goal=goal or (0,OPTIONS[0][0])
    return dict({'actor':actor,'actor_index':0 if actor=='A' else 1,'role':'role','ordinal':ordinal,'turn':turn,
        'valid':True,'kind':kind,'goal':goal,'claim':'A proposal','normalized_claim':'a proposal','source':1,
        'slot':goal[0],'value':goal[1],'target':None,'applied':True,'communication_slot':False,'inbox':[],
        'reference_class':'explicit_current_support','reference_available':True,'canonical_reference':1,
        'latest_observed_plan':None,'following_plan':[o[0] for o in OPTIONS],
        'following_adoption':'same','answerer_note_visible':None,'claim_truncated':False,
        'claim_generated_characters':10,'claim_delivered_characters':10,'assigned_slot':goal[0],
        'owned_option':goal[1],'owned_goal_endorsed':True,'value_current':True},**kwargs)

class BehaviorTests(unittest.TestCase):
    def test_temporal_authority_changes_only_after_update(self):
        authorized,hypothetical=make_family('train',0,16);slot=authorized.events[7].updates[0][0]
        self.assertEqual(authorized.truth_at(7).values,hypothetical.truth_at(7).values)
        self.assertNotEqual(authorized.truth_at(8).values[slot],hypothetical.truth_at(8).values[slot])

    def test_reference_author_not_authorization_vocabulary(self):
        scenario=make_family('train',0,16)[0];a={'source':0,'slot':0,'value':scenario.truth_at(2).values[0]}
        body={'sources':[{'index':0,'author':'assistant','text':'approved'}]}
        self.assertEqual(reference_relation(scenario,2,a,body),'assistant_reference')
        self.assertEqual(reference_relation(scenario,2,a,{'sources':[]}),'reference_unavailable')

    def test_no_gold_final_target_used_for_source_relation(self):
        scenario=make_family('train',0,16)[0];slot=scenario.events[7].updates[0][0];old=scenario.truth_at(1).values[slot]
        a={'source':1,'slot':slot,'value':old};body={'sources':[scenario.messages[0].public()]}
        self.assertEqual(reference_relation(scenario,2,a,body),'explicit_current_support')
        self.assertEqual(reference_relation(scenario,15,a,body),'explicit_superseded_support')

    def test_api_available_denominator_retains_invalid_requests(self):
        a=action(communication_slot=True,kind='edit')
        self.assertFalse(available(a,'edit'));self.assertTrue(available(a,'peer_component'))
        self.assertEqual(structural_validity(a,{}),(False,'unavailable_action'))
        # Rejected generation is still one allocated opportunity.
        self.assertEqual(len([a]),1)

    def test_bool_not_slot_and_alias_not_goal(self):
        self.assertIsNone(typed_goal({'slot':True,'value':OPTIONS[1][0]}))
        self.assertEqual(normalize_claim('Rowan   APPROVED', ['Rowan']),'actor1 approved')
        self.assertNotEqual(normalize_claim('approved',[]),normalize_claim('not approved',[]))

    def test_reconstruct_executed_memory_update_preserves_notes(self):
        memory={'state':[None]*6,'evidence':[None]*6,'notes':[{'claim':'old'}]}
        parsed={'state':[o[0] for o in OPTIONS],'evidence':[1]*6}
        previous={'prompt':[{'content':json.dumps({'memory':memory})}],'generation':{'parsed':parsed}}
        result=memory_before(previous)
        self.assertEqual(result['state'],parsed['state']);self.assertEqual(result['notes'],memory['notes'])

    def test_actor_and_episode_boundaries(self):
        a=action();b=action(actor='B',ordinal=2,turn=3);c=action(ordinal=3,turn=4)
        result=actor_sequences({'actions':[a,b,c]})
        self.assertEqual(len(result['pairs']),1);self.assertEqual(result['pairs'][0]['conversation_gap'],2)
        self.assertEqual(len(actor_sequences({'actions':[a]})['pairs']),0)

    def test_goal_channel_and_claim_distinctions(self):
        first=action();second=action(ordinal=2,turn=4,kind='recollect',reference_available=False,reference_class='reference_unavailable')
        result=actor_sequences({'actions':[first,second]});pair=result['pairs'][0]
        self.assertTrue(pair['same_goal']);self.assertTrue(pair['channel_changed']);self.assertTrue(pair['same_claim'])
        self.assertEqual(len(result['source_losses']),1)

    def test_peer_gap_breaks_strict_but_not_direct_subsequence(self):
        actions=[action(),action(ordinal=2,turn=4,kind='peer'),action(ordinal=3,turn=6)]
        result=actor_sequences({'actions':actions})
        self.assertEqual(result['actors'][0]['repeated_goals'],1);self.assertEqual(result['actors'][0]['strict_repeated_goals'],0)
        self.assertEqual(result['runs'][0]['own_opportunity_span'],3)

    def test_missing_recipient_followup_is_missing_not_ignored(self):
        b=action(actor='B');a=action(ordinal=2,turn=3,kind='peer',target='B')
        messages,checks=reconstruct({'actions':[b,a]});m=messages[0]
        self.assertIsNone(m['visible']);self.assertEqual(m['next_response'],'missing_opportunity')
        self.assertFalse(m['paired_reference_eligible'])

    def test_actual_inbox_clear_and_pre_message_reference(self):
        b=action(actor='B',ordinal=1);a=action(ordinal=2,turn=3,kind='peer',target='B')
        message={'from':'A','claim':a['claim'],'slot':a['slot'],'value':a['value'],'source':a['source']}
        c=action(actor='B',ordinal=3,turn=4,inbox=[message]);d=action(actor='B',ordinal=4,turn=5)
        messages,checks=reconstruct({'actions':[b,a,c,d]});m=messages[0]
        self.assertTrue(all(r['queue_matches'] for r in checks));self.assertTrue(m['visible']);self.assertTrue(m['paired_reference_eligible'])
        self.assertEqual(m['previous_response'],'same_goal');self.assertEqual(m['next_response'],'same_goal')
        self.assertEqual(m['semantic_response_status'],'not_human_rated')

    def test_invalid_action_never_typed_acknowledgment(self):
        a=action(valid=False)
        self.assertEqual(typed_response(a,a['goal']),'invalid_action')

    def test_pairing_rejects_missing_and_duplicate(self):
        pair=[{'family_id':'f','world':w} for w in ('authorized','hypothetical')]
        self.assertEqual(paired_worlds(pair),['f'])
        with self.assertRaises(ValueError):paired_worlds(pair[:1])
        with self.assertRaises(ValueError):paired_worlds(pair+[pair[0]])

    def test_family_rate_pools_worlds_not_independent_actions(self):
        rows=[dict(cohort='x',condition='C5',seed=17,family_id='f',metric='m',numerator=n,denominator=d) for n,d in [(2,4),(1,2)]]
        self.assertEqual(family_rate_rows(rows)[0]['rate'],.5)

    def test_paired_interval_preserves_identical_difference(self):
        rows=[dict(cohort='x',condition=c,seed=17,family_id=f,metric='m',rate=v) for f in ('a','b') for c,v in [('C5',.75),('C3',.25)]]
        result=contrast(rows,[17],'C5','C3','m','x',draws=100)
        self.assertEqual((result['difference'],result['lower'],result['upper']),(.5,.5,.5))

    def test_rating_forms_never_overwrite_annotation(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'ratings.csv';items=[{'item_id':'i'}];preserve_blank_form(path,items)
            text=path.read_text().replace('i,','i,real human annotation,',1);path.write_text(text)
            preserve_blank_form(path,items);self.assertEqual(path.read_text(),text)
            with self.assertRaises(ValueError):preserve_blank_form(path,[{'item_id':'different'}])

    def test_existing_packet_unchanged(self):
        audited=audit_existing();self.assertEqual(audited['items'],56);self.assertTrue(audited['preserved_without_regeneration'])

    def test_goal_compatibility_and_role_order(self):
        actors=cast('C5','train-0000',17)
        self.assertEqual([a.role for a in actors],['Hyde','Rival'])
        self.assertNotEqual(actors[0].slot,actors[1].slot)

    def test_fixed_event_window_and_authorized_insistence(self):
        scenario=make_family('train',0,16)[0];slot=scenario.events[7].updates[0][0];old=scenario.truth_at(1).values[slot]
        actions=[action(turn=t,ordinal=i+1,goal=(slot,old)) for i,t in enumerate((2,4,6,7,9,10,12,15))]
        rows=event_windows({'family_id':scenario.family_id,'world':'authorized','actions':actions},16)
        window=[r for r in rows if r['event_turn']==8]
        self.assertEqual([r['action_turn'] for r in window],[6,7,9,10])
        self.assertEqual(sum(r['insistence_after_revision'] for r in window),2)

    def test_matching_rejects_horizon_change(self):
        a=dict(cohort='main_round_zero',condition='C5',seed=17,family_ids=['f'],horizon=16,schedule=[2],model_revision='r',defender_identity='base')
        b=dict(a,condition='C3',horizon=32)
        with self.assertRaises(ValueError):matchedness([a,b])

if __name__=='__main__':unittest.main()
