import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from . import results,monitor
from supplements.review_001.exposure import replay


def worlds(family,success,seed=17):
    return [{'family_id':family,'world':world,'success':success,'seed':seed} for world in ('authorized','hypothetical')]


class OvernightTests(unittest.TestCase):
    def test_transition_table_retains_family_pairs(self):
        left=worlds('a',True)+worlds('b',True)+worlds('c',False)+worlds('d',False)
        right=worlds('a',True)+worlds('b',False)+worlds('c',True)+worlds('d',False)
        row,cells=results.transitions(left,right)
        self.assertEqual([row[k] for k in ('both_succeed','only_first','only_second','neither')],[1,1,1,1])
        self.assertEqual(row['difference'],0);self.assertEqual(cells['only_first'],['b'])
        with self.assertRaises(ValueError):results.transitions(left+left[:1],right)
        with self.assertRaises(ValueError):results.transitions(left[:-1],right)
        with self.assertRaises(ValueError):results.transitions(left,worlds('z',True)+right[2:])

    def test_partial_and_excluded_stages_cannot_enter(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for name,status in [('complete','completed'),('partial','running'),('excluded','completed')]:
                p=root/'artifacts/runs'/name;p.mkdir(parents=True);(p/'status.json').write_text(json.dumps({'status':status}))
            queue=[{'command':'evaluate','id':name} for name in ('complete','partial','excluded','missing')]
            with patch.object(results,'ROOT',root),patch.object(results,'verify_freeze',return_value={'plan':{}}),patch.object(results,'load_overrides',return_value={}),patch.object(results,'jobs',return_value=queue),patch.object(results,'resolve_job',side_effect=lambda j,o:j),patch.object(results,'exclusions',return_value={'excluded':'known invalid'}):
                eligible=list(results.eligible_evaluations())
            self.assertEqual([r[0]['id'] for r in eligible],['complete'])

    def test_running_elapsed_not_counted_twice_in_forecast(self):
        queue=[{'id':'done','model':'qwen','command':'fit','horizon':16,'families':150},{'id':'active','model':'qwen','command':'fit','horizon':16,'families':150}]
        records={'done':{'status':'completed','gpu_reserved_seconds':10},'active':{'status':'running','gpu_reserved_seconds':4}}
        with patch.object(monitor,'read',return_value={'jobs':[{'run_id':'done','seconds_forecast':10},{'run_id':'active','seconds_forecast':10}]}),patch.object(monitor,'jobs',return_value=queue),patch.object(monitor,'verify_freeze',return_value={'plan':{}}):
            value=monitor.forecast(queue,records,14)
        self.assertAlmostEqual(value['expected_total_reserved_hours']*3600,20)
        self.assertEqual(value['pending'][0]['expected_remaining_seconds'],6)

    def test_loss_accounting_separates_replay_and_masks(self):
        records,steps=replay(iter([('clean',2,2),('recovery',2,2),('clean',2,2)]),2,6,1)
        self.assertEqual(sum(s['supervised_tokens'] for s in steps),2)
        self.assertEqual(records['recovery']['orphaned_target_tokens_masked'],2)
        self.assertEqual(records['recovery']['unmasked_target_tokens'],0)
        self.assertEqual(sum(r['input_tokens_in_resume_replay_only'] for r in records.values()),6)
        self.assertEqual(sum(r['input_tokens_in_optimized_chunks'] for r in records.values()),6)


if __name__=='__main__':unittest.main()
