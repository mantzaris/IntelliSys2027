import unittest
from .semantic_review_v2 import action_trace_name,selection,anonymize

class CompatibilityTests(unittest.TestCase):
    def test_compressed_and_plain_are_exact_locked_paths(self):
        for suffix in ('.jsonl','.jsonl.gz'):
            name='collection_characters'+suffix
            self.assertEqual(action_trace_name({'prefix':'collection','raw_hashes':{name:'hash'}}),name)
        with self.assertRaises(ValueError):action_trace_name({'prefix':'collection','raw_hashes':{}})
        with self.assertRaises(ValueError):action_trace_name({'prefix':'collection','raw_hashes':{'collection_characters.jsonl':'a','collection_characters.jsonl.gz':'b'}})

    def test_blinding_preserves_source_and_stable_speakers(self):
        raw={'speaker':'Rowan','claim':'Rowan contradicts Ellis at source 7','source':7}
        blinded=anonymize(raw,{'Rowan':'Speaker 1','Ellis':'Speaker 2'})
        self.assertEqual(blinded['speaker'],'Speaker 1');self.assertEqual(blinded['source'],7)
        self.assertEqual(blinded['claim'],'Speaker 1 contradicts Speaker 2 at source 7')

    def test_selection_matched_and_outcome_independent(self):
        cells=[{'id':str(seed)+c,'cohort':'main_round_zero','condition':c,'seed':seed,'family_ids':['f'+str(i) for i in range(10)],'schedule':[2,3]}
               for seed in (17,29,43) for c in ('C3','C5')]
        chosen=selection(cells);self.assertEqual(len(chosen),24)
        for seed in (17,29,43):
            for condition in ('C3','C5'):
                rows=[r for r in chosen if r['seed']==seed and r['condition']==condition]
                self.assertEqual(sum(r['world']=='authorized' for r in rows),2)
            self.assertEqual({(r['family_id'],r['world']) for r in chosen if r['seed']==seed and r['condition']=='C3'},
                             {(r['family_id'],r['world']) for r in chosen if r['seed']==seed and r['condition']=='C5'})

if __name__=='__main__':unittest.main()
