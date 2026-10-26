"""Artifact integration with explicit prerequisites, independent of model availability."""
import sys
from collections import Counter
from .common import *

def main():
 needed=[HERE/'inputs/research.json',HERE/'inputs/compatibility_semantic.json',HERE/'tables/ANNOTATIONS.json',HERE/'tables/COMPATIBILITY_INTERACTION_EVENTS.json']
 missing=[str(p.relative_to(ROOT)) for p in needed if not p.exists()]
 if missing:
  print(json.dumps({'status':'missing_prerequisites','files':missing,'command':'Run bundle --extract, then documented CPU analysis commands; no inference required.'}));return 2
 for path in ['PROFILE_FREEZE.json','FINAL_PROMPT_FREEZE.json','SCIENTIFIC_FREEZE.json','ANALYSIS_AMENDMENT_001_FREEZE.json','RECOVERY_POLICY_FREEZE.json','CONTINUATION_001_FREEZE.json']:verify(HERE/path)
 items=read(HERE/'inputs/research.json');assert len(items)==692
 keys=[r['item_id'] for r in items];assert len(keys)==len(set(keys))
 assert Counter(r['population'] for r in items)=={'broad':540,'fixed72':72,'synthetic_holdout':80}
 fixed=[r for r in items if r['population']=='fixed72'];routes=Counter(r['public']['route'] for r in fixed)
 assert routes=={'component':64,'answerer':8},routes
 rows=read(HERE/'tables/ANNOTATIONS.json');assert len(rows)==1664
 assert len({(r['item_id'],r['model'],r['probe']) for r in rows})==len(rows)
 assert all(r['record_status']!='not_recorded' for r in rows),'Incomplete observations remain missing; not a complete measurement grid'
 for m in ['phi','qwen']:
  rr=[r for r in rows if r['model']==m];assert len(rr)==832
  assert sum(r['population']=='synthetic_holdout' for r in rr)==80
  assert sum(r['population']=='broad' and r['probe']=='base' for r in rr)==540
 for r in read(HERE/'tables/SEMANTIC_RATES.json'):
  assert not r['population'].startswith('synthetic_')
  assert sum(r['label_counts'].values())==r['planned']
  if r['population']=='broad':assert r['planned']==90
 primary=read(HERE/'tables/COMPATIBILITY_PRIMARY_RESPONSE.json');assert sum(r['compatible_count'] for r in primary)==128 and sum(r['incompatible_count'] for r in primary)==128
 assert len(read(HERE/'tables/COMPATIBILITY_EPISODES.json'))==64
 actual=read(HERE/'reports/COMPATIBILITY_SEMANTIC_INPUT_BINDING.json');assert sha(HERE/'inputs/compatibility_semantic.json')==actual['payload_sha256']
 for path in [HERE/'paper/sections/dialogues.tex',HERE/'paper/sections/controlled_dialogue.tex']:
  assert 'file://' not in path.read_text()
 report={'status':'passed','scientific_freezes':6,'fixed_events':72,'fixed_component_events':64,'fixed_answerer_events':8,'broad_events':540,'heldout_controls_per_model':80,'final_judgment_tasks_including_probes':1664,'real_base_sample_records':644,'unique_underlying_real_events':641,'controlled_conversations':64,'primary_controlled_reserved_opportunities':256,'human_annotations':0,'qualification':'Software, coverage and source-binding checks; not semantic ground-truth validation.'}
 write(HERE/'reports/OUTPUT_VERIFICATION.json',report);print(report);return 0
if __name__=='__main__':sys.exit(main())
