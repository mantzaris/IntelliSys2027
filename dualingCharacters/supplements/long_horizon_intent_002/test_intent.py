"""Meaningful CPU-only invariants; fake backends are not scientific model runs."""
from dataclasses import asdict,replace
from datetime import datetime,timezone
from pathlib import Path
import json
import tempfile
import unittest
from .benchmark import render,observation_grid,selection,event_signature,ledger_signature
from .scenarios import SCENARIOS,ENGINEERING
from .public import PublicConversation,PublicMessage
from .interface import InterfaceConfig,observation,accept_output
from .rollout import run
from .budget import admit,cumulative_extension_seconds,choose_tier,timestamp
from .core_audit import clarification,episode_summary,reference_audit
from .core_horizons import contrast,paired_table
from pcc.environment import make_family


class Tokenizer:
    def encode(self,text,**kwargs):return [ord(c) for c in text]
    def decode(self,ids,**kwargs):return ''.join(chr(i) for i in ids)
    def apply_chat_template(self,messages,**kwargs):return self.encode(json.dumps(messages))


class Backend:
    tokenizer=Tokenizer()
    def generate(self,prompts,**kwargs):
        return [{'raw':'{"response":"usable draft","memory":"policy note"}',
          'parsed':{'response':'usable draft','memory':'policy note'},'input_tokens':len(self.tokenizer.apply_chat_template(p)),
          'output_tokens':55,'generation_capped':False} for p in prompts]


