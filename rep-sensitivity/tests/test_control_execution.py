"""Exercise complete control admission, scoring and resume without a GPU."""
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from rep_sensitivity.replay import prepare
from rep_sensitivity.supporting import run_controls
from rep_sensitivity.aux_analysis import summarize


class TokenizerFixture:
    def encode(self,text,**kwargs):return list(text.encode())
    def decode(self,tokens):return bytes(tokens).decode(errors='replace')


class ModelFixture:
    accepted=0
    prompts=[]
    def __init__(self,*args,**kwargs):
        self.tokenizer=TokenizerFixture();self.batch_size=32
        self.settings={'fixture':'unit-test-only'}
    def prepare(self,prompt):return prompt
    def run(self,requests):
        out=[]
        for r in requests:
            self.prompts.append(r['prompt'])
            text=json.dumps({'assertions':[],'unresolved':[],'candidate_assessments':[],
                             'choice':'INSUFFICIENT' if r['stage']=='root' else None,'probabilities':{}})
            if ModelFixture.accepted==0:text='completed but malformed'
            ModelFixture.accepted+=1
            out.append({'text':text,'finish_reason':'stop','input_tokens':len(r['prompt']),
                        'output_tokens':len(text),'batch_wall_seconds':0.1,
                        'allocated_inference_seconds':0.1/len(requests)})
        return out


class ControlExecutionTests(unittest.TestCase):
    def test_controls_keep_failures_and_resume_complete_calls(self):
        root=Path(__file__).resolve().parents[1]
        config=json.loads((root/'configs/supporting-provisional.json').read_text())
        config.update(name='control-fixture',status='development_controls',source_corpus='source',
                      pair_indices=[0,5],stochastic_repetitions=1)
        source={'name':'source','split':'development','base_pairs':6,'benchmark_version':2,
                'models':['fixture'],'worlds':[0,1],'repetition_conditions':['single'],
                'organizations':['flat'],'policies':['ordinary'],'stochastic_repetitions':1}
        ModelFixture.accepted=0;ModelFixture.prompts=[]
        previous=Path.cwd()
        try:
            with tempfile.TemporaryDirectory() as d:
                os.chdir(d)
                prepare(source,'source')
                with patch('rep_sensitivity.supporting.LocalModel',ModelFixture),redirect_stdout(io.StringIO()):
                    run_controls(config,'fixture')
                    count=ModelFixture.accepted
                    run_controls(config,'fixture')
                self.assertEqual(ModelFixture.accepted,count)
                directory=Path('artifacts/runs/control-fixture/fixture')
                rows=[json.loads(p.read_text()) for p in (directory/'scores').glob('*.json')]
                planned=sum(json.loads(p.read_text())['trajectories'] for p in (directory/'manifests').glob('*.json'))
                self.assertEqual(len(rows),planned)
                self.assertTrue(any(r['operational_failure'] for r in rows))
                self.assertTrue(any(r['contrast']=='unique_clause' for r in rows))
                self.assertTrue(any(r['contrast']=='version_admission' for r in rows))
                for prompt in ModelFixture.prompts:
                    for secret in ('reference_answer','oracle_choice','decision_changed'):
                        self.assertNotIn(secret,prompt)
                result=summarize(directory.parent,'analysis',replicates=100)
                self.assertEqual(result['analyzed_trajectories'],planned)
                self.assertFalse(result['excluded_incomplete_clusters'])
        finally:os.chdir(previous)
