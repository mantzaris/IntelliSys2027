import unittest
from copy import deepcopy
from rep_sensitivity.generation import generate_pair, oracle
from rep_sensitivity.reports import make_reports
from rep_sensitivity.metrics import parse
from rep_sensitivity.schema import canonical
from rep_sensitivity.targeted_replay import lossless_summary
from scripts.visible_information_v2 import visible_state, assess_choice

class VisibleInformationV2Tests(unittest.TestCase):
    def fixture(self):
        pair=generate_pair('development',6,2);world=pair['worlds'][0]
        reports=make_reports(world,'development',pair['seed'])
        obj,_=parse(canonical(lossless_summary(reports)),world['tie_order'],manager=True)
        return world,reports,obj

    def test_omission_is_not_contradiction_or_justification(self):
        world,reports,obj=self.fixture()
        obj['assertions']=[a for a in obj['assertions'] if '/objective/' not in a[0]]
        s=visible_state(world,reports,[{'summary':obj}])
        self.assertEqual(s['status'],'incomplete_multiple_answers')
        self.assertEqual(set(s['possible_answers']),set(world['tie_order']))
        choice=oracle(world)['answer']
        a=assess_choice(s,choice)
        self.assertTrue(a['choice_possible_under_some_completion'])
        self.assertFalse(a['choice_justified_under_every_completion'])

    def test_contradiction_has_no_consistent_completion_even_if_unresolved(self):
        world,reports,obj=self.fixture()
        a=deepcopy(next(a for a in obj['assertions'] if '/objective/' in a[0]));a[1]+=1
        obj['assertions'].append(a);obj['unresolved'].append(a[0])
        s=visible_state(world,reports,[{'summary':obj}])
        self.assertEqual(s['status'],'contradictory');self.assertEqual(s['possible_answers'],[])
        self.assertIn(a[0],s['conflicting_scopes']);self.assertTrue(s['relaxed_possible_answers'])
        self.assertIsNone(assess_choice(s,oracle(world)['answer'])['choice_possible_under_some_completion'])

    def test_scope_error_and_type_error_not_silent_repairs(self):
        world,reports,obj=self.fixture();bad=deepcopy(obj)
        a=next(a for a in bad['assertions'] if '/objective/' in a[0]);a[0]='wrong_entity/objective/current'
        s=visible_state(world,reports,[{'summary':bad}]);self.assertIn(a[0],s['unknown_scope_keys'])
        self.assertTrue(s['missing_scopes'])
        bad=deepcopy(obj);a=next(a for a in bad['assertions'] if '/objective/' in a[0]);a[1]=True
        s=visible_state(world,reports,[{'summary':bad}]);self.assertEqual(s['status'],'invalid_values')
        self.assertIn(a[0],s['invalid_value_scopes']);self.assertEqual(s['possible_answers'],[])

    def test_consistent_wrong_values_and_application_failure_separate(self):
        world,reports,obj=self.fixture();truth=oracle(world)['answer'];other=next(c for c in world['tie_order'] if c!=truth)
        for a in obj['assertions']:
            if '/objective/' in a[0]:a[1]=0 if a[0].startswith(other+'/') else 100
        s=visible_state(world,reports,[{'summary':obj}]);self.assertEqual(s['justified_answers'],[other])
        self.assertTrue(assess_choice(s,truth)['sufficient_information_violated'])
        self.assertTrue(assess_choice(s,other)['agreement_with_unique_supported_decision'])

    def test_integer_objective_bounds_and_ties(self):
        world,reports,obj=self.fixture();first=world['tie_order'][0]
        obj['assertions']=[a for a in obj['assertions'] if '/objective/' not in a[0] or a[0].startswith(first+'/')]
        for a in obj['assertions']:
            if '/objective/' in a[0]:a[1]=0
        s=visible_state(world,reports,[{'summary':obj}]);self.assertEqual(s['justified_answers'],[first])
        # A missing objective cannot become negative just to defeat a known zero.
        duplicate=deepcopy(obj);duplicate['assertions']*=4
        self.assertEqual(s,visible_state(world,reports,[{'summary':duplicate}]))

if __name__=='__main__':unittest.main()
