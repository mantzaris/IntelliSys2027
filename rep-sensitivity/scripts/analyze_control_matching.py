"""Describe actual matching residuals and admission loss from immutable controls."""
import argparse
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path

p=argparse.ArgumentParser();p.add_argument('run');p.add_argument('output');a=p.parse_args()
root=Path(a.run);output=Path(a.output);output.mkdir(parents=True,exist_ok=True)
config=json.loads((root/'config.json').read_text());accepted=[];missing=[]
for model in config['models']:
    directory=root/model
    rows=[json.loads(p.read_text()) for p in (directory/'scores').glob('*.json')]
    by_pair=defaultdict(list)
    for r in rows:by_pair[r['pair_id']].append(r)
    for path in (directory/'manifests').glob('*.json'):
        expected=json.loads(path.read_text())['trajectories']
        if len(by_pair[path.stem])==expected:accepted.extend(by_pair[path.stem])
        else:missing.append({'model':model,'pair':path.stem})
    if not rows:missing.append({'model':model,'pair':'all'})
observations=defaultdict(list)
cells=defaultdict(dict)
for r in accepted:cells[(r['kind'],r['model'],r['contrast'],r['pair_id'],r['world'],r['repetition'])][r['arm']]=r
def add(kind,model,pid,label,value):observations[(kind,model,label)].append((pid,float(value)))
for (kind,model,contrast,pid,world,rep),arms in cells.items():
    pairs=[]
    if contrast=='packaging':pairs=[('high_overlap','low_overlap','packaging')]
    if contrast=='unique_clause':pairs=[(c+'_high',c+'_low','unique_'+c) for c in ('decisive','harmless')]
    for high,low,label in pairs:
        if high not in arms or low not in arms:continue
        hi,lo=(arms[x]['audit'] for x in (high,low))
        add(kind,model,pid,label+'_report_token_difference_high_minus_low',hi['report_text_tokens']-lo['report_text_tokens'])
        add(kind,model,pid,label+'_report_slot_difference_high_minus_low',hi['report_slots']-lo['report_slots'])
        similarity=lambda x:x['mean_pairwise_similarity'] if contrast=='packaging' else x['rendering_audit']['target_anchor_character_similarity']
        add(kind,model,pid,label+'_character_similarity_difference_high_minus_low',similarity(hi)-similarity(lo))
    if contrast=='length' and 'neutral_padding' in arms:
        for value in arms['neutral_padding']['audit']['full_manager_prompt_token_residual']:
            add(kind,model,pid,'neutral_minus_repeat_manager_prompt_tokens',value)
    if contrast=='branch_placement' and all(x in arms for x in ('same_branch','different_branch')):
        for hi,lo in zip(arms['different_branch']['audit']['branch_report_counts'],arms['same_branch']['audit']['branch_report_counts']):
            add(kind,model,pid,'distinct_scope_branch_absolute_report_load_change',abs(hi-lo))
    if contrast=='deduplication' and 'exact_removal' in arms:
        r=arms['exact_removal'];audit=r['audit']
        for method in ('exact','similarity'):
            add(kind,model,pid,method+'_admission_distinct_claims_lost',audit[method]['distinct_claims_lost'])
            add(kind,model,pid,method+'_admission_fraction_of_required_claims_lost',audit[method]['distinct_claims_lost']/r['required_claims'])
rows=[]
for (kind,model,metric),values in sorted(observations.items()):
    clusters=defaultdict(list)
    for pid,value in values:clusters[pid].append(value)
    means=[sum(v)/len(v) for v in clusters.values()]
    rows.append(dict(kind=kind,model=model,metric=metric,clusters=len(clusters),observations=len(values),
                     cluster_weighted_mean=sum(means)/len(means),minimum=min(v for p,v in values),maximum=max(v for p,v in values)))
if rows:
    with (output/'matching_audit.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
record={'suite':config['name'],'complete':bool(accepted) and not missing,'excluded_or_missing':missing,'summary':rows,
        'source_records_sha256':hashlib.sha256(json.dumps(sorted(accepted,key=lambda r:r['trial_id']),sort_keys=True).encode()).hexdigest(),
        'analysis_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'interpretation':'Descriptive matching residuals; equal weighting of base-cluster means, no inferential intervals. Branch observations and repetitions are not independent samples. Full root lengths depend on generated summaries; only pre-generation report/manager matching is assessed here.'}
(output/'matching_audit.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'suite':config['name'],'complete':record['complete'],'diagnostic_rows':len(rows)}))
