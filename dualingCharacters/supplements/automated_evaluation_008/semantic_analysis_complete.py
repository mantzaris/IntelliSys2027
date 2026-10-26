"""Versioned composition of persisted source records if an exact-ID continuation is needed."""
from . import semantic_analysis_v2 as base
from .common import *

def load_complete(bindings,items):
 by={};provenance=[]
 for model,runs in bindings.items():
  for run in runs:
   rows,prov=base.load_runs({model:[run]},items);provenance+=prov
   for row in rows:
    key=row['item_id'],row['model'],row['probe'];old=by.get(key)
    if old is None:by[key]=row
    elif old['record_status']=='not_recorded':
     if row['record_status']!='not_recorded':by[key]=row
    elif row['record_status']!='not_recorded':raise ValueError('Duplicate persisted judgment; never select a better label: '+str(key))
 return list(by.values()),provenance

def main():
 binding_path=HERE/'RUN_BINDINGS_COMPLETE.json'
 if not binding_path.exists():return base.main()
 verify(HERE/'CONTINUATION_001_FREEZE.json')
 items=read(HERE/'inputs/research.json')+read(HERE/'inputs/probes.json');items=list({i['item_id']:i for i in items}.values())+read(HERE/'inputs/compatibility_semantic.json')
 rows,provenance=load_complete(read(binding_path)['analysis'],items)
 write(HERE/'tables/ANNOTATIONS.json',rows);write(HERE/'tables/SEMANTIC_RATES.json',base.summarize(rows));write(HERE/'tables/SEMANTIC_CONTRASTS.json',base.paired_contrasts(rows));write(HERE/'tables/JUDGE_AGREEMENT.json',base.judge_agreement(rows));write(HERE/'tables/STABILITY.json',base.sensitivity(rows));write(HERE/'tables/JUDGE_PROVENANCE.json',provenance)
 overlap=set(read(HERE/'reports/SAMPLING.json')['overlap_families']);write(HERE/'tables/SEMANTIC_NONOVERLAP.json',base.paired_contrasts([r for r in rows if r['family'] not in overlap]))
 route_rows=[dict(r,stratum=str(r['stratum'])+' / '+str(r['route'])) for r in rows];write(HERE/'tables/SEMANTIC_BY_ROUTE.json',base.summarize(route_rows));write(HERE/'tables/AGREEMENT_BY_ROUTE.json',base.judge_agreement(route_rows))
 seed_rows=[dict(r,population=str(r['population'])+' / seed '+str(r['seed'])) for r in rows];write(HERE/'tables/SEMANTIC_BY_SEED.json',base.summarize(seed_rows))
 flat=[{k:v for k,v in r.items() if k not in {'labels','assertions','errors'}}|r['labels'] for r in rows];base.export_csv(HERE/'tables/ANNOTATIONS.csv',flat)
 print({'judgments':len(rows),'source_runs':len(provenance),'missing_preserved':sum(r['record_status']=='not_recorded' for r in rows),'no_human_ratings':True})
if __name__=='__main__':main()
