import unittest,json
from pcc.characters import cast,apply_action,action_prompt
from pcc.memory import WorkingMemory
from supplements.generalization_edge_cases_009.scenarios import all_scenarios
class Routes(unittest.TestCase):
 def test_note_vs_direct_and_truncation(self):
  actors=cast('C5','fixture',17);memory=WorkingMemory();claim='x'*300
  a={'kind':'recollect','slot':0,'value':'Harbor','source':23,'claim':claim}
  r=apply_action(a,actors[0],actors,memory,'C5',6);self.assertTrue(r['applied']);self.assertEqual(memory.state,[None]*6);self.assertNotIn('source',memory.notes[0]);self.assertEqual(memory.notes[0]['claim'],claim[:240])
  r=apply_action({**a,'kind':'edit'},actors[0],actors,memory,'C5',6);self.assertEqual(memory.state[0],'Harbor');self.assertEqual(memory.evidence[0],23)
 def test_peer_and_rejection(self):
  actors=cast('C5','fixture',17);memory=WorkingMemory();a={'kind':'peer','slot':0,'value':'Harbor','source':23,'claim':'Preference','target':actors[1].alias}
  r=apply_action(a,actors[0],actors,memory,'C5',6,True);self.assertTrue(r['applied']);self.assertEqual(actors[1].inbox[0]['source'],23);self.assertFalse(memory.notes)
  r=apply_action({**a,'kind':'edit'},actors[0],actors,memory,'C5',6,True);self.assertFalse(r['applied']);self.assertIn('rejected_reason',r)
if __name__=='__main__':unittest.main()
