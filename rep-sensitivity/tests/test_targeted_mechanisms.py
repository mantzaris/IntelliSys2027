"""Scientific checks for target selection, lossless transport and shared controls."""
from collections import Counter
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import unittest
import os
import tempfile
from unittest.mock import patch
from rep_sensitivity.generation import generate_pair
from rep_sensitivity.reports import make_reports
from rep_sensitivity.controls import semantic_inventory,decision_from_claims
from rep_sensitivity.mechanism import critical_keys,necessary_keys,transport_metrics,injected_value_metrics
from rep_sensitivity.metrics import parse
from rep_sensitivity.schema import canonical
from rep_sensitivity.targeted_design import targets,repeat_selected,uniform_repeat,plan_pair,source_pairs
from rep_sensitivity.targeted_replay import lossless_summary,shared_manager_requests
from rep_sensitivity.targeted_analysis import cluster_values,clustered_interval,contrast_rows

CONFIG=json.loads((Path(__file__).resolve().parents[1]/'configs/mechanism-development-v1.json').read_text())


class TargetedMechanismTests(unittest.TestCase):
    def test_relevance_changes_choice_and_never_loses_coverage(self):
        for pair in source_pairs(CONFIG):
            for world in pair['worlds']:
                rs=make_reports(world,'development',pair['seed']);ts=targets(world,rs,pair['seed'])
                self.assertIn(ts['A'].claim.key,critical_keys(world,rs))
                if ts['B']:self.assertNotIn(ts['B'].claim.key,critical_keys(world,rs))
                for target in [r for r in ts.values() if r]:
                    repeated=repeat_selected(rs,target,16)
                    self.assertEqual(semantic_inventory(rs),semantic_inventory(repeated))
                    self.assertEqual(len(repeated),len(rs)+15)
                    self.assertEqual({r.claim.verification_execution_identifier for r in rs},{r.claim.verification_execution_identifier for r in repeated})
                uniform=uniform_repeat(rs,4,'development')
                self.assertEqual(Counter(r.claim.key for r in uniform),Counter({r.claim.key:4 for r in rs}))

    def test_false_repetition_targets_false_report_not_true_same_scope(self):
        jobs,_=plan_pair(generate_pair('development',0,2),CONFIG)
        single=next(j for j in jobs if j['trial']['arm']=='false_visible1')
        repeated=next(j for j in jobs if j['trial']['arm']=='false_visible4')
        key=repeated['injected_key'];true=repeated['true_value']
        self.assertEqual(sum(r.claim.key==key and r.claim.asserted_value is not true for r in single['reports']),1)
        self.assertEqual(sum(r.claim.key==key and r.claim.asserted_value is not true for r in repeated['reports']),4)
        self.assertTrue(any(r.claim.key==key and r.claim.asserted_value is true for r in repeated['reports']))
        self.assertEqual(single['extra_evidence'],repeated['extra_evidence'])
        self.assertFalse(any('injected' in r.identifier for r in repeated['reports']))

    def test_near_renderings_hold_information_and_slots_fixed(self):
        for index in CONFIG['targeted_subset_indices']:
            jobs,_=plan_pair(generate_pair('development',index,2),CONFIG)
            by_arm={j['trial']['arm']:j for j in jobs if j['trial']['world']==0}
            for importance in ('decisive','harmless'):
                for dose in (1,4):
                    a=by_arm['near_'+importance+'_high'+str(dose)]['reports']
                    b=by_arm['near_'+importance+'_low'+str(dose)]['reports']
                    self.assertEqual(semantic_inventory(a),semantic_inventory(b))
                    self.assertEqual([r.identifier for r in a],[r.identifier for r in b])
            for dose in (1,4):
                a=by_arm['numeric_high'+str(dose)];b=by_arm['numeric_low'+str(dose)]
                self.assertEqual(semantic_inventory(a['reports']),semantic_inventory(b['reports']))
                self.assertEqual(a['extra_evidence'],b['extra_evidence'])
                key=a['audit']['false_numeric_key'];value=a['audit']['true_numeric_value']
                self.assertEqual(sum(r.claim.key==key and r.claim.asserted_value==value+1 for r in a['reports']),dose)
                self.assertEqual(sum(r.claim.key==key and r.claim.asserted_value==value for r in a['reports']),1)

    def test_objective_loss_and_post_transport_error_are_distinct(self):
        pair=generate_pair('development',6,2);world=pair['worlds'][0];rs=make_reports(world,'development',pair['seed'])
        obj,_=parse(canonical(lossless_summary(rs)),world['tie_order'],manager=True)
        full=transport_metrics(world,rs,[obj],False)
        self.assertEqual(full['necessary_retention'],1)
        self.assertTrue(full['root_error_despite_sufficient_visible_truth'])
        missing=deepcopy(obj);missing['assertions']=[a for a in missing['assertions'] if '/objective/' not in a[0]]
        scored=transport_metrics(world,rs,[missing],False)
        self.assertEqual(scored['critical_retention'],1)
        self.assertLess(scored['necessary_retention'],1)
        self.assertFalse(scored['visible_truth_sufficient'])
        # Diagnostic transport preserves an injected false value; it never fixes it.
        false=replace(rs[0],claim=replace(rs[0].claim,asserted_value=False))
        self.assertFalse(lossless_summary([false])['assertions'][0]['value'])

    def test_identical_manager_pairing_never_collapses_repetitions(self):
        requests=[]
        for rep in (0,1):
            for arm in ('baseline','bypass','repeat'):
                t={'pair_id':'base','world':0,'repetition':rep,'trial_id':arm+str(rep)}
                requests.append({'trial':t,'stage':'manager0','prompt':'unchanged input'})
        unique,mapping=shared_manager_requests(requests)
        self.assertEqual(len(unique),2)
        self.assertEqual(mapping[('bypass0','manager0')],mapping[('baseline0','manager0')])
        self.assertNotEqual(mapping[('baseline0','manager0')],mapping[('baseline1','manager0')])

    def test_effect_sign_and_cluster_units(self):
        rows=[]
        for pid in ('a','b'):
            for world in (0,1):
                for rep in (0,1):
                    for arm in ('hier_F','hier_A4'):
                        rows.append({'pair_id':pid,'world':world,'repetition':rep,'arm':arm,'aliases':[],
                                     'correct':arm=='hier_A4'})
        values,n=cluster_values(rows,{'hier_A4':1,'hier_F':-1},'correct')
        self.assertEqual(values,{'a':1.0,'b':1.0});self.assertEqual(n,8)
        uncertain=clustered_interval(values,{'a':('one',True),'b':('two',True)},100)
        self.assertFalse(uncertain['interval_available']);self.assertIsNone(uncertain['lower'])

    def test_numeric_corruption_is_not_scored_as_boolean_negation(self):
        obj={'assertions':[['scope',9,[]]],'unresolved':[]}
        self.assertTrue(injected_value_metrics(obj,'scope',8,9)['false_assertion_adopted'])
        obj['assertions'].append(['scope',8,[]])
        self.assertTrue(injected_value_metrics(obj,'scope',8,9)['false_assertion_emitted'])
        self.assertFalse(injected_value_metrics(obj,'scope',8,9)['false_assertion_adopted'])
        obj={'assertions':[['scope',True,[]]],'unresolved':[]}
        self.assertFalse(injected_value_metrics(obj,'scope',0,1)['false_assertion_emitted'])

    def test_four_dose_uses_same_world_and_base_subset_as_other_doses(self):
        rows=[]
        for pid in ('subset','outside'):
            for world in (0,1):
                arms=['hier_F','hier_B4']+(['dose2'] if pid=='subset' and world==0 else [])
                for arm in arms:rows.append({'pair_id':pid,'world':world,'repetition':0,'arm':arm,
                    'aliases':['hier_common4'] if arm=='hier_B4' else [],'correct':arm!='hier_F'})
        selected=contrast_rows(rows,'dose_4')
        values,n=cluster_values(selected,{'hier_common4':1,'hier_F':-1},'correct')
        self.assertEqual(values,{'subset':1.0});self.assertEqual(n,1)
        self.assertEqual(contrast_rows(rows,'P2'),rows)

    def test_future_instances_are_disjoint(self):
        old={generate_pair('heldout',i,2)['pair_id'] for i in range(192)}
        future={generate_pair('heldout',i,2)['pair_id'] for i in range(384,432)}
        self.assertFalse(old&future)

    def test_new_future_designs_preserve_eligible_core_comparisons(self):
        for split,start,n in [('validation',36,24),('heldout',384,48)]:
            config={**CONFIG,'split':split,'pair_start':start,'base_pairs':n,'phase':split,'targeted_subset_indices':[]}
            for pair in source_pairs(config):
                jobs,excluded=plan_pair(pair,config)
                self.assertFalse(excluded)
                for wi in (0,1):
                    arms={j['trial']['arm'] for j in jobs if j['trial']['world']==wi}
                    self.assertTrue({'hier_F','hier_A4','hier_COMMON4','hier_E4','bypass_F','bypass_common4'}<=arms)

    def test_targeted_resume_keeps_completed_malformed_outputs(self):
        from rep_sensitivity.targeted_replay import run
        from rep_sensitivity.targeted_analysis import summarize
        class Model:
            alias='qwen3';settings={'max_output_tokens':2304};load_seconds=0;batch_size=32;calls=0
            def run(self,requests):
                self.calls+=len(requests)
                return [{'text':'MALFORMED','finish_reason':'stop','input_tokens':20,'output_tokens':3,
                         'batch_wall_seconds':.1,'allocated_inference_seconds':.1/len(requests)} for r in requests]
        config={**CONFIG,'name':'test-targeted','base_pairs':1,'targeted_subset_indices':[],
                'phase':'heldout','status':'frozen'}
        old=os.getcwd()
        with tempfile.TemporaryDirectory() as directory:
            try:
                os.chdir(directory);model=Model()
                with patch('rep_sensitivity.targeted_replay.reuse_or_load',return_value=(model,False)):
                    run(config,model);first=model.calls
                    # Force score reconstruction from immutable accepted responses,
                    # including malformed completions, as after a scoring crash.
                    scores=next(Path('artifacts/runs/test-targeted/qwen3/scores').glob('*.json'))
                    expected=scores.read_bytes();scores.unlink()
                    run(config,model)
                    self.assertEqual(model.calls,first);self.assertEqual(scores.read_bytes(),expected)
                    run(config,model);self.assertEqual(model.calls,first)
                result=summarize('artifacts/runs/test-targeted','results/test',100)
                self.assertTrue(result['complete'])
                self.assertEqual(result['physical_resource_inventory']['unscored_accepted_calls'],0)
                self.assertLess(first,result['physical_resource_inventory']['logical_graph_calls'])
                self.assertTrue(all(r['accuracy']==0 for r in result['summary']))
            finally:os.chdir(old)

    def test_fresh_executions_keep_false_initial_report_and_respect_total_budget(self):
        from rep_sensitivity.fresh_probe import run
        from rep_sensitivity.fresh_analysis import summarize
        from rep_sensitivity.generation import oracle
        pair=generate_pair('development',0,2);world=pair['worlds'][0]
        truth={r.claim.key:r.claim.asserted_value for r in make_reports(world,'development',pair['seed'])}
        answer=oracle(world)['answer']
        class Model:
            alias='qwen3';settings={'max_output_tokens':2304};load_seconds=0;batch_size=32;calls=0
            def token_ids(self,prompt):return [0]*(len(prompt)//8)
            def run(self,requests):
                out=[];self.calls+=len(requests)
                for r in requests:
                    if r['stage'].startswith('worker'):
                        payload=json.loads(r['prompt'].split('\n')[-1]);key=next(iter(payload['access']['scope_registry']))
                        value=not truth[key] if r['stage']=='worker0' else truth[key]
                        obj={'assertions':[{'key':key,'value':value,'reports':[]}],'unresolved':[],
                             'candidate_assessments':[],'choice':None,'probabilities':{}}
                    else:obj={'assertions':[],'unresolved':[],'candidate_assessments':[],
                              'choice':answer,'probabilities':{}}
                    text=canonical(obj)
                    out.append({'text':text,'finish_reason':'stop','input_tokens':len(self.token_ids(r['prompt'])),
                        'output_tokens':len(text)//8,'batch_wall_seconds':.1,'allocated_inference_seconds':.1/len(requests)})
                return out
        config=json.loads((Path(__file__).resolve().parents[1]/'configs/fresh-probe-v1.json').read_text())
        config.update(name='test-fresh',status='frozen',pair_indices=[0])
        old=os.getcwd()
        with tempfile.TemporaryDirectory() as directory:
            try:
                os.chdir(directory);model=Model()
                with patch('rep_sensitivity.fresh_probe.reuse_or_load',return_value=(model,False)):
                    run(config,model);first=model.calls
                    path=next(Path('artifacts/runs/test-fresh/qwen3/scores').glob('*.json'))
                    expected=path.read_bytes();path.unlink();run(config,model)
                    self.assertEqual(model.calls,first);self.assertEqual(path.read_bytes(),expected)
                rows={r['arm']:r for r in json.loads(expected)}
                self.assertFalse(rows['original']['initial_worker']['correct'])
                self.assertEqual(rows['copies']['initial_worker'],rows['original']['initial_worker'])
                self.assertTrue(rows['fresh_added']['fresh_correct_after_initial_error'])
                self.assertLessEqual(rows['fresh_fixed']['total_tokens'],rows['original']['baseline_trajectory_token_allowance'])
                result=summarize('artifacts/runs/test-fresh','results/test',100)
                self.assertTrue(result['complete']);self.assertEqual(first,12)
                self.assertFalse(any(r['interval_available'] for r in result['contrasts']))
            finally:os.chdir(old)
