"""End-to-end replay checkpoints and raw-output analysis without model inference."""
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from rep_sensitivity.replay import run
from rep_sensitivity.analysis import load_complete


class ReplayFixture:
    accepted=0
    def __init__(self,*args,**kwargs):
        self.batch_size=8;self.settings={'fixture':'unit-test-only'};self.load_seconds=0
    def run(self,requests):
        out=[]
        for r in requests:
            for forbidden in ('oracle_choice','decision_changed','affected_predicates'):
                assert forbidden not in r['prompt']
            manager=r['stage']!='root'
            text=json.dumps({'assertions':[],'unresolved':[],'candidate_assessments':[],
                             'choice':None if manager else 'NONE','probabilities':{}})
            if manager and ReplayFixture.accepted==2:text='malformed completed output'
            ReplayFixture.accepted+=1
            out.append({'text':text,'finish_reason':'stop','input_tokens':100,'output_tokens':30,
                        'batch_wall_seconds':0.1,'allocated_inference_seconds':0.1/len(requests)})
        return out


class ReplayExecutionTests(unittest.TestCase):
    def test_replay_complete_clusters_and_immutable_resume(self):
        config={'name':'replay-fixture','interface_version':7,'benchmark_version':2,'split':'development','base_pairs':1,
                'models':['fixture'],'worlds':[0,1],'repetition_conditions':['single','exact','paraphrase'],
                'organizations':['flat','hierarchical'],'policies':['ordinary','checklist'],
                'stochastic_repetitions':1,'max_context_tokens':12288,'max_output_tokens':2304,
                'temperature':0.3,'top_p':0.95,'batch_size':8}
        ReplayFixture.accepted=0;previous=Path.cwd()
        try:
            with tempfile.TemporaryDirectory() as d:
                os.chdir(d)
                with patch('rep_sensitivity.models.LocalModel',ReplayFixture),redirect_stdout(io.StringIO()):
                    run(config,'fixture')
                    count=ReplayFixture.accepted
                    run(config,'fixture')
                self.assertEqual(count,48);self.assertEqual(ReplayFixture.accepted,count)
                manifest,rows,incomplete=load_complete('artifacts/runs/replay-fixture')
                self.assertEqual(len(rows),24);self.assertFalse(incomplete)
                self.assertTrue(any(r['operational_failure'] for r in rows))
                self.assertEqual(sum(r['calls'] for r in rows),manifest['manager_calls'])
                self.assertTrue(all(r['required_claims']==18 for r in rows))
                self.assertTrue(all(r['retained_count']==0 for r in rows))
        finally:os.chdir(previous)
