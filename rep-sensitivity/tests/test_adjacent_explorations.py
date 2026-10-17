import gzip
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from rep_sensitivity.adjacent_explorations import (
    build_cases, inventory, feedback_prompt, consensus_prompt, length_control, run)
from rep_sensitivity.adjacent_analysis import analyze, transitions, cluster_estimate
from rep_sensitivity.generation import generate_pair
from rep_sensitivity.schema import canonical, digest
from scripts.run_adjacent_explorations import choose_allocation
from scripts.visible_information_v2 import visible_state


class AdjacentTests(unittest.TestCase):
    def fixture(self, path):
        source=Path(path)/'source';source.mkdir()
        config=json.loads(Path('configs/adjacent-explorations-v1.json').read_text())
        config.update(source_run=str(source),status='frozen')
        pairs=[generate_pair('development',i,2) for i in config['pair_indices']]
        (source/'pairs.json').write_text(json.dumps(pairs));(source/'manifest.json').write_text('{"fixture":true}')
        cases=build_cases(config);config['input_inventory_sha256']=digest(inventory(config,cases))
        return config,cases

    def test_matched_updates_and_complete_visible_evidence(self):
        with tempfile.TemporaryDirectory() as path:
            config,cases=self.fixture(path);target_status=[];numerical_directions=[]
            for c in cases:
                self.assertNotEqual(c['truth']['initial']['answer'],c['truth']['consequential']['answer'])
                self.assertEqual(c['truth']['initial']['answer'],c['truth']['harmless']['answer'])
                for state,reports in c['reports'].items():
                    obj={'assertions':[[r.claim.key,r.claim.asserted_value,[r.identifier]] for r in reports],'unresolved':[]}
                    v=visible_state(c['worlds'][state],reports,[{'summary':obj}])
                    self.assertEqual(v['justified_answers'],[c['truth'][state]['answer']])
                target_status.extend(c['target_candidate']==c['truth'][s]['answer'] for s in ('initial','consequential'))
                if c['family']=='numeric':numerical_directions.append(c['edits']['consequential'][0]['after']-c['edits']['consequential'][0]['before'])
            self.assertEqual(sum(target_status),4);self.assertEqual(sorted(numerical_directions),[-1,1])

    def test_feedback_is_context_only_and_length_has_no_decision(self):
        with tempfile.TemporaryDirectory() as path:
            _,cases=self.fixture(path);c=cases[0]
            feedback={'previous_round':2,'evidence_version':'1','parse_status':'valid','choice':'C_wrong',
                      'candidate_assessments':[{'candidate':'C_wrong','all_mandatory_pass':True,'objective':1}]}
            baseline=feedback_prompt(c,'consequential',3)
            active=feedback_prompt(c,'consequential',3,feedback)
            neutral,residual=length_control(c,'consequential',3,feedback,list)
            def payload(p):return json.loads(p.split('\nINPUT\n')[1])
            a,b,n=map(payload,(baseline,active,neutral));context=b.pop('context_only_not_current_evidence')
            self.assertEqual(a,b);self.assertEqual(context,feedback)
            neutral_context=n.pop('context_only_not_current_evidence');self.assertEqual(a,n)
            self.assertNotIn('C_wrong',canonical(neutral_context));self.assertLessEqual(abs(residual),1)
            self.assertEqual(a['task_authority']['current_version'],'2')
            self.assertNotIn('oracle',canonical(a))
            r1=payload(feedback_prompt(c,'consequential',1));r2=payload(feedback_prompt(c,'harmless',2))
            self.assertEqual(r1['reports'],r2['reports']);self.assertEqual(r1['scope_registry'],r2['scope_registry'])

    def test_relay_identity_cues_do_not_change_claims_or_ancestry(self):
        with tempfile.TemporaryDirectory() as path:
            config,cases=self.fixture(path)
            for c in cases:
                for w in (0,1):
                    stripped=[];source_sets=[]
                    for arm in config['consensus_arms']:
                        prompt,reports=consensus_prompt(c,w,arm);payload=json.loads(prompt.split('\nINPUT\n')[1])
                        shown=[r for r in payload['reports'] if 'presentation' in r]
                        self.assertEqual(len(shown),1 if arm=='single' else 4)
                        self.assertEqual(len({r['presentation']['origin_report'] for r in shown}),1)
                        self.assertEqual(len({r['execution'] for r in shown}),1)
                        self.assertEqual(len({r['presentation']['displayed_agent'] for r in shown}),1 if arm in ('single','same_worker') else 4)
                        self.assertTrue(all(not r['presentation']['independent_reverification'] for r in shown))
                        source_sets.append({(r.claim.key,canonical(r.claim.asserted_value)) for r in reports})
                        for r in shown:r.pop('presentation')
                        if arm!='single':stripped.append(payload)
                    self.assertTrue(all(v==source_sets[0] for v in source_sets));self.assertEqual(stripped[0],stripped[1]);self.assertEqual(stripped[1],stripped[2])

    def test_restart_preserves_accepted_round_and_malformed_answer(self):
        class Model:
            alias='qwen3';batch_size=32;load_seconds=0;settings={'max_output_tokens':2304}
            def __init__(self):self.total=0;self.failed=False
            token_ids=staticmethod(list)
            def run(self,requests):
                if self.total==24 and not self.failed:self.failed=True;raise RuntimeError('fixture interruption')
                out=[]
                for r in requests:
                    text='malformed' if self.total==0 else canonical({'assertions':[],'unresolved':[],'candidate_assessments':[],
                        'choice':'NONE','probabilities':{}})
                    self.total+=1
                    out.append({'text':text,'finish_reason':'stop','input_tokens':10,'output_tokens':3,
                                'allocated_inference_seconds':.01,'batch_wall_seconds':.01*len(requests)})
                return out
        model=Model()
        with tempfile.TemporaryDirectory() as path,patch('rep_sensitivity.models.reuse_or_load',return_value=(model,False)):
            config,cases=self.fixture(path);root=Path(path)/'runs'
            with self.assertRaises(RuntimeError):run(config,root=root)
            self.assertEqual(model.total,24)
            run(config,root=root);self.assertEqual(model.total,104)
            run(config,root=root);self.assertEqual(model.total,104)
            calls=[json.loads(gzip.decompress(p.read_bytes())) for p in (root/config['name']/'qwen3/calls').glob('*.json.gz')]
            self.assertEqual(len(calls),104);self.assertEqual(sum(c['response']['text']=='malformed' for c in calls),1)
            for call in calls:
                t=call['trial'];payload=json.loads(call['prompt'].split('\nINPUT\n')[1])
                if t['experiment']=='feedback' and t['arm']=='fresh':self.assertNotIn('context_only_not_current_evidence',payload)
                if t['experiment']=='feedback' and t['round']>1 and t['arm']=='length_control':
                    self.assertNotIn('choice',payload['context_only_not_current_evidence'])
            result=analyze(root/config['name'],Path(path)/'results')
            self.assertTrue(result['complete']);self.assertEqual(result['experiments']['feedback']['calls'],72)
            self.assertEqual(result['experiments']['consensus']['calls'],32)

    def test_transitions_do_not_call_wrong_persistence_robustness(self):
        rows=[{'round':1,'choice':'A','oracle_choice':'B','correct':False,'operational_failure':False},
              {'round':2,'choice':'A','oracle_choice':'B','correct':False,'operational_failure':False},
              {'round':3,'choice':'A','oracle_choice':'A','correct':True,'operational_failure':False}]
        t=transitions(rows);self.assertTrue(t['initial_wrong_choice_persists_and_still_wrong_round_2'])
        self.assertFalse(t['initial_wrong_choice_persists_and_still_wrong_round_3'])
        self.assertFalse(t['correct_update_response_or_stability'])
        self.assertTrue(t['2_to_3']['incorrect_to_correct']);self.assertFalse(t['2_to_3']['answer_changed'])
        rows[2].update(choice=None,correct=False,operational_failure=True)
        failed=transitions(rows)
        self.assertIsNone(failed['initial_wrong_choice_persists_and_still_wrong_round_3'])
        self.assertFalse(failed['2_to_3']['incorrect_to_correct'])
        self.assertIsNone(failed['2_to_3']['answer_changed'])
        known=cluster_estimate({'a':1,'b':0,'c':0,'d':-1});self.assertEqual(known['base_pairs'],4);self.assertEqual(known['estimate'],0)

    def test_budget_fallback_is_prospective_and_keeps_shared_margin(self):
        config={'maximum_gpu_wall_seconds':900,'allocation_rule':{'priority':['both','feedback_only'],'margin_seconds':60,
            'projections':{'both':{'prospectively_feasible':True,'minimum_remaining_seconds':820},
                           'feedback_only':{'prospectively_feasible':True,'minimum_remaining_seconds':653}}}}
        self.assertEqual(choose_allocation(config,1000),('both',900))
        self.assertEqual(choose_allocation(config,800),('feedback_only',740))
        self.assertEqual(choose_allocation(config,700),(None,0))


if __name__=='__main__':unittest.main()
