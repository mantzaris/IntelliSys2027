"""Portable checks of paired data, frozen statistics, quotations and paper structure.
No original artifact directory, model, GPU, network or project package is used.
Bootstrap algorithms preserve the historical sampling order and seeds.
"""
from pathlib import Path
from collections import defaultdict
import csv, hashlib, json, random, re, statistics
import numpy as np
P=Path(__file__).resolve().parents[1];D=P/'data'
def load(name):return json.loads((D/name).read_text())
def csvload(name):return list(csv.DictReader((D/name).open()))
def close(a,b):assert np.allclose(a,b,rtol=0,atol=1e-12),(a,b)
def pairs(rows):
    grouped=defaultdict(dict)
    for row in rows:
        key=row['seed'],row['family_id'];world=row['world']
        assert world not in grouped[key], 'Duplicate paired world'
        grouped[key][world]=bool(row['success'])
    assert all(set(w)=={'authorized','hypothetical'} for w in grouped.values()), 'Incomplete paired family'
    return {k:int(all(v.values())) for k,v in grouped.items()}
def core_contrast(left,right):
    a,b=pairs(left),pairs(right);assert a.keys()==b.keys()
    seeds=sorted({s for s,f in a});families=sorted({f for s,f in a})
    assert len(a)==len(seeds)*len(families)
    delta={(s,f):a[s,f]-b[s,f] for s in seeds for f in families}
    rng=random.Random(90210);draws=[]
    for _ in range(10000):
        ss=rng.choices(seeds,k=len(seeds));ff=rng.choices(families,k=len(families))
        draws.append(statistics.mean(delta[s,f] for s in ss for f in ff))
    draws.sort()
    return statistics.mean(delta.values()),[draws[250],draws[9750]]
def archive_contrast(rows,expected):
    m=expected['metric'];seeds=expected['seeds'];first,second=expected['first'],expected['second']
    values={(r['condition'],int(r['seed']),r['family_id']):int(r[m+'_n'])/int(r[m+'_d'])
        for r in rows if int(r[m+'_d'])>0}
    family_sets=[{f for c,s,f in values if c==condition and s==seed} for seed in seeds for condition in [first,second]]
    families=sorted(set.intersection(*family_sets));assert len(families)==expected['matched_families']
    a=np.array([[values[first,s,f] for f in families] for s in seeds]);b=np.array([[values[second,s,f] for f in families] for s in seeds]);delta=a-b
    rng=np.random.default_rng(400041);fi=rng.integers(0,len(families),(10000,len(families)))
    if len(seeds)==1:draws=delta[0,fi].mean(1)
    else:
        si=rng.integers(0,len(seeds),(10000,len(seeds)));draws=delta[si[:,:,None],fi[:,None,:]].mean((1,2))
    close([a.mean(),b.mean(),delta.mean(),*np.quantile(draws,[.025,.975])],
        [expected[k] for k in ['first_mean','second_mean','difference','lower','upper']])
def strings(obj,path='$'):
    if isinstance(obj,str):yield path,obj
    elif isinstance(obj,list):
        for i,item in enumerate(obj):yield from strings(item,f'{path}[{i}]')
    elif isinstance(obj,dict):
        for key,value in obj.items():yield from strings(value,f'{path}.{key}')
