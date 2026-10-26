import unittest
from supplements.generalization_edge_cases_009.analysis import recovery,field_correct,eligible_goal,interval
class Metrics(unittest.TestCase):
 def test_recovery(self):
  self.assertEqual(recovery([True]*8,list(range(1,9)),1)['status'],'never_wrong')
  self.assertEqual(recovery([False,True,True,True,False],list(range(1,6)),1)['latency'],1)
  self.assertEqual(recovery([False,True,True],list(range(1,4)),1)['status'],'unrecovered')
 def test_dynamic_clarification(self):
  r={'generation':{'parsed':{'plan':[None]*6,'clarify':['day']}},'target':{'plan':[None]*6,'clarify':['day']}}
  self.assertTrue(field_correct(r,3));r['generation']['parsed']['clarify']=[];self.assertFalse(field_correct(r,3))
 def test_invalid_goal_and_empty(self):
  self.assertIsNone(eligible_goal({'slot':True,'value':'onsite'}));self.assertIsNone(eligible_goal({'slot':0,'value':'online'}));self.assertEqual(interval([]),[None,None])
if __name__=='__main__':unittest.main()
