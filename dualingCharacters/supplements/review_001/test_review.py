import copy
import itertools
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from pcc.config import RunConfig
from pcc.environment import make_family,OPTIONS,Truth,Event,Message,score
from pcc.memory import WorkingMemory,observation
from .inputs import memory_variant,collapsed_prompt,selected_families
from .fresh import family,design,actors_for
from .rollout import route_action,run_rollout
from .exposure import replay
from .allocation import choose
from .freeze import manifests
from .analyze import pairs,contrast
from .gpu import generate_records


class ReviewTests(unittest.TestCase):
    def test_removals_preserve_user_bytes_authority_catalog_and_request(self):
        scenario=make_family('test',17,64)[0]
        transcript=list(scenario.source_messages())+[Message(126,'assistant','Unsupported memory summary'),scenario.messages[-1]]
        original,_=observation(scenario.spec,transcript,WorkingMemory(['junk']*6,[900]*6,[{'claim':'x'}]))
        self.assertEqual(original,memory_variant(original,'A0'))
        body=json.loads(original[-1]['content']);a1=json.loads(memory_variant(original,'A1')[-1]['content']);a2=json.loads(memory_variant(original,'A2')[-1]['content'])
        expected=copy.deepcopy(body);expected['memory']=WorkingMemory().public();self.assertEqual(a1,expected)
        expected['sources']=[m for m in expected['sources'] if m['author']!='assistant'];self.assertEqual(a2,expected)
        self.assertEqual(json.loads(original[-1]['content']),body)
        prompt=collapsed_prompt(scenario.spec,scenario.messages);common=json.loads(prompt[-1]['content'])
        self.assertTrue(all(m['author']=='user' for m in common['sources']));self.assertLessEqual(len(common['sources']),12)
        self.assertEqual(common['latest_user_index'],127)

    def test_selection_pairs_balance_and_fresh_oracles(self):
        for n in (32,64,120,240):
            selected=selected_families(n);self.assertEqual(len(selected),n)
            counts={}
            for i in selected:
                s=make_family('test',i,64)[0];key=s.spec.domain,s.spec.online_override;counts[key]=counts.get(key,0)+1
            self.assertEqual(set(counts.values()),{n//8})
        cells={};alignment={};order={}
        for n in range(64):
            a,h=family('balanced',n,64);key=(a.spec.domain,a.spec.online_override,bool(a.truth_at(64).pending));cells[key]=cells.get(key,0)+1
            slot,alternative=a.events[a.switch_turn-1].updates[0]
            self.assertEqual(a.truth_at(64).values[slot],alternative)
            self.assertNotEqual(h.truth_at(64).values[slot],alternative)
            self.assertEqual(a.messages[:31],h.messages[:31]);self.assertEqual(a.messages[32:],h.messages[32:])
            self.assertEqual(score(a.truth_at(64).target(a.spec),a.truth_at(64),a.spec)['success'],True)
        self.assertEqual(len(cells),16);self.assertEqual(set(cells.values()),{4})
        for n in range(16):
            d=design('mechanism',n);alignment[d['initial_alignment']]=alignment.get(d['initial_alignment'],0)+1;order[d['first_role']]=order.get(d['first_role'],0)+1
            a=actors_for('mechanism',n,'B1');b=actors_for('mechanism',n,'B0')
            self.assertEqual(a[0].slot,a[1].slot);self.assertNotEqual(a[0].owned_option,a[1].owned_option);self.assertNotEqual(b[0].slot,b[1].slot)
        self.assertEqual(alignment,{'Hyde':6,'Rival':5,'neither':5});self.assertEqual(order,{0:8,1:8})
        self.assertEqual(manifests()['exact_graph_overlap'],0)

    def test_routing_cannot_add_jekyll_notes_in_communication(self):
        for c in ('C-single','C-peer','C-off'):
            actors=actors_for('mechanism',0,c);memory=WorkingMemory();actor=actors[0]
            action={'kind':'peer','slot':actor.slot,'value':actor.owned_option,'claim':'Use mine','source':1,'target':'Jekyll'}
            rec=route_action(action,actor,actors,memory,c,6,True)
            self.assertFalse(rec['applied']);self.assertEqual(memory.notes,[])
            self.assertFalse(route_action(action,actor,actors,memory,c,6,False)['applied'])
            action.update(kind='edit');rec=route_action(action,actor,actors,memory,c,6,False)
            self.assertTrue(rec['applied']);self.assertEqual(memory.state[actor.slot],actor.owned_option)
        actors=actors_for('mechanism',0,'C-off');memory=WorkingMemory();action.update(kind='peer',target=actors[1].alias)
        route_action(action,actors[0],actors,memory,'C-off',6,True)
        self.assertEqual(actors[1].inbox,[]);self.assertEqual(memory.notes,[])

    def test_packing_masks_orphans_and_resume_prefix(self):
        lengths=iter([('a',2,2),('b',2,2),('c',2,2)])
        rows,steps=replay(lengths,2,6)
        self.assertEqual([s['supervised_tokens'] for s in steps],[2,2])
        self.assertEqual(rows['b']['orphaned_target_tokens_masked'],2)
        self.assertEqual(rows['b']['unmasked_target_tokens'],0)
        self.assertEqual(rows['a']['unmasked_target_tokens'],2);self.assertEqual(rows['c']['unmasked_target_tokens'],2)
        rows,steps=replay(iter([('a',2,2),('b',2,2),('c',2,2)]),2,6,1)
        self.assertEqual(rows['a']['unmasked_target_tokens'],0);self.assertEqual(rows['c']['unmasked_target_tokens'],2)
        self.assertEqual(sum(r['input_tokens_in_resume_replay_only'] for r in rows.values()),6)

    def test_allocation_never_spends_contingency_or_reviews_cap(self):
        timing={'load_seconds':30,'memory_seconds':25,'common_seconds':10,'rollout_seconds':40}
        for project in (50000,340000,343799):
            allocation=choose(timing,100,project)
            self.assertLessEqual(sum(allocation['estimated_seconds'].values()),max(0,min(7100,345600-1800-project)-90))
            if allocation['families']:self.assertIn(allocation['families'],(240,120,64,32))
        self.assertEqual(choose(timing,7200,50000)['stages'],[])

    def test_only_explicit_prompt_enters_backend(self):
        class Model:
            config=RunConfig()
            def generate(self,prompts):
                self.received=prompts;return [{'raw':'{}','parsed':{}} for p in prompts]
        model=Model();prompt=[{'role':'user','content':'Public source'}]
        with tempfile.TemporaryDirectory() as tmp:
            generate_records(model,[{'prompt':prompt,'target':'PRIVATE','saved_answer':'GOLD'}],Path(tmp)/'x.jsonl')
        self.assertEqual(model.received,[prompt])

    def test_rollout_private_truth_never_enters_actor_history(self):
        class Model:
            config=RunConfig(batch_size=2)
            def generate(self,prompts,*args,**kwargs):
                result=[]
                for p in prompts:
                    body=json.loads(p[-1]['content']);text=json.dumps(p)
                    self_test.assertNotIn('evaluator_target',text);self_test.assertNotIn('following_success',text);self_test.assertNotIn('contradictory_edit_with_source_access',text)
                    if kwargs.get('frozen'):
                        parsed={'kind':'recollect','slot':0,'value':'Harbor','claim':'I remember Harbor','source':1,'target':None}
                    else:parsed={'state':['Harbor','onsite','3000','Tuesday','students','Cedar'],'plan':[],'evidence':[1]*6,'clarify':[]}
                    result.append({'raw':json.dumps(parsed),'parsed':parsed,'input_tokens':1,'output_tokens':1})
                return result
        self_test=self
        with tempfile.TemporaryDirectory() as tmp:
            rows=run_rollout(Model(),list(family('mechanism',0,32)),'B1',Path(tmp)/'x.jsonl')
            self.assertEqual(len(rows),2)
            actions=[json.loads(x) for x in (Path(tmp)/'x_characters.jsonl').read_text().splitlines()]
            self.assertEqual(len(actions),24);self.assertTrue(any('evaluator_target' in a for a in actions))

    def test_hidden_truth_change_cannot_change_policy_inputs(self):
        from dataclasses import replace
        class Recorder:
            config=RunConfig(batch_size=2)
            def __init__(self):self.prompts=[]
            def generate(self,prompts,*args,**kwargs):
                self.prompts.extend(copy.deepcopy(prompts))
                parsed={'kind':'pass','slot':0,'value':'Harbor','claim':'','source':1,'target':None} if kwargs.get('frozen') else {'state':['Harbor','onsite','3000','Tuesday','students','Cedar'],'plan':[],'evidence':[1]*6,'clarify':[]}
                return [{'raw':json.dumps(parsed),'parsed':copy.deepcopy(parsed),'input_tokens':1,'output_tokens':1} for p in prompts]
        originals=list(family('mechanism',1,32))
        altered=[replace(s,events=tuple(Event('filler') for _ in s.events)) for s in originals]
        first=Recorder();second=Recorder()
        with tempfile.TemporaryDirectory() as tmp:
            run_rollout(first,originals,'B1',Path(tmp)/'first.jsonl')
            run_rollout(second,altered,'B1',Path(tmp)/'second.jsonl')
        self.assertEqual(first.prompts,second.prompts)

    def test_packet_preserves_ratings_and_refuses_changed_items(self):
        from unittest.mock import patch
        from . import packets
        action={'family_id':'fixture','world':'authorized','turn':2,'actor':'Robin','kind':'edit','slot':0,'value':'Harbor','claim':'A fixture claim','source':1,'target':None,'applied':True,
                'prompt':[{'role':'user','content':json.dumps({'sources':[],'inbox':[],'memory':{}})}]}
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(packets,'ROOT',Path(tmp)),patch.object(packets,'ARTIFACTS',Path(tmp)),patch.object(packets,'RESULTS',Path(tmp)/'results'):
                packets.build('fixture',{'B0':[action]},{});form=Path(tmp)/'human_review/fixture/rater_1.csv'
                form.write_text('existing independent human annotation')
                packets.build('fixture',{'B0':[action]},{});self.assertEqual(form.read_text(),'existing independent human annotation')
                action['claim']='Changed content'
                with self.assertRaises(ValueError):packets.build('fixture',{'B0':[action]},{} )

    def test_family_statistics_reject_incomplete_worlds(self):
        with self.assertRaises(ValueError):pairs([{'family_id':'x','world':'authorized','success':True}])
        c=contrast({'x':1,'y':0},{'x':0,'y':1},'test');self.assertEqual(c['paired_difference'],0)


if __name__=='__main__':unittest.main()
