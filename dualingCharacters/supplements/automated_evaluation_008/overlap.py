"""Underlying event identity across separately reported sampling populations."""
from collections import defaultdict
from .common import *
def main():
 rows=[r for r in read(HERE/'inputs/research.json') if not r['population'].startswith('synthetic_')];by=defaultdict(list);families=defaultdict(set)
 for r in rows:
  i=r['private']['identity'];key=tuple(i[k] for k in ['family_id','world','seed','condition','opportunity']);by[key].append(r);families[r['population']].add(i['family_id'])
 duplicates=[]
 for key,rs in by.items():
  if len(rs)>1:
   assert len({json.dumps(r['private']['source_locator'],sort_keys=True) for r in rs})==1
   duplicates.append({'identity':list(key),'items':[(r['population'],r['item_id']) for r in rs]})
 report={'archive_sample_records':len(rows),'unique_underlying_events':len(by),'duplicate_event_records_between_separate_populations':duplicates,'shared_families':sorted(families['broad']&families['fixed72']),'not_pooled':True,'qualification':'Three underlying opportunities are sampled in both fixed and broad populations; those populations and their uncertainty analyses remain separate. Non-overlap sensitivity excludes both shared families.'};write(HERE/'reports/PHYSICAL_EVENT_OVERLAP.json',report);print(report)
if __name__=='__main__':main()
