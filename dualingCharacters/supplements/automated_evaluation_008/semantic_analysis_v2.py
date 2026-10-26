"""Frozen descriptive analyses: retain missingness, routes and family dependence."""
import csv
from collections import defaultdict,Counter
import numpy as np
from .common import *
from .analysis import effective_labels,checked_output,agreements,binary_range,interval_family
from .judge_spec import QUESTIONS,BINARY

def export_csv(path,rows):
 if not rows:return
 with Path(path).open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def load_runs(bindings,items):
 lookup={i['item_id']:i for i in items};rows=[];provenance=[]
 for model,run_ids in bindings.items():
  for run in run_ids:
   path=ROOT/'artifacts/runs'/run/'judgments.jsonl'
   if not path.exists():
    status={'status':'not_started'}
   else:status=read(path.parent/'status.json')
   provenance.append({'run_id':run,'status':status['status'],'raw_sha256':sha(path) if path.exists() else None,'model_revision':status.get('model_revision'),'calls':status.get('model_calls'),'elapsed':status.get('gpu_reserved_seconds')})
   raw=list(stream(path)) if path.exists() else []
   if '-probes-' in run:
    expected=[(i,p) for i in read(HERE/'inputs/probes.json') for p in ['alias_permutation','category_order','api_exposed']]
   elif '-compatibility-judge-' in run:
    expected=[(i,'base') for i in items if i['population']=='compatibility']
   else:expected=[(i,'base') for i in items if i['population']!='compatibility']
   seen={(r['item_id'],r.get('probe','base')) for _,r in raw}
   assert len(seen)==len(raw),'Duplicate raw response identity'
   expected_keys={(i['item_id'],p) for i,p in expected};assert seen<=expected_keys,'Unexpected judgment identity'
   raw += [(None,{'item_id':i['item_id'],'probe':p,'status':'not_recorded','source_type':'automated_model'}) for i,p in expected if (i['item_id'],p) not in seen]
   for line,r in raw:
    if r['item_id'] not in lookup:continue
    item=lookup[r['item_id']];identity=item['private'].get('identity',{});labels=effective_labels(r,item);check=checked_output(r,item)
    rows.append({'item_id':r['item_id'],'model':model,'probe':r.get('probe','base'),'population':item['population'],'family':identity.get('family_id',item.get('template_family','')),'world':identity.get('world',''),'seed':identity.get('seed',''),'condition':identity.get('condition',''),'stratum':identity.get('stratum','communication' if item['population']=='fixed72' else ''),'route':item['public'].get('route'),'labels':labels,'assertions':check.get('assertions',[]),'record_status':r.get('status','recorded'),'format_valid':check['format_valid'],'errors':check['errors'],'repair':bool(r.get('repair')),'raw_run':run,'raw_line':line,'input_tokens':r.get('generation',{}).get('input_tokens',0),'output_tokens':r.get('generation',{}).get('output_tokens',0)})
 keys=[(r['item_id'],r['model'],r['probe']) for r in rows];assert len(keys)==len(set(keys)),'Duplicate judgment units'
 return rows,provenance

def summarize(rows):
 summaries=[];groups=defaultdict(list)
 for r in rows:
  if r['probe']=='base' and not r['population'].startswith('synthetic_'):
   groups[(r['population'],r['model'],r['condition'],r['stratum'])].append(r)
 for group,rs in sorted(groups.items()):
  for dim in QUESTIONS:
   counts=Counter(str(r['labels'][dim]) for r in rs);families=defaultdict(list)
   for r in rs:families[r['family']].append(r['labels'][dim]=='yes')
   yes=counts['yes'];no=counts['no'];joint=yes+no
   summaries.append({'population':group[0],'model':group[1],'condition':group[2],'stratum':group[3],'dimension':dim,'planned':len(rs),'families':len(families),'seeds':sorted(set(str(r['seed']) for r in rs)),'label_counts':dict(counts),'yes':yes,'no':no,'missing':counts['None'],'uncertain':counts['uncertain'],'not_applicable':counts['not_applicable'],'positive_rate_all_opportunities':yes/len(rs) if dim in BINARY else None,'positive_rate_substantive':yes/joint if joint and dim in BINARY else None,'family_interval_all_opportunities':interval_family([np.mean(x) for x in families.values()]) if dim in BINARY else None})
 return summaries