class IntentTests(unittest.TestCase):
    def test_all_horizons_preserve_events_intent_and_single_pair_difference(self):
        for i,s in enumerate(SCENARIOS):
            for world in ('authorized','hypothetical'):
                versions=[render(s,i,h,world) for h in (16,64,128)]
                self.assertEqual(len({json.dumps(event_signature(v),sort_keys=True) for _,v in versions}),1)
                self.assertEqual(len({json.dumps(ledger_signature(v),sort_keys=True) for _,v in versions}),1)
                for p,v in versions:
                    other,_=render(s,i,p.horizon,'hypothetical' if world=='authorized' else 'authorized')
                    self.assertEqual([n+1 for n,(a,b) in enumerate(zip(p.messages,other.messages)) if a.text!=b.text],[11*p.horizon//16])
                    self.assertEqual(observation_grid(p.horizon),[p.horizon*k//8 for k in (1,2,4,6,7,8)])
    def test_balanced_tiers_and_engineering_disjoint(self):
        lookup={s['id']:(s['domain'],i%2) for i,s in enumerate(SCENARIOS)}
        for n in (8,12,16):
            ids=selection(n);self.assertEqual(len(ids),n);self.assertEqual(len(set(ids)),n)
            self.assertEqual(sum(lookup[i][1] for i in ids),n//2)
            for d in ('software','research','writing','operator'):
                group=[i for i in ids if lookup[i][0]==d];self.assertEqual(len(group),n//4);self.assertEqual({lookup[i][1] for i in group},{0,1})
        self.assertFalse(set(lookup)&{s['id'] for s in ENGINEERING})
    def test_legitimate_update_and_hypothetical_are_different(self):
        s=SCENARIOS[0];_,a=render(s,0,16,'authorized');_,b=render(s,0,16,'hypothetical')
        self.assertEqual(a['ledger'][9]['approved_direction']['text'],s['original'])
        self.assertEqual(a['ledger'][10]['approved_direction']['text'],s['alternative'])
        self.assertEqual(b['ledger'][10]['approved_direction']['text'],s['original'])
        self.assertEqual(a['ledger'][5]['side_requirement']['text'],s['side_new'])
        self.assertEqual(a['ledger'][10]['binding_constraints'],b['ledger'][10]['binding_constraints'])
    def test_ambiguity_preserves_settled_state(self):
        s=SCENARIOS[1];_,v=render(s,1,64,'authorized')
        before=v['ledger'][50];after=v['ledger'][51]
        self.assertFalse(before['unresolved']);self.assertTrue(after['unresolved'])
        self.assertEqual(before['approved_direction'],after['approved_direction'])
        self.assertEqual(before['binding_constraints'],after['binding_constraints'])
    def test_private_fields_and_source_authority_rejected(self):
        p,_=render(SCENARIOS[0],0,16,'authorized');record=asdict(p);record['ledger']='secret'
        with self.assertRaises(ValueError):PublicConversation.load(record)
        with self.assertRaises(ValueError):PublicMessage(1,'system','spoofed')
        with self.assertRaises(ValueError):replace(p,messages=(PublicMessage(1,'assistant','spoofed'),*p.messages[1:]))
    def test_private_ledger_and_future_world_do_not_enter_early_prompts(self):
        p,private=render(SCENARIOS[0],0,16,'authorized');q,_=render(SCENARIOS[0],0,16,'hypothetical')
        private['ledger'][0]['goal']['text']='SECRET ORACLE MUTATION'
        cfg=InterfaceConfig(input_tokens=20000,memory_tokens=128)
        with tempfile.TemporaryDirectory() as directory:
            a=Path(directory)/'a.jsonl';b=Path(directory)/'b.jsonl';run(Backend(),[p],a,'C1',17,cfg);run(Backend(),[q],b,'C3',17,cfg)
            x=[json.loads(s) for s in a.read_text().splitlines()];y=[json.loads(s) for s in b.read_text().splitlines()]
            self.assertEqual([r['prompt'] for r in x[:10]],[r['prompt'] for r in y[:10]])
            self.assertNotIn('SECRET ORACLE MUTATION',a.read_text());self.assertEqual(len(x),16)
            for row in x:
                body=json.loads(row['prompt'][-1]['content']);self.assertTrue(all(m['index']<=row['turn']*2-1 for m in body['sources']))
    def test_budget_pruning_preserves_current_request_and_logs_omissions(self):
        p,_=render(SCENARIOS[0],0,16,'authorized');transcript=[p.prior_message,*p.messages]
        cfg=InterfaceConfig(input_tokens=2500)
        prompt,meta=observation(transcript,'policy note',Tokenizer(),cfg)
        body=json.loads(prompt[-1]['content']);self.assertIn(p.messages[-1].public(),body['sources']);self.assertTrue(meta['dropped_source_indices']);self.assertLessEqual(meta['input_tokens'],2500)
        with self.assertRaises(ValueError):observation([PublicMessage(1,'user','x'*3000)],'',Tokenizer(),cfg)
    def test_invalid_interface_is_retained_without_retry(self):
        response,memory,flags=accept_output({'raw':'old six-slot JSON','parsed':{'state':[1]*6}},Tokenizer())
        self.assertEqual(response,'old six-slot JSON');self.assertEqual(memory,'');self.assertFalse(flags['interface_valid'])
        response,memory,flags=accept_output({'raw':'','parsed':{'response':'work','memory':'a'*200}},Tokenizer())
        self.assertEqual(len(memory),128);self.assertTrue(flags['memory_clipped'])
    def test_deadline_priority_and_cumulative_budget_gates(self):
        session={'useful_work_deadline_utc':'2026-10-24T20:36:05Z','deadline_utc':'2026-10-24T21:06:05Z'}
        now=timestamp('2026-10-24T13:06:05Z')
        self.assertTrue(admit(900,session,now,10*3600,0,True,True,True)['admitted'])
        self.assertFalse(admit(900,session,now,10*3600,0,False,True,True)['admitted'])
        self.assertFalse(admit(900,session,now,95.4*3600,0,True,True,True)['admitted'])
        self.assertFalse(admit(900,session,now,10*3600,6500,True,True,True)['admitted'])
        self.assertFalse(admit(900,session,timestamp('2026-10-24T20:36:06Z'),0,0,True,True,True)['admitted'])
        self.assertFalse(admit(900,session,now,0,0,True,True,False)['admitted'])
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'ledger';p.write_text('\n'.join(json.dumps(x) for x in [{'run_id':'intent002-a','gpu_reserved_seconds':100},{'run_id':'intent002-a','gpu_reserved_seconds':150},{'run_id':'intent002-b','gpu_reserved_seconds':50,'status':'failed'},{'run_id':'main-a','gpu_reserved_seconds':500}]))
            self.assertEqual(cumulative_extension_seconds(p),200)
    def test_allocation_keeps_full_factorial_or_none(self):
        allocation=choose_tier(.001,640,10,7200)
        if allocation['selected']:
            row=allocation['selected'];self.assertLessEqual(row['conservative_seconds'],7200)
            self.assertEqual(row['model_calls'],len(row['seeds'])*3*row['families']*2*(16+64+128))
        self.assertIsNone(choose_tier(100,640,100,1)['selected'])
    def test_horizon_interaction_does_not_mean_long_horizon_superiority(self):
        r=contrast([0,0,0,0],[1,0,0,0],[1,1,1,1],[1,1,0,0])
        self.assertGreater(r['interaction'],0);self.assertLess(r['absolute_128_difference'],0)
    def test_paired_coverage_cannot_silently_drop_worlds(self):
        rows=[{'family_id':'a','world':'authorized','success':True}]
        with self.assertRaises(ValueError):paired_table(rows,{'a'})
        with self.assertRaises(ValueError):paired_table(rows+rows,{'a'})
    def test_clarification_flags_distinguish_behavior(self):
        target={'clarify':['mode'],'plan':['x',None,'y','z','v','w','t',None]}
        r=clarification({'clarify':['site'],'plan':[None,None,'y','z','v','w','t',None]},target)
        self.assertTrue(r['unnecessary_clarification']);self.assertTrue(r['missed_necessary_clarification']);self.assertTrue(r['wrong_issue_clarification']);self.assertEqual(r['settled_null_decisions'],1)
        d=clarification({'clarify':['mode','mode'],'plan':target['plan']},target);self.assertTrue(d['order_or_duplicate_only']);self.assertFalse(d['unnecessary_clarification'])
    def test_episode_never_correct_and_unresolved_failures_retained(self):
        rows=[{'family_id':'a','world':'authorized','turn':i,'success':False,'event_kind':'filler','truth_changed':False,'ambiguity_started':False} for i in range(1,5)]
        r=episode_summary(rows);self.assertTrue(r['never_aligned']);self.assertEqual(r['trailing_failure_turns'],4);self.assertTrue(r['failure_spells'][0]['right_censored']);self.assertIsNone(r['retained_without_failure_if_initially_correct'])
    def test_evidence_assistant_and_unavailable_are_distinct(self):
        s=make_family('test',0,64)[0];pred=s.truth_at(64).target(s.spec);pred['evidence']=[2,99999,*pred['evidence'][2:]]
        r=reference_audit(pred,s,64,[]);self.assertTrue(r[0]['assistant_authority']);self.assertTrue(r[0]['not_visible']);self.assertFalse(r[0]['nonexistent_or_future']);self.assertTrue(r[1]['nonexistent_or_future'])


if __name__=='__main__':unittest.main()