def main():
    outcomes=load('core_outcomes.json');counts=load('core_counts.json');assert len(counts)==38
    for row in counts:
        selected=[r for r in outcomes if all(r[k]==row[k] for k in ['model','condition','seed'])]
        assert len(selected)==480
        pp=pairs(selected);assert len(pp)==240 and sum(pp.values())==row['paired_successes']
        assert sum(r['success'] for r in selected)==row['conversation_successes']
    for expected in load('core_contrasts.json'):
        first,second=expected['comparison'].split('-')
        groups=[[r for r in outcomes if r['model']==expected['model'] and r['condition']==condition] for condition in [first,second]]
        mean,ci=core_contrast(*groups);close(mean,expected['difference']);close(ci,expected['ci95'])
    archive=csvload('archive_family_numerators.csv');assert len(archive)==1350
    assert len({(r['condition'],r['seed'],r['family_id']) for r in archive})==1350
    assert len({r['family_id'] for r in archive})==150
    for e in load('archive_contrasts.json'):archive_contrast(archive,e)
    for row in csvload('archive_counts.csv'):
        m=row['metric'];selected=[r for r in archive if r['condition']==row['condition'] and (row['generator_seed']=='all' or r['seed']==row['generator_seed'])]
        assert sum(int(r[m+'_n']) for r in selected)==int(row['numerator'])
        assert sum(int(r[m+'_d']) for r in selected)==int(row['denominator'])
    families=load('edge_families.json');assert len(families)==96
    assert len({(r['model'],r['condition'],r['family_id'],r['seed']) for r in families})==96
    for row in load('edge_summary.json'):
        selected=[r for r in families if r['model']==row['model'] and r['condition']==row['condition']]
        assert len(selected)==16
        for metric in ['paired_success','edit','recollect','propose','peer','pass','opportunities','repeat_n','repeat_d']:
            assert sum(r[metric] for r in selected)==row[metric],metric
    for e in load('edge_behavior_contrasts.json'):
        first,second=e['comparison'].split('-');m=e['metric'];rows=[r for r in families if r['model']==e['model']]
        lookup={(r['condition'],r['family_id']):r for r in rows};values=[]
        for family in sorted({r['family_id'] for r in rows}):
            a,b=lookup[first,family],lookup[second,family]
            if m=='repeat_n':
                if a['repeat_d'] and b['repeat_d']:values.append(a['repeat_n']/a['repeat_d']-b['repeat_n']/b['repeat_d'])
            else:values.append(a[m]/a['opportunities']-b[m]/b['opportunities'])
        x=np.array(values);rng=np.random.default_rng(900031);samples=x[rng.integers(0,len(x),(10000,len(x)))].mean(1)
        close(x.mean(),e['family_mean_difference']);close(np.quantile(samples,[.025,.975]),e['ci95'])
    calibration=load('calibration.json');assert sum(r['screen_pass'] for r in calibration if r['model']=='phi')==0
    assert sum(r['screen_pass'] for r in calibration if r['model']=='qwen')==3
    for r in calibration:assert sum(x['count'] for x in r['confusion'])==80
    trajectory=load('ambiguity_trajectory.json');assert len(trajectory)==192
    for model in ['qwen','phi']:
        for condition in ['C3','C5','A1']:
            rr=[r for r in trajectory if r['model']==model and r['condition']==condition]
            assert sorted(r['turn'] for r in rr)==list(range(1,33))
            assert all((r['expected_cap'] is None)==(10<=r['turn']<=19) for r in rr)
    manuscript=(P/'manuscript.tex').read_text();quotes=re.findall(r"``(.*?)''",manuscript,re.S)
    provenance=[]
    for quote in quotes:
        matches=[]
        for name in ['selected_edge_records.json','selected_archive_episodes.json']:
            for locator,text in strings(load(name)):
                if quote in text:matches.append({'file':'data/'+name,'json_locator':locator})
        assert matches, 'Quotation absent: '+quote
        provenance.append({'quote':quote,'matches':matches})
    assert len(quotes)==9
    refs=re.findall(r'\\bibitem\{([^}]+)\}',manuscript)
    cited={key for group in re.findall(r'\\cite\{([^}]+)\}',manuscript) for key in group.split(',')}
    assert len(refs)==26 and set(refs)==cited
    abstract=manuscript.split('\\begin{abstract}')[1].split('\\keywords')[0]
    words=len(re.findall(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*",abstract));assert 150<=words<=250
    assert not re.search(r'\\(?:input|include)\{',manuscript)
    assert manuscript.isascii() and '~' not in manuscript
    assert len(re.findall(r'\\includegraphics',manuscript))==4
    for term in ['/home/','file://','mantzaris','github.com/mantzaris']:
        assert term not in manuscript
    scope=json.loads((P/'SCOPE.json').read_text())
    assert hashlib.sha256((P/'svproc.cls').read_bytes()).hexdigest()==scope['template']['class_sha256']
    report={'core_cells':38,'paired_world_rows':len(outcomes),'core_bootstraps_reproduced':10,
        'archive_family_seed_condition_rows':1350,'archive_contrasts_reproduced':72,
        'edge_families_per_backbone':16,'edge_behavior_contrasts_reproduced':20,
        'exact_quotes':len(quotes),'references_all_cited':len(refs),'abstract_words':words,'figures':4,
        'method':'Portable sufficient-statistic reproduction, not an independent raw-archive or semantic validation.'}
    output=P/'.build';output.mkdir(exist_ok=True)
    (output/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    (output/'quote_matches.json').write_text(json.dumps(provenance,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
