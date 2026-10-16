from copy import deepcopy
import unittest

from rep_sensitivity.generation import generate_pair, oracle
from rep_sensitivity.reports import make_reports
from rep_sensitivity.metrics import parse
from rep_sensitivity.schema import canonical
from rep_sensitivity.targeted_replay import lossless_summary
from rep_sensitivity.pilot_interpretation import paired_effect, paired_world_rows, failure_locations


class PilotInterpretationTests(unittest.TestCase):
    def test_whole_cluster_effect_and_leave_one_out(self):
        rows = []
        for pid, values in [('a', (False, True)), ('b', (True, False)), ('c', (False, True))]:
            # Unequal within-cluster counts must not change the equal-base mean.
            for rep in range(1 if pid != 'a' else 5):
                for condition, correct in zip(('single', 'exact'), values):
                    rows.append(dict(pair_id=pid, model='m', world=0, organization='hierarchical',
                        policy='ordinary', repetition=rep, condition=condition, correct=correct,
                        family='numeric', decision_changed=True))
        r = paired_effect(rows, 'exact')
        self.assertAlmostEqual(r['estimate'], 1/3)
        self.assertEqual(r['clusters'], 3)
        self.assertEqual((r['improvements'], r['regressions'], r['unchanged']), (6, 1, 0))
        self.assertEqual(r['leave_one_base_out'], {'a': 0, 'b': 1, 'c': 0})
        with self.assertRaises(ValueError):
            paired_effect(rows[:-1], 'exact')

    def test_pair_success_requires_both_correct_not_change_alone(self):
        rows = [dict(pair_id='p', model='m', organization='flat', policy='ordinary', condition='single',
            repetition=0, world=w, decision_changed=True, oracle_choice=['A', 'B'][w],
            choice=['C', 'A'][w], correct=False) for w in (0, 1)]
        r = paired_world_rows(rows)[0]
        self.assertTrue(r['answer_changed']); self.assertFalse(r['correct'])
        with self.assertRaises(ValueError):
            paired_world_rows(rows[:1])

    def fixture(self):
        pair = generate_pair('development', 6, 2); world = pair['worlds'][0]
        reports = make_reports(world, 'development', pair['seed'])
        summary, _ = parse(canonical(lossless_summary(reports)), world['tie_order'], manager=True)
        return world, reports, summary

    def test_wrong_candidate_binding_does_not_retain_objective(self):
        world, reports, summary = self.fixture()
        objective = next(r.claim for r in reports if r.claim.task_identifier == 'objective')
        changed = deepcopy(summary)
        for a in changed['assertions']:
            if a[0] == objective.key:
                a[0] = 'another_candidate/objective/current'
        root = {**summary, 'choice': oracle(world)['answer']}
        result = failure_locations(world, reports, [changed], root, True, False, {objective.key})
        self.assertTrue(result['necessary_fact_omitted'])
        self.assertNotIn(objective.key, result['retained_keys_strict'])
        # Boolean true must not count as the numerical objective 1.
        changed = deepcopy(summary)
        for a in changed['assertions']:
            if a[0] == objective.key:
                a[1] = True
        result = failure_locations(world, reports, [changed], root, True, False, {objective.key})
        self.assertTrue(result['necessary_value_wrong_or_conflicted'])

    def test_invalid_selection_after_complete_delivery_and_wrong_support(self):
        pair = generate_pair('development', 0, 2); world = pair['worlds'][0]
        reports = make_reports(world, 'development', pair['seed'])
        summary, _ = parse(canonical(lossless_summary(reports)), world['tie_order'], manager=True)
        truth = oracle(world)
        invalid = next(c for c, v in truth['candidates'].items() if not v['feasible'])
        root = {**summary, 'choice': invalid}
        result = failure_locations(world, reports, [summary], root, False, False)
        self.assertTrue(result['visible_false_constraint_ignored'])
        self.assertTrue(result['complete_constraints_delivered_invalid_choice'])
        self.assertTrue(result['root_error_despite_sufficient_visible_truth'])
        self.assertFalse(result['necessary_fact_omitted'])
        root = deepcopy(summary); root['choice'] = truth['answer']
        root['assertions'][0][1] = 99999
        result = failure_locations(world, reports, [summary], root, True, False)
        self.assertTrue(result['correct_choice_erroneous_support'])

    def test_scope_contains_units_condition_version_and_entity(self):
        from dataclasses import replace
        world, reports, summary = self.fixture()
        claim = reports[0].claim
        for field, value in [('units', 'other_units'), ('applicability_condition', 'only_T'),
                             ('effective_time_or_version', 'superseded'), ('entity_identifier', 'other_entity')]:
            self.assertNotEqual(claim.key, replace(claim, **{field: value}).key)


if __name__ == '__main__':
    unittest.main()
