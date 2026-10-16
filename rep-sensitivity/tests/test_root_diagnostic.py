from copy import deepcopy
import unittest
from rep_sensitivity.root_diagnostic import repeat_assertions, supplied_inventory


class RootDiagnosticTests(unittest.TestCase):
    def test_root_copy_preserves_every_distinct_proposition_and_ancestry(self):
        source = [{'manager': 0, 'parse_status': 'valid', 'summary': {'unresolved': ['conflict'],
            'assertions': [['candidate_A/objective', 4, ['a']], ['candidate_B/objective', 5, ['b']],
                           ['conflict', False, ['c']], ['conflict', True, ['d']]]}}]
        old = deepcopy(source)
        copied, added = repeat_assertions(source, {'candidate_A/objective'}, 4)
        self.assertEqual(source, old)
        self.assertEqual(added, 3)
        self.assertEqual(supplied_inventory(source), supplied_inventory(copied))
        self.assertEqual(copied[0]['summary']['assertions'][:4], [source[0]['summary']['assertions'][0]]*4)
        self.assertEqual(copied[0]['summary']['unresolved'], ['conflict'])
        # Both sides of an existing contradiction survive. No hidden correction.
        contradiction, _ = repeat_assertions(source, {'conflict'}, 4)
        self.assertEqual(supplied_inventory(source), supplied_inventory(contradiction))

    def test_missing_target_never_fabricated_or_recovered_from_truth(self):
        source = [{'manager': 0, 'parse_status': 'valid', 'summary': {'unresolved': [], 'assertions': []}}]
        copied, added = repeat_assertions(source, {'missing'}, 4)
        self.assertEqual(added, 0); self.assertEqual(copied, source)

    def test_end_placement_changes_position_not_content(self):
        source = [{'manager': 0, 'summary': {'unresolved': [], 'assertions': [['a', 4, ['r1']], ['b', 5, ['r2']]]}}]
        adjacent, _ = repeat_assertions(source, {'a'}, 4)
        end, _ = repeat_assertions(source, {'a'}, 4, 'end')
        self.assertNotEqual(adjacent, end)
        self.assertEqual(supplied_inventory(adjacent), supplied_inventory(end))
        self.assertEqual(end[0]['summary']['assertions'][1][0], 'b')


if __name__ == '__main__': unittest.main()
