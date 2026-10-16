"""Live execution admits actual worker errors and preserves the fixed allowance."""
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from rep_sensitivity.live import run_live
from rep_sensitivity.aux_analysis import summarize


class TokenizerFixture:
    def encode(self,text,**kwargs):return [0]*(len(text)//4)


class LiveFixture:
    accepted=0;root_prompts=[]
    def __init__(self,*args,**kwargs):
        self.batch_size=32;self.settings={'fixture':'unit-test-only'};self.load_seconds=0
        self.tokenizer=TokenizerFixture()
    def prepare(self,prompt):return prompt
    def run(self,requests):
        outputs=[]
        for r in requests:
            assert 'oracle_choice' not in r['prompt']
            root=r['stage']=='root';assertions=[]
            if root:self.root_prompts.append(r['prompt'])
            else:
                payload=json.loads(r['prompt'].split('\n')[-1])
                key=next(iter(payload['access']['registry']))
                assertions=[{'key':key,'value':-1 if payload['assignment']['family']=='objective' else False,
                             'reports':[payload['assignment']['source_identifier']]}]
            text=json.dumps({'assertions':assertions,'unresolved':[],'candidate_assessments':[],
                             'choice':'INSUFFICIENT' if root else None,'probabilities':{}})
            if LiveFixture.accepted==0:text='malformed completed worker response'
            LiveFixture.accepted+=1
            outputs.append({'text':text,'finish_reason':'stop','input_tokens':len(r['prompt'])//4,
                            'output_tokens':len(text)//4,'batch_wall_seconds':0.1,
                            'allocated_inference_seconds':0.1/len(requests)})
        return outputs


class LiveExecutionTests(unittest.TestCase):
    def test_worker_errors_delivery_budget_and_resume(self):
        config=json.loads((Path(__file__).resolve().parents[1]/'configs/live-provisional.json').read_text())
        config.update(name='live-fixture',status='development_live',generated_pairs=1,models=['fixture'],worker_interface_version=2)
        LiveFixture.accepted=0;LiveFixture.root_prompts=[];previous=Path.cwd()
        try:
            with tempfile.TemporaryDirectory() as d:
                os.chdir(d)
                with patch('rep_sensitivity.models.LocalModel',LiveFixture),redirect_stdout(io.StringIO()):
                    run_live(config,'fixture');count=LiveFixture.accepted
                    run_live(config,'fixture')
                self.assertEqual(count,66);self.assertEqual(LiveFixture.accepted,count)
                rows=[json.loads(p.read_text()) for p in Path('artifacts/runs/live-fixture/fixture/scores').glob('*.json')]
                self.assertEqual(len(rows),10)
                self.assertTrue(any(r['operational_failure'] for r in rows))
                self.assertTrue(all(r['assignment_coverage']['covered_assignments']==12 for r in rows))
                self.assertTrue(all(r['worker_incorrect_claims']>0 for r in rows))
                self.assertTrue(any('-1 time_units' in prompt for prompt in LiveFixture.root_prompts))
                for r in rows:
                    if r['allowance']=='fixed':
                        self.assertLessEqual(r['allocated_total_worker_token_allowance'],r['baseline_total_worker_token_allowance'])
                        self.assertLessEqual(r['closed_worker_tokens_plus_root_allowance'],r['baseline_total_trajectory_token_allowance'])
                        self.assertLessEqual(r['input_tokens']+r['output_tokens'],r['baseline_total_trajectory_token_allowance'])
                result=summarize('artifacts/runs/live-fixture','analysis',replicates=100)
                self.assertEqual(result['analyzed_trajectories'],10)
                self.assertFalse(result['excluded_incomplete_clusters'])
        finally:os.chdir(previous)
