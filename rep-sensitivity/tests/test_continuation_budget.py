import unittest
from scripts.run_objective_confirmation import prior_seconds

class ContinuationBudgetTests(unittest.TestCase):
    def test_restart_charges_ambiguous_attempt_without_resetting_allowance(self):
        completed=[{'event':'attempt_start','attempt':'one','reserved_seconds':7200},
                   {'event':'attempt_end','attempt':'one','elapsed_seconds':1900}]
        self.assertEqual(prior_seconds(completed),1900)
        crashed=completed+[{'event':'attempt_start','attempt':'two','reserved_seconds':5300}]
        self.assertEqual(prior_seconds(crashed),7200)
        recovered=crashed+[{'event':'attempt_end','attempt':'two','elapsed_seconds':2100}]
        self.assertEqual(prior_seconds(recovered),4000)

if __name__=='__main__':unittest.main()
