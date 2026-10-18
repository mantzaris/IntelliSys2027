"""Descriptive manuscript breakdowns from complete main outputs, CPU only."""
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from rep_sensitivity.analysis import bootstrap, repetition_values
from analyze_main_transitions import read_rows


def mean(values):
    values=list(values)
    return sum(values)/len(values)


def main():
    source=Path('results/main-v7/decisions.csv')
    rows=read_rows(source)
    original=json.load(open('results/main-v7/analysis.json'))
    assert original['complete'] and len(rows)==original['planned_trajectories']
    absolute=[];effects=[];pair_success=[]
    for kind in ('schedule','workflow'):
        for model in ('qwen3','phi4'):
            for org in ('both','flat','hierarchical'):
                for policies in [('ordinary','checklist','scope'),('ordinary','checklist'),('ordinary',),('checklist',),('scope',)]:
                    selected=[r for r in rows if r['kind']==kind and r['model']==model
                              and (org=='both' or r['organization']==org) and r['policy'] in policies]
                    context=dict(kind=kind,model=model,organization=org,policies='+'.join(policies))
                    strata={r['pair_id']:(r['family'],r['decision_changed']) for r in selected}
                    for condition in ('single','exact','paraphrase'):
                        arms=[r for r in selected if r['condition']==condition]
                        by_base=defaultdict(list)
                        for r in arms: by_base[r['pair_id']].append(int(r['correct']))
                        values={p:mean(v) for p,v in by_base.items()}
                        absolute.append({**context,'condition':condition,'trajectories':len(arms),
                            'correct':sum(r['correct'] for r in arms),'accuracy':bootstrap(values,strata),
                            'input_tokens':sum(int(r['input_tokens']) for r in arms),
                            'output_tokens':sum(int(r['output_tokens']) for r in arms),
                            'inference_seconds':sum(float(r['inference_seconds_allocated']) for r in arms),
                            'output_failures':sum(r['operational_failure'] for r in arms)})
                    for condition in ('exact','paraphrase'):
                        values={p:-v for p,v in repetition_values(selected,condition).items()}
                        effects.append({**context,'condition':condition,**bootstrap(values,strata),'base_effects':values})
                    if org!='both' or len(policies)!=3: continue
                    for change in (False,True):
                        cells=defaultdict(dict)
                        for r in selected:
                            if r['decision_changed']!=change:continue
                            key=tuple(r[k] for k in ('pair_id','organization','policy','repetition'))
                            cells[key].setdefault(r['condition'],{})[r['world']]=r['correct']
                        n=len(cells);base=defaultdict(lambda:defaultdict(list))
                        for key,arms in cells.items():
                            for cond,worlds in arms.items():
                                assert set(worlds)=={0,1}
                                base[key[0]][cond].append(int(all(worlds.values())))
                        rates={p:{c:mean(v) for c,v in arms.items()} for p,arms in base.items()}
                        for condition in ('exact','paraphrase'):
                            diff={p:a[condition]-a['single'] for p,a in rates.items()}
                            pair_success.append({**context,'condition':condition,'decision_changed':change,
                                'paired_cells_per_condition':n,'base_pairs':len(rates),
                                'single':mean(v['single'] for v in rates.values()),
                                'repeated':mean(v[condition] for v in rates.values()),**bootstrap(diff,strata)})
    out=Path('results/manuscript-main-v7');out.mkdir(exist_ok=True)
    result={'complete':True,'status':'descriptive breakdowns of frozen complete main; no new outcomes',
      'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
      'analysis_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
      'method':'Same whole-base family-by-change bootstrap as main, 10000 draws. Subgroup contrasts are descriptive and pointwise, not additional prespecified primary tests.',
      'absolute':absolute,'effects':effects,'paired_success':pair_success}
    (out/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'absolute_cells':len(absolute),'effects':len(effects),'paired_success':len(pair_success)}))


if __name__=='__main__': main()
