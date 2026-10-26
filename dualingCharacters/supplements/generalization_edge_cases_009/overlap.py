"""Exact script/decision-instance checks, with explicit shared-schema limitation."""
from dataclasses import asdict
from .common import *
from .scenarios import all_scenarios
from pcc.environment import make_family,digest

def run():
 old_sources=set();old_events=set();counts={};manifests={}
 for split in ('pilot','train','validation','test','natural'):
  p=ROOT/f'data/manifests/{split}.json';d=read(p);manifests[str(p.relative_to(ROOT))]=sha(p);counts[split]=len(d['families'])
  for i in range(counts[split]):
   for horizon in (16,32,64,128):
    for s in make_family(split,i,horizon):
     old_sources.add(digest([m.public() for m in s.source_messages()]));old_events.add(digest([asdict(e) for e in s.events]))
 rows=[]
 for s in all_scenarios():
  rows.append({'family':s.family_id,'world':s.world,'exact_source_overlap':digest([m.public() for m in s.source_messages()]) in old_sources,'exact_decision_sequence_overlap':digest([asdict(e) for e in s.events]) in old_events})
 assert not any(r['exact_source_overlap'] or r['exact_decision_sequence_overlap'] for r in rows)
 write(HERE/'inputs/OVERLAP.json',{'utc':now(),'core_manifest_hashes':manifests,'families_checked_by_split':counts,'horizons_checked':[16,32,64,128],'rows':rows,'scope':'Exact instantiated source and Event sequence comparison, not a claim of semantic novelty. Both contexts absent in inspected earlier generator source; six categorical fields, tools and conditional dependency remain shared.'})
if __name__=='__main__':run()
