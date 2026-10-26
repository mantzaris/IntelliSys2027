import unittest
from supplements.generalization_edge_cases_009.scenarios import *
class Cases(unittest.TestCase):
 def test_pairs_and_boundaries(self):
  rows=all_scenarios();self.assertEqual(len(rows),32);self.assertEqual(len({s.family_id for s in rows}),16)
  for x,y in zip(rows[::2],rows[1::2]):
   self.assertEqual(x.spec.public(),y.spec.public());self.assertEqual(len(x.messages),32)
   differing=[i+1 for i,(a,b) in enumerate(zip(x.messages,y.messages)) if a.text!=b.text]
   self.assertEqual(differing,[12,20] if '07'==x.family_id[-2:] else [12])
   k=metadata(x)['slot'];self.assertNotEqual(x.truth_at(12).target(x.spec)['plan'][k],y.truth_at(12).target(y.spec)['plan'][k])
   for s in (x,y):
    initial=s.truth_at(1).values
    for t in range(2,33):
     self.assertTrue(all(v==initial[j] for j,v in enumerate(s.truth_at(t).values) if j!=k))
 def test_known_answers_and_mutations(self):
  for c in CONTEXTS:
   for p in PATTERNS:
    a,h=family(c,p);k=metadata(a)['slot']
    self.assertEqual(h.truth_at(12).values[k],h.truth_at(11).values[k])
    if p!='ambiguity_resolution':self.assertNotEqual(a.truth_at(12).values[k],a.truth_at(11).values[k]);self.assertEqual(a.truth_at(12).evidence[k],23)
    if p=='ambiguity_resolution':
     self.assertIn(k,h.truth_at(12).pending);self.assertNotIn(k,a.truth_at(12).pending)
     self.assertFalse(h.truth_at(20).pending);self.assertEqual(h.truth_at(20).evidence[k],39)
    # Mutating annotation to approve quoted material must fail the expected no-change property.
    wrong=h.truth_at(11);wrong.apply(h.messages[11],Event('set',((k,OPTIONS[k][(OPTIONS[k].index(wrong.values[k])+1)%3]),)))
    self.assertNotEqual(wrong.values[k],h.truth_at(12).values[k])
 def test_observation_boundary(self):
  from pcc.memory import observation,WorkingMemory
  s=all_scenarios()[0];p=observation(s.spec,[s.prior_assistant_proposal,*s.messages[:12]],WorkingMemory())
  self.assertNotIn('expectations',str(p));self.assertNotIn('graph_hash',str(p));self.assertNotIn('truth',str(p))
if __name__=='__main__':unittest.main()