def paired_contrasts(rows):
 out=[];groups=defaultdict(list)
 for r in rows:
  if r['population'].startswith('broad') and r['probe']=='base':groups[r['model'],r['stratum']].append(r)
 for (model,stratum),rs in sorted(groups.items()):
  for comparison in ['C3','A1']:
   for dim in BINARY:
    vals=defaultdict(dict)
    for r in rs:vals[r['family'],r['world'],r['seed']][r['condition']]=r['labels'][dim]
    families=defaultdict(list);joint=defaultdict(list);seedvalues=defaultdict(list)
    for (family,world,seed),v in vals.items():
     assert 'C5' in v and comparison in v,'Missing paired condition'
     delta=int(v['C5']=='yes')-int(v[comparison]=='yes');families[family].append(delta);seedvalues[seed].append(delta)
     if v['C5'] in {'yes','no'} and v[comparison] in {'yes','no'}:joint[family].append(delta)
    means=[np.mean(v) for k,v in sorted(families.items())]
    out.append({'model':model,'stratum':stratum,'dimension':dim,'first':'C5','second':comparison,'families':len(families),'paired_events':sum(map(len,families.values())),'difference_all_opportunities':float(np.mean(means)),'family_interval':interval_family(means),'joint_substantive_pairs':sum(map(len,joint.values())),'joint_substantive_difference':float(np.mean([x for v in joint.values() for x in v])) if joint else None,'per_seed':{str(k):float(np.mean(v)) for k,v in seedvalues.items()},'qualification':'All-opportunity numerator counts positive classifications; missing/uncertain remain separate. Fixed three generator seeds averaged within family, not independent trained policies.'})
 return out

def judge_agreement(rows):
 groups=defaultdict(dict);out=[]
 for r in rows:
  if r['probe']=='base' and not r['population'].startswith('synthetic_'):groups[r['population'],r['condition'],r['stratum']].setdefault(r['item_id'],{})[r['model']]=r
 for group,units in sorted(groups.items()):
  for dim in QUESTIONS:
   first=[u.get('phi',{}).get('labels',{}).get(dim) for u in units.values()];second=[u.get('qwen',{}).get('labels',{}).get(dim) for u in units.values()]
   out.append({'population':group[0],'condition':group[1],'stratum':group[2],'dimension':dim,**agreements(first,second,dim in BINARY),'conservative_range':binary_range(first,second) if dim in BINARY else None})
 return out

def sensitivity(rows):
 by={(r['item_id'],r['model'],r['probe']):r for r in rows};groups=defaultdict(list);out=[]
 for r in rows:
  if r['probe']!='base':groups[r['model'],r['probe']].append(r)
 for (model,probe),rs in sorted(groups.items()):
  for dim in QUESTIONS:
   pairs=[(by.get((r['item_id'],model,'base'),{}).get('labels',{}).get(dim),r['labels'][dim]) for r in rs];joint=[(a,b) for a,b in pairs if a is not None and b is not None]
   out.append({'model':model,'probe':probe,'dimension':dim,'planned':len(rs),'jointly_assessed':len(joint),'changed':sum(a!=b for a,b in joint),'change_rate_joint':sum(a!=b for a,b in joint)/len(joint) if joint else None,'baseline_missing':sum(a is None for a,b in pairs),'probe_missing':sum(b is None for a,b in pairs)})
 return out

def main():
 allocation=read(HERE/'ALLOCATION.json');items=read(HERE/'inputs/research.json')+read(HERE/'inputs/probes.json');lookup={i['item_id']:i for i in items};items=list(lookup.values())
 if (HERE/'inputs/compatibility_semantic.json').exists():items+=read(HERE/'inputs/compatibility_semantic.json')
 bindings=read(HERE/'RUN_BINDINGS_FINAL.json')['analysis'];rows,provenance=load_runs(bindings,items)
 write(HERE/'tables/ANNOTATIONS.json',rows);write(HERE/'tables/SEMANTIC_RATES.json',summarize(rows));write(HERE/'tables/SEMANTIC_CONTRASTS.json',paired_contrasts(rows));write(HERE/'tables/JUDGE_AGREEMENT.json',judge_agreement(rows));write(HERE/'tables/STABILITY.json',sensitivity(rows));write(HERE/'tables/JUDGE_PROVENANCE.json',provenance)
 overlap=set(read(HERE/'reports/SAMPLING.json')['overlap_families']);write(HERE/'tables/SEMANTIC_NONOVERLAP.json',paired_contrasts([r for r in rows if r['family'] not in overlap]))
 route_rows=[dict(r,stratum=str(r['stratum'])+' / '+str(r['route'])) for r in rows];write(HERE/'tables/SEMANTIC_BY_ROUTE.json',summarize(route_rows));write(HERE/'tables/AGREEMENT_BY_ROUTE.json',judge_agreement(route_rows))
 seed_rows=[dict(r,population=str(r['population'])+' / seed '+str(r['seed'])) for r in rows];write(HERE/'tables/SEMANTIC_BY_SEED.json',summarize(seed_rows))
 flat=[{k:v for k,v in r.items() if k not in {'labels','assertions','errors'}}|r['labels'] for r in rows];export_csv(HERE/'tables/ANNOTATIONS.csv',flat)
 print({'judgments':len(rows),'runs':len(provenance),'no_human_ratings':True})
if __name__=='__main__':main()
