"""Reproduce frozen sufficient tables; no new raw-trace population or statistical test."""
from collections import defaultdict
from .common import *
from supplements.dialogue_interpretation_005.statistics import expand,METRICS
from supplements.behavior_characterization_004.statistics import contrast
CONDITIONS=('C3','C5','A1')

def run():
 rows=expand(csv_read(DIALOGUE/'tables/FAMILY_NUMERATORS.csv'))
 expected=read(DIALOGUE/'tables/REPRODUCED_CONTRASTS.json');checks=[]
 for old in expected:
  new=contrast(rows,old['seeds'],old['first'],old['second'],old['metric'],'main_round_zero')
  for key in ['difference','lower','upper','first_mean','second_mean']:assert abs(new[key]-old[key])<1e-12
  checks.append(new)
 write(HERE/'tables/CONTRASTS.json',checks)
 sums=defaultdict(lambda:[0,0])
 for r in rows:
  for seed in [str(r['seed']),'all']:
   k=r['condition'],seed,r['metric'];sums[k][0]+=r['numerator'];sums[k][1]+=r['denominator']
 output=[dict(zip(['condition','generator_seed','metric'],k),numerator=v[0],denominator=v[1],pooled_rate=v[0]/v[1] if v[1] else None) for k,v in sorted(sums.items())]
 csv_write(HERE/'tables/MECHANICAL_COUNTS.csv',output)
 source=csv_read(BEHAVIOR/'reports/CHANNELS.csv');ch=[]
 for r in source:
  if r['cohort']=='main_round_zero' and r['condition'] in CONDITIONS:
   ch.append({k:r[k] for k in ['condition','seed','metric','numerator','denominator','pooled_rate']})
 for c in CONDITIONS:
  for metric in sorted({r['metric'] for r in ch}):
   items=[r for r in ch if r['condition']==c and r['metric']==metric and r['seed']!='all']
   n=sum(int(r['numerator']) for r in items);d=sum(int(r['denominator']) for r in items)
   ch.append(dict(condition=c,seed='all',metric=metric,numerator=n,denominator=d,pooled_rate=n/d))
 for c in CONDITIONS:
  vals=[r for r in ch if r['condition']==c and r['seed']=='all' and r['metric'].startswith('channel_')]
  assert sum(int(r['numerator']) for r in vals)==10800
 csv_write(HERE/'tables/CHANNELS_AND_CHANGES.csv',ch)
 performance=csv_read(PREVIOUS/'tables/PERFORMANCE_CONTEXT.csv');csv_write(HERE/'tables/PERFORMANCE_CONTEXT.csv',performance)
 write(HERE/'reports/NUMERIC_VERIFICATION.json',{'frozen_contrasts_reproduced':len(checks),'family_rows':len(rows)//len(METRICS),'unique_families':len({r['family_id'] for r in rows}),'seeds':[17,29,43],'input_hashes':{str(p.relative_to(ROOT)):sha(p) for p in [DIALOGUE/'tables/FAMILY_NUMERATORS.csv',DIALOGUE/'tables/REPRODUCED_CONTRASTS.json',BEHAVIOR/'reports/CHANNELS.csv',PREVIOUS/'tables/PERFORMANCE_CONTEXT.csv']},'no_new_semantic_frequency_or_significance_test':True})
 print('Reproduced 72 frozen contrasts; all-opportunity channel sums; per-seed counts.')
if __name__=='__main__':run()
