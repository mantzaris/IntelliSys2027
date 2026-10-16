from copy import deepcopy
import unittest
from rep_sensitivity.generation import generate_pair,oracle
from rep_sensitivity.reports import make_reports
from rep_sensitivity.targeted_replay import lossless_summary
from rep_sensitivity.metrics import parse
from rep_sensitivity.schema import canonical
from scripts.audit_root_information import visible_answer


class RootInformationTests(unittest.TestCase):
    def test_hidden_truth_is_not_used_to_repair_a_summary(self):
        pair=generate_pair('development',6,2); world=pair['worlds'][0]
        reports=make_reports(world,'development',pair['seed'])
        obj,_=parse(canonical(lossless_summary(reports)),world['tie_order'],manager=True)
        truth=oracle(world)['answer']
        other=next(c for c in world['tie_order'] if c!=truth)
        changed=deepcopy(obj)
        for assertion in changed['assertions']:
            if '/objective/' in assertion[0]:assertion[1]=0 if assertion[0].startswith(other+'/') else 100
        answer,possible=visible_answer(world,reports,[{'summary':changed}])
        self.assertEqual(answer,other);self.assertNotEqual(answer,truth)
        changed['assertions']=[a for a in changed['assertions'] if '/objective/' not in a[0]]
        answer,possible=visible_answer(world,reports,[{'summary':changed}])
        self.assertEqual(answer,'INSUFFICIENT');self.assertGreater(len(possible),1)


if __name__=='__main__':unittest.main()
