"""Recalculate old mechanical results without rewriting historical outputs."""
import csv
from collections import defaultdict
from .common import *
from supplements.dialogue_interpretation_005.statistics import expand,METRICS
from supplements.behavior_characterization_004.statistics import contrast

def main():
 old=ROOT/'supplements/results_clarity_007';dialogue=ROOT/'supplements/dialogue_interpretation_005'
 source=dialogue/'tables/FAMILY_NUMERATORS.csv'
 with source.open() as f:rows=expand(list(csv.DictReader(f)))
 contrasts=[]
 for expected in read(dialogue/'tables/REPRODUCED_CONTRASTS.json'):
  actual=contrast(rows,expected['seeds'],expected['first'],expected['second'],expected['metric'],'main_round_zero')
  for k in ['difference','lower','upper','first_mean','second_mean']:assert abs(actual[k]-expected[k])<1e-12
  contrasts.append(actual)
 sums=defaultdict(lambda:[0,0])
 for r in rows:
  for seed in [str(r['seed']),'all']:
   key=r['condition'],seed,r['metric'];sums[key][0]+=r['numerator'];sums[key][1]+=r['denominator']
 with (old/'tables/MECHANICAL_COUNTS.csv').open() as f:
  for r in csv.DictReader(f):assert sums[r['condition'],r['generator_seed'],r['metric']]==[int(r['numerator']),int(r['denominator'])]
 for name in ['MECHANICAL_COUNTS.csv','CHANNELS_AND_CHANGES.csv']:
  (HERE/'tables'/name).write_bytes((old/'tables'/name).read_bytes())
 (HERE/'inputs/FAMILY_NUMERATORS.csv').write_bytes(source.read_bytes());write(HERE/'tables/MECHANICAL_CONTRASTS.json',contrasts)
 write(HERE/'reports/MECHANICAL_REPRODUCTION.json',{'contrasts':len(contrasts),'unique_families':150,'episodes_per_condition':900,'opportunities_per_condition':10800,'seeds':[17,29,43],'inputs':{str(p.relative_to(ROOT)):sha(p) for p in [source,dialogue/'tables/REPRODUCED_CONTRASTS.json',old/'tables/CHANNELS_AND_CHANGES.csv']},'qualified':'Recomputed fixed sufficient statistics; original broad trace reconstruction remains the historical audit. This is not an independent semantic validation.'})
 print('72 contrasts reproduced; old files unchanged')
if __name__=='__main__':main()
