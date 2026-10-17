import unittest
from copy import deepcopy
from rep_sensitivity.generation import generate_pair
from rep_sensitivity.reports import make_reports
from rep_sensitivity.targeted_replay import lossless_summary
from rep_sensitivity.metrics import parse
from rep_sensitivity.schema import canonical
from scripts.visible_information_v3 import visible_state,support_from_state,support_assessment


class DecisionSupportTests(unittest.TestCase):
    def fixture(self):
        p=generate_pair('development',6,2);world=p['worlds'][0]
        rs=make_reports(world,'development',p['seed'])
        obj,_=parse(canonical(lossless_summary(rs)),world['tie_order'],manager=True)
        selected=world['tie_order'][0]
        for a in obj['assertions']:
            if '/objective/' not in a[0] and not a[0].startswith(selected+'/'):a[1]=False
        return world,rs,obj,selected

    def test_invalid_objectives_need_not_prevent_unique_feasible_choice(self):
        world,rs,obj,selected=self.fixture()
        for a in obj['assertions']:
            if '/objective/' in a[0]:a[1]=True
        state=visible_state(world,rs,[{'summary':obj}]);support=support_from_state(state)
        self.assertEqual(state['status'],'invalid_values');self.assertEqual(state['possible_answers'],[])
        self.assertEqual(support['uncontested_unique_decision'],selected)
        self.assertTrue(support['determinate_despite_representation_errors'])
        other=next(c for c in world['tie_order'] if c!=selected)
        self.assertTrue(support_assessment(support,other)['violates_uncontested_unique_decision'])

    def test_irrelevant_conflict_stays_unresolved_without_vetoing_decision(self):
        world,rs,obj,selected=self.fixture()
        a=deepcopy(next(a for a in obj['assertions'] if '/objective/' in a[0] and not a[0].startswith(selected+'/')))
        a[1]+=1;obj['assertions'].append(a)
        state=visible_state(world,rs,[{'summary':obj}]);support=support_from_state(state)
        self.assertTrue(state['conflicting_scopes']);self.assertFalse(state['consistent'])
        self.assertEqual(support['uncontested_unique_decision'],selected)
        # Now the disputed candidate may compete. Do not select a preferred
        # number from the conflict or fill it with the world's hidden truth.
        competing=a[0].split('/')[0]
        for b in obj['assertions']:
            if b[0].startswith(competing+'/') and '/objective/' not in b[0]:b[1]=True
        support=support_from_state(visible_state(world,rs,[{'summary':obj}]))
        self.assertFalse(support['decision_determined_from_uncontested_facts'])

    def test_missing_objectives_with_multiple_feasible_candidates_stay_unknown(self):
        world,rs,obj,selected=self.fixture()
        for a in obj['assertions']:
            a[1]=True
        support=support_from_state(visible_state(world,rs,[{'summary':obj}]))
        self.assertEqual(set(support['uncontested_completion_answers']),set(world['tie_order']))
        self.assertIsNone(support['uncontested_unique_decision'])
        self.assertIsNone(support_assessment(support,selected)['agreement_with_uncontested_unique_decision'])


if __name__=='__main__':unittest.main()
