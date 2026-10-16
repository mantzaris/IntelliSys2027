"""No model is called by these protocol-freeze guard checks."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from rep_sensitivity.study_execution import freeze_main,freeze_validation


class StudyFreezeTests(unittest.TestCase):
    def test_incomplete_pilot_and_weak_validation_block_heldout(self):
        templates=Path(__file__).resolve().parents[1]/'configs';previous=Path.cwd()
        try:
            with tempfile.TemporaryDirectory() as d:
                os.chdir(d)
                with self.assertRaisesRegex(RuntimeError,'pilot is not complete'):freeze_validation(templates)
                with self.assertRaisesRegex(RuntimeError,'complete validation'):freeze_main(templates)
                weak={'complete':True,'competence':[{'kind':'schedule','accuracy':0.8},{'kind':'schedule','accuracy':0.9}]}
                with patch('rep_sensitivity.study_execution.complete',return_value=True),patch('rep_sensitivity.study_execution.summarize',return_value=weak):
                    with self.assertRaisesRegex(RuntimeError,'competence is inadequate'):freeze_main(templates)
                self.assertFalse(Path('configs/frozen/main-v7.json').exists())
                self.assertFalse(list(Path('artifacts').glob('**/calls/*.json.gz')))
        finally:os.chdir(previous)

    def test_resource_rule_freezes_before_any_heldout_call(self):
        templates=Path(__file__).resolve().parents[1]/'configs';previous=Path.cwd()
        validation=json.loads((templates/'validation-candidate-v7.json').read_text())
        validation.update(name='validation-v7',status='frozen_validation',freeze_required=False)
        analysis={'complete':True,'competence':[{'kind':'schedule','accuracy':0.9},{'kind':'schedule','accuracy':0.9}]}
        try:
            with tempfile.TemporaryDirectory() as d:
                os.chdir(d);Path('configs/frozen').mkdir(parents=True)
                Path('configs/frozen/validation-v7.json').write_text(json.dumps(validation))
                projection=lambda source,config:{'projected_total_inference_hours':50 if config['base_pairs']==192 else 25}
                with patch('rep_sensitivity.study_execution.complete',return_value=True),patch('rep_sensitivity.study_execution.summarize',return_value=analysis),patch('rep_sensitivity.study_execution.project',side_effect=projection):
                    main=freeze_main(templates)
                self.assertEqual(main['base_pairs'],96)
                self.assertEqual(main['expected_trajectories'],13824)
                self.assertEqual(main['expected_manager_calls'],27648)
                self.assertTrue(Path('configs/frozen/supporting-v7.json').exists())
                self.assertTrue(Path('configs/frozen/live-v7.json').exists())
                self.assertFalse(list(Path('artifacts').glob('**/calls/*.json.gz')))
        finally:os.chdir(previous)
