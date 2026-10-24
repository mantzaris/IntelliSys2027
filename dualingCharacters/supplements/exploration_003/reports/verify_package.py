"""Check compact result/provenance invariants without new scientific estimates."""
from collections import Counter,defaultdict
from pathlib import Path
import csv
import json
import re
import statistics
from supplements.exploration_003.common import ROOT,HERE,REPORTS,CACHE,read,write,sha256,utc,verified_stream
from supplements.exploration_003.analysis import verify_science


def rows(name):
    with (REPORTS/name).open() as f:return list(csv.DictReader(f))


def paired_means(records,field):
    pairs={}
    for row in records:
        key=row['family_id'],row['world']
        if key in pairs:raise ValueError('Duplicate paired observation')
        pairs[key]=float(row[field])
    families=defaultdict(dict)
    for (family,world),value in pairs.items():families[family][world]=value
    if any(set(worlds)!={'authorized','hypothetical'} for worlds in families.values()):
        raise ValueError('Incomplete paired-world coverage')
    return {family:statistics.mean(worlds.values()) for family,worlds in families.items()}


def main():
    science=verify_science()
    # These compact order manifests are ignored derived artifacts. Rebuild only
    # absent copies from the exact locked raw stream; never rewrite a mismatch.
    for cell in read(HERE/'DATA_AUDIT.json')['included_cells']:
        path=ROOT/cell['order_manifest']
        if not path.exists():
            observed=defaultdict(list)
            name=next((n for n in cell['raw_hashes'] if n.startswith(cell['prefix']+'_characters.jsonl')),None)
            if name:
                raw=ROOT/'artifacts/runs'/cell['run_id']/name
                for action in verified_stream(raw,cell['raw_hashes'][name]):
                    observed[action['family_id'],action['world']].append(action)
            order=[{'family_id':family,'world':world,'turns':[a['turn'] for a in observed[family,world]],
                    'actors':[a['actor'] for a in observed[family,world]]}
                   for family in sorted(cell['family_ids']) for world in ('authorized','hypothetical')]
            write(path,order)
        if sha256(path)!=cell['order_manifest_sha256']:raise ValueError('Actual action-order manifest mismatch')
    episodes=rows('primary_episode_metrics.csv')
    by_condition={c:paired_means([r for r in episodes if r['condition']==c],'coverage')
                  for c in sorted({r['condition'] for r in episodes})}
    if any(len(v)!=8 for v in by_condition.values()):raise ValueError('Unexpected pilot family count')
    primary=next(r for r in read(REPORTS/'primary_paired_contrasts.json') if r.get('budget')==12 and r['metric']=='coverage')
    difference=statistics.mean(by_condition['C5'][f]-by_condition['C3'][f] for f in by_condition['C5'])
    if difference!=primary['difference']:raise ValueError('Primary result does not match episode table')
    for name in ('REPORT_PROVENANCE.json','FIGURE_PROVENANCE.json'):
        document=read(REPORTS/name)
        for relative,digest in document.get('outputs',{}).items():
            if sha256(HERE/relative)!=digest:raise ValueError('Output provenance mismatch: '+relative)
        for relative,digest in document.get('figures',{}).items():
            if sha256(REPORTS/'figures'/relative)!=digest:raise ValueError('Figure provenance mismatch: '+relative)
    v1=CACHE/'human_review/reviewer';v2=CACHE/'human_review/reviewer_v2'
    if sha256(v1/'items.json')!=sha256(v2/'items.json'):raise ValueError('Review trajectories changed between presentation versions')
    items=read(v2/'items.json');ids=[r['item_id'] for r in items]
    if len(ids)!=56 or len(set(ids))!=56:raise ValueError('Review sample duplicated or incomplete')
    if re.search(r'\b(?:C[1-6]|A[1-3]|Jekyll|Hyde|Rival|Traditionalist|Provocateur)\b',(v2/'items.json').read_text()):
        raise ValueError('Identifying study labels remain in reviewer items')
    annotations={}
    for rater in (1,2):
        with (v2/f'rater_{rater}.csv').open() as f:ratings=list(csv.DictReader(f))
        if [r['item_id'] for r in ratings]!=ids:raise ValueError('Rating identities changed')
        annotations[str(rater)]=sum(any(v.strip() for k,v in r.items() if k!='item_id') for r in ratings)
    private=read(CACHE/'human_review/private/mapping.json');counts=Counter(r['cell'].split('__')[-1] for r in private)
    if set(counts.values())!={8}:raise ValueError('Review condition balance changed')
    costs=rows('run_cost_reconciliation.csv')
    for row in costs:
        for field in ('model_calls','input_tokens','output_tokens'):
            if int(row['rollout_'+field])+int(row['outside_rollout_'+field])!=int(row['ledger_'+field]):raise ValueError('Cost totals fail reconciliation')
    result={'verified_utc':utc(),'prior_frozen_files':113,'exploration_frozen_files':len(science['files']),
        'primary_paired_difference_recomputed_from_episode_table':difference,'pilot_conditions':len(by_condition),
        'paired_families_per_condition':8,'reconciled_runs':len(costs),'review_items':len(items),
        'review_annotation_rows':annotations,'new_gpu_calls':0,'new_model_judge_calls':0,
        'qualification':'Presentation/provenance verification only; no new analysis population or semantic labels.'}
    write(REPORTS/'PACKAGE_VERIFICATION.json',result);print(result)


if __name__=='__main__':main()
