"""Compact reused numerical context, with unchanged provenance and no new endpoint."""
from collections import defaultdict
from .common import *

def run():
 source=OLD/'tables/FAMILY_NUMERATORS.csv';rows=list(csv.DictReader(source.open()));metrics=[k[:-2] for k in rows[0] if k.endswith('_n')]
 totals=defaultdict(lambda:[0,0])
 for r in rows:
  for metric in metrics:
   for seed in (str(r['seed']),'all'):
    pair=totals[r['condition'],seed,metric];pair[0]+=int(r[metric+'_n']);pair[1]+=int(r[metric+'_d'])
 summary=[{'condition':c,'generator_seed':s,'metric':m,'numerator':n,'denominator':d,'pooled_rate':n/d if d else None} for (c,s,m),(n,d) in sorted(totals.items())]
 csv_write(HERE/'tables/REPRODUCED_CONTEXT.csv',summary)
 original=list(csv.DictReader((OLD/'tables/KNOWN_BEHAVIOR.csv').open()))
 for r in original:
  n,d=totals[r['condition'],'all',r['metric']];assert n==int(r['numerator']) and d==int(r['denominator'])
 csv_write(HERE/'tables/PERFORMANCE_CONTEXT.csv',list(csv.DictReader((OLD/'tables/PRIOR_DEFENDER_CONTEXT.csv').open())))
 write(HERE/'reports/CONTEXT_PROVENANCE.json',{'input_sha256':sha(source),'related_family_rows':len(rows),'generator_seeds':[17,29,43],
  'original_counts_reproduced':len(original),'uncertainty_input':str((OLD/'tables/REPRODUCED_CONTRASTS.json').relative_to(ROOT)),
  'uncertainty_sha256':sha(OLD/'tables/REPRODUCED_CONTRASTS.json'),'performance_sha256':sha(OLD/'tables/PRIOR_DEFENDER_CONTEXT.csv'),
  'qualification':'Pooled counts and rates are separate from the original family/seed-resampled mean-rate contrasts. No semantic frequency is inferred; no new run enters the old cutoff.'})
 print('Reproduced27 existing pooled counts, plus per-seed numerators/denominators; preserved prior performance context.')
if __name__=='__main__':run()
