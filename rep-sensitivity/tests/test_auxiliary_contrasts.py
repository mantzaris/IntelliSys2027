"""Known interactions must retain signs, pairing and independent-cluster units."""
import unittest
from rep_sensitivity.aux_analysis import unique_clause_interaction


class AuxiliaryContrastTests(unittest.TestCase):
    def test_unique_clause_harm_and_retention_are_opposite_signed(self):
        rows=[]
        for pair in ('a','b'):
            for world in (0,1):
                for rep in (0,1):
                    for arm in ('decisive_high','decisive_low','harmless_high','harmless_low'):
                        rows.append({'pair_id':pair,'world':world,'repetition':rep,'arm':arm,
                            'correct':arm!='decisive_high','unique_clause_retained':arm!='decisive_high'})
        values,n=unique_clause_interaction(rows,'decision_error')
        self.assertEqual(values,{'a':1.0,'b':1.0});self.assertEqual(n,8)
        retained,n=unique_clause_interaction(rows,'unique_clause_retained')
        self.assertEqual(retained,{'a':-1.0,'b':-1.0})
        # An unobserved member is excluded, never imputed as success or failure.
        partial=[r for r in rows if not (r['pair_id']=='a' and r['arm']=='harmless_low')]
        self.assertEqual(unique_clause_interaction(partial,'decision_error'),({'b':1.0},4))
