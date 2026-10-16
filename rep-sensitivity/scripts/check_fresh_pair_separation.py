"""Outcome-blind, name-invariant separation for the bounded scheduling extension."""
from rep_sensitivity.generation import generate_pair
from rep_sensitivity.schema import canonical,digest


def structure(pair):
    # Generation-order job/resource IDs are arbitrary names. Candidate IDs and
    # tie priority do not make a case structurally novel. Absolute time is removed.
    w=pair['worlds'][0];jobs=[j['identifier'] for j in w['jobs']];resources=list(w['capacities'])
    names={j:i for i,j in enumerate(jobs)};machines={r:i for i,r in enumerate(resources)}
    offset=min(t for c in w['candidates'] for t in c['starts'].values())
    candidates=sorted(w['candidates'],key=lambda c:tuple(c['starts'][j] for j in jobs))
    order=[c['identifier'] for c in candidates]
    worlds=[]
    for world in pair['worlds']:
        cs={c['identifier']:c for c in world['candidates']}
        worlds.append({'jobs':[(j['duration'],sorted((machines[r],d) for r,d in j['demands'].items()),
            max(0,j.get('release',0)-offset), None if j.get('deadline') is None else j['deadline']-offset) for j in world['jobs']],
            'capacities':[world['capacities'][r] for r in resources],
            'precedence':sorted((names[a],names[b]) for a,b in world['precedence']),
            'starts':[[cs[c]['starts'][j]-offset for j in jobs] for c in order],
            'downtime':sorted((machines[r],[(a-offset,b-offset) for a,b in intervals]) for r,intervals in world.get('downtime',{}).items())})
    # Reversing the two worlds is not a new structural pair.
    return sorted(worlds,key=canonical)


def flatten(value,path=()):
    if isinstance(value,dict):return {k:v for a,b in value.items() for k,v in flatten(b,path+(a,)).items()}
    if isinstance(value,(list,tuple)):return {k:v for i,b in enumerate(value) for k,v in flatten(b,path+(i,)).items()}
    return {path:value}


def distance(a,b):
    return sum(a.get(k,('missing',))!=b.get(k,('missing',)) for k in a.keys()|b.keys())


def select(count_per_stratum=4,start=768,stop=4096):
    prior=[]
    for split,indices in [('development',range(24)),('validation',range(60)),('heldout',list(range(192))+list(range(384,432)))]:
        for i in indices:
            if i%6<3:prior.append(flatten(structure(generate_pair(split,i,2))))
    selected=[];rejected=[];counts={}
    for i in range(start,stop):
        if i%6>=3:continue
        pair=generate_pair('heldout',i,2);stratum=(pair['evaluation']['family'],pair['evaluation']['decision_changed'])
        if counts.get(stratum,0)>=count_per_stratum:continue
        signature=flatten(structure(pair));nearest=min(distance(signature,p) for p in prior)
        if nearest<3:
            rejected.append({'index':i,'reason':'at most two normalized structural field changes','minimum_distance':nearest});continue
        selected.append({'index':i,'pair_id':pair['pair_id'],'seed':pair['seed'],'stratum':stratum,
                         'normalized_structure_sha256':digest(structure(pair)),'minimum_prior_field_distance':nearest})
        prior.append(signature);counts[stratum]=counts.get(stratum,0)+1
        if len(selected)==6*count_per_stratum:break
    if len(selected)!=6*count_per_stratum:raise RuntimeError('Cannot satisfy the prespecified fresh-structure rule')
    return {'selected':selected,'rejected':rejected,'criterion':'At least three leaf-field changes after name, absolute-time, candidate-order and world-order normalization. This excludes exact isomorphic copies and one/two-field near clones, not all shared motifs. Comparisons never use model outcomes.',
            'limitations':'All cases retain the existing scheduling generator and heldout fork-join motifs; no new task-family generalization.',
            'prior_sets':'development 0:24, validation 0:60, original heldout 0:192, reserved mechanism heldout 384:432',
            'start':start,'stop':stop}

if __name__=='__main__':
    import json
    print(json.dumps(select(),indent=2))
