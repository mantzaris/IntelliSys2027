"""Distinguish correctness transitions, answer changes and output failures."""
import sys
from pathlib import Path
import unittest
from rep_sensitivity.analysis import repetition_values

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from analyze_main_transitions import transition, describe


def row(choice, correct=False, failure=False):
    return dict(choice=choice, correct=correct, operational_failure=failure)


class TransitionTests(unittest.TestCase):
    def test_interaction_cluster_order_does_not_depend_on_input_order(self):
        rows=[]
        for pair in ('zeta','alpha','mu'):
            for org in ('flat','hierarchical'):
                for condition in ('single','exact','paraphrase'):
                    rows.append(dict(pair_id=pair,model='fixture',policy='ordinary',organization=org,
                        repetition=0,world=0,condition=condition,correct=(org=='flat' or condition=='single')))
        a=repetition_values(rows,interaction=True)
        b=repetition_values(list(reversed(rows)),interaction=True)
        self.assertEqual(list(a),['alpha','mu','zeta'])
        self.assertEqual(list(a),list(b))
        self.assertEqual(a,b)
        self.assertTrue(all(v==1 for v in a.values()))

    def test_wrong_to_wrong_changes_answer_but_not_accuracy(self):
        x=transition(row('P'),row('Q'))
        self.assertEqual(x['wrong_to_wrong_answer_change'],1)
        self.assertEqual(x['answer_change'],1)
        self.assertEqual(x['accuracy_effect'],0)
        self.assertEqual(x['correctness_change'],0)

    def test_failed_delivery_is_error_even_if_root_choice_matches(self):
        x=transition(row('P',failure=True),row('P',correct=True))
        self.assertEqual(x['correction'],1)
        self.assertEqual(x['answer_comparable'],0)
        self.assertEqual(x['answer_change'],0)

    def test_balanced_corrections_can_hide_changes_and_resample_whole_bases(self):
        pairs=[('a',row('P'),row('Q',True)),('a',row('Q',True),row('P')),
               ('b',row('P'),row('Q',True)),('b',row('Q',True),row('P'))]
        result=describe(pairs,{'a':('numeric',False),'b':('numeric',False)})
        self.assertEqual(result['totals']['correction'],2)
        self.assertEqual(result['totals']['regression'],2)
        self.assertEqual(result['totals']['accuracy_effect'],0)
        self.assertEqual(result['intervals']['accuracy_effect']['clusters'],2)
        self.assertEqual(result['intervals']['accuracy_effect']['lower'],0)
        self.assertEqual(result['intervals']['correctness_change']['estimate'],1)


if __name__=='__main__': unittest.main()
