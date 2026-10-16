import json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from rep_sensitivity.objective_confirmation import prepare,plan_pair,run
from rep_sensitivity.generation import generate_pair
from rep_sensitivity.controls import semantic_inventory
from rep_sensitivity.schema import canonical
from scripts.check_fresh_pair_separation import structure,select,flatten,distance
from scripts.analyze_objective_confirmation import analyze

class ObjectiveConfirmationTests(unittest.TestCase):
    def config(self):
        c=json.loads(Path('configs/objective-confirmation-v1.json').read_text())
        c.update(status='frozen',models=['qwen3'],pair_indices=c['pair_indices'][:1],pair_ids=c['pair_ids'][:1])
        return c

    def test_selective_and_balanced_preserve_scope_coverage_and_ancestry(self):
        c=self.config();pair=generate_pair('heldout',c['pair_indices'][0],2)
        jobs=plan_pair(pair,c,'qwen3');baseline=next(j for j in jobs if j['trial']['arm']=='single' and j['trial']['world']==0)
        for j in jobs:
            if j['trial']['world']!=0:continue
            self.assertEqual(semantic_inventory(j['reports']),semantic_inventory(baseline['reports']))
            originals={r.identifier:r for r in j['required']}
            copies=[r for r in j['reports'] if r.identifier not in originals]
            expected=0 if j['trial']['arm']=='single' else 9 if j['trial']['arm'].startswith('balanced') else 3
            self.assertEqual(len(copies),expected)
            for r in copies:
                parent=originals[r.parent_report_identifiers[0]]
                self.assertEqual(r.claim,parent.claim)
                if j['trial']['arm'].endswith('paraphrase'):self.assertNotEqual(r.text,parent.text)
                else:self.assertEqual(r.text,parent.text)
        self.assertEqual(len({j['audit']['target_candidate'] for j in jobs}),1)

    def test_fresh_pairs_and_repetition_cache_coordinates(self):
        selection=select();self.assertEqual(len(selection['selected']),24)
        self.assertTrue(all(p['minimum_prior_field_distance']>=3 for p in selection['selected']))
        c=self.config();pair=generate_pair('heldout',c['pair_indices'][0],2);c['stochastic_repetitions']=2
        jobs=plan_pair(pair,c,'qwen3')
        self.assertEqual(len({j['trial']['trial_id'] for j in jobs}),20)
        phi=plan_pair(pair,c,'phi4')
        self.assertFalse({j['trial']['trial_id'] for j in jobs}&{j['trial']['trial_id'] for j in phi})

    def test_resume_keeps_accepted_malformed_answers_without_resampling(self):
        c=self.config()
        analysis_spec=json.loads(Path(c['analysis']).read_text());c['analysis']='analysis.json'
        class Model:
            alias='qwen3';batch_size=32;load_seconds=0;settings={'max_output_tokens':2304}
            def __init__(self):self.calls=0
            def run(self,requests):
                self.calls+=len(requests)
                return [{'text':'malformed completed answer','finish_reason':'stop','input_tokens':10,'output_tokens':3,
                         'allocated_inference_seconds':0.01,'batch_wall_seconds':0.01*len(requests)} for r in requests]
        model=Model();old=Path.cwd()
        with tempfile.TemporaryDirectory() as directory:
            try:
                os.chdir(directory);Path('analysis.json').write_text(json.dumps(analysis_spec))
                with patch('rep_sensitivity.objective_confirmation.reuse_or_load',return_value=(model,True)):
                    self.assertTrue(run(c,'qwen3',100));n=model.calls
                    score=next(Path('artifacts/runs',c['name'],'qwen3','scores').glob('*.json'))
                    before=score.read_bytes();rows=json.loads(before)
                    self.assertEqual(len(rows),10);self.assertTrue(all(r['operational_failure'] for r in rows))
                    self.assertTrue(run(c,'qwen3',100));self.assertEqual(model.calls,n);self.assertEqual(score.read_bytes(),before)
                    result=analyze('artifacts/runs/'+c['name'],'results/fixture')
                    self.assertTrue(result['complete']);record=result['model_results'][0]
                    self.assertEqual(record['physical_calls'],n);self.assertEqual(record['logical_calls'],30)
                    self.assertTrue(all(x['estimate']==0 and x['clusters']==1 for x in record['contrasts']))
            finally:os.chdir(old)

if __name__=='__main__':unittest.main()
