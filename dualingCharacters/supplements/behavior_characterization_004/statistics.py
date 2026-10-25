"""Matched family rates; worlds and temporal observations never resampled alone."""
from collections import defaultdict
import numpy as np

BOOTSTRAP_SEED=400041
DRAWS=10000

def paired_worlds(episodes):
    seen=set();worlds=defaultdict(set)
    for episode in episodes:
        key=episode['family_id'],episode['world']
        if key in seen:raise ValueError('Duplicate family/world')
        seen.add(key);worlds[key[0]].add(key[1])
    if any(w!={'authorized','hypothetical'} for w in worlds.values()):raise ValueError('Missing paired world')
    return sorted(worlds)

def family_rate_rows(rows):
    values=defaultdict(lambda:[0,0])
    for row in rows:
        key=tuple(row[k] for k in ('cohort','condition','seed','family_id','metric'))
        values[key][0]+=row['numerator'];values[key][1]+=row['denominator']
    return [dict(zip(('cohort','condition','seed','family_id','metric'),key),numerator=n,denominator=d,rate=n/d if d else None)
        for key,(n,d) in sorted(values.items())]

def contrast(values,seeds,first,second,metric,cohort,draws=DRAWS):
    lookup={(r['condition'],r['seed'],r['family_id']):r['rate'] for r in values if r['cohort']==cohort and r['metric']==metric}
    family_sets=[{f for (c,s,f),v in lookup.items() if c==condition and s==seed and v is not None}
        for seed in seeds for condition in (first,second)]
    families=sorted(set.intersection(*family_sets)) if family_sets else []
    result={'cohort':cohort,'first':first,'second':second,'metric':metric,'seeds':seeds,
        'matched_families':len(families),'candidate_families':len(set.union(*family_sets)) if family_sets else 0,
        'uncertainty':'paired family bootstrap' if len(seeds)==1 else 'paired family/seed two-way bootstrap',
        'draws':draws,'bootstrap_seed':BOOTSTRAP_SEED,'seed_generalization':'limited; generator seed also changes assignments, not independently trained character policies'}
    if not families:return dict(result,first_mean=None,second_mean=None,difference=None,lower=None,upper=None)
    a=np.array([[lookup[first,s,f] for f in families] for s in seeds]);b=np.array([[lookup[second,s,f] for f in families] for s in seeds]);delta=a-b
    result.update(first_mean=float(a.mean()),second_mean=float(b.mean()),difference=float(delta.mean()))
    if len(families)<2:return dict(result,lower=None,upper=None)
    rng=np.random.default_rng(BOOTSTRAP_SEED)
    family_indices=rng.integers(0,len(families),(draws,len(families)))
    if len(seeds)==1:sample=delta[0,family_indices].mean(axis=1)
    else:
        seed_indices=rng.integers(0,len(seeds),(draws,len(seeds)))
        sample=delta[seed_indices[:,:,None],family_indices[:,None,:]].mean(axis=(1,2))
    lo,hi=np.quantile(sample,[.025,.975]);return dict(result,lower=float(lo),upper=float(hi))

def all_contrasts(family_rows):
    output=[]
    for cohort in sorted({r['cohort'] for r in family_rows}):
        for first,second in [('C5','C3'),('C5','A1')]:
            seeds=sorted({r['seed'] for r in family_rows if r['cohort']==cohort and r['condition']==first}&
                         {r['seed'] for r in family_rows if r['cohort']==cohort and r['condition']==second})
            for metric in sorted({r['metric'] for r in family_rows if r['cohort']==cohort}):
                for seed in seeds:output.append(contrast(family_rows,[seed],first,second,metric,cohort))
                if len(seeds)>1:output.append(contrast(family_rows,seeds,first,second,metric,cohort))
    return output
