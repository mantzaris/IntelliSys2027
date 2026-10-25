"""Independent accounting and provenance checks; does not add scientific metrics."""
from collections import Counter,defaultdict
import csv
import json
import re
from .common import *
from .reporting import rows

def run():
    science=verify_science();amendment_files=0
    for name in ('AMENDMENT_001_MANIFEST.json','AMENDMENT_002_MANIFEST.json','AMENDMENT_003_MANIFEST.json'):
        manifest=read(HERE/name)
        if manifest['original_manifest_sha256']!=sha256(HERE/'SCIENTIFIC_MANIFEST.json'):raise ValueError('Amendment ancestry mismatch')
        for path,digest in manifest['files'].items():
            if sha256(HERE/path)!=digest:raise ValueError('Amended file changed')
        amendment_files+=len(manifest['files'])
    audit=read(HERE/'DATA_AUDIT.json');summary=rows('metric_summary.csv');by_key={(r['cohort'],r['condition'],r['seed'],r['metric']):r for r in summary}
    if len(by_key)!=len(summary):raise ValueError('Duplicate summary key')
    for cell in audit['cells']:
        prefix=(cell['cohort'],cell['condition'],str(cell['seed']))
        expected=cell['families']*2*cell['opportunities_per_episode']
        channels=[r for key,r in by_key.items() if key[:3]==prefix and key[-1].startswith('channel_')]
        if sum(int(r['numerator']) for r in channels)!=expected:raise ValueError('Channels omit or double-count opportunities')
        if any(int(r['denominator'])!=expected for r in channels):raise ValueError('Allocated denominator wrong')
        for field in ('edit','recollect','propose'):
            r=by_key[*prefix,'available_channel_'+field]
            if int(r['denominator'])!=(expected*2//3):raise ValueError('Available denominator wrong')
        order=ROOT/cell['action_order_path']
        if sha256(order)!=cell['action_order_sha256']:raise ValueError('Locked schedule artifact changed')
    for row in rows('ACTION_CHAIN.csv'):
        n=int(row['allocated_with_this_channel'])
        for field in ('valid','applied','state_changed','evidence_changed','notes_changed'):
            if sum(int(row[field+'_'+v]) for v in ('yes','no','missing'))!=n:raise ValueError('Chain branch denominator mismatch')
        if sum(int(row['following_adoption_'+v]) for v in ('same','different','unknown_value','missing'))!=n:raise ValueError('Following-answer missingness lost')
    for row in rows('run_cost_reconciliation.csv'):
        for field in ('input_tokens','output_tokens','calls'):
            if int(row['collection_'+field])+int(row['residual_'+field])!=int(row['recorded_model_'+field]):raise ValueError('Cost reconciliation failure')
            if int(row['residual_'+field])<0:raise ValueError('Negative cost residual')
    joins=rows('supervision_join_v2.csv');corrected=[r for r in joins if r['collection_id']=='main-qwen-c1-17-r1-collect-format2__C1']
    if len(corrected)!=1 or corrected[0]['run_id']!='main-qwen-c1-17-r1-fit-format2':raise ValueError('Legacy exposure linkage remains wrong')
    if sum(r['exposure_audit_status']=='verified_existing' for r in joins)!=24:raise ValueError('Exposure join completeness changed')
    paired=rows('secondary_paired_transitions.csv')
    for row in paired:
        if sum(int(row[k]) for k in ('both','only_C5','only_control','neither'))!=int(row['families']):raise ValueError('Secondary pair table incomplete')
        difference=(int(row['only_C5'])-int(row['only_control']))/int(row['families'])
        if abs(difference-float(row['difference']))>1e-12:raise ValueError('Paired transition difference wrong')
    # Every primary point estimate is independently recovered from retained family rates.
    with (CACHE/'family_rates.csv').open() as f:family_rows=list(csv.DictReader(f))
    values={(r['cohort'],r['condition'],int(r['seed']),r['family_id'],r['metric']):float(r['rate']) for r in family_rows if r['rate']}
    by_population=defaultdict(set)
    for cohort,condition,seed,family,metric in values:by_population[cohort,condition,seed,metric].add(family)
    for r in read(REPORTS/'matched_contrasts.json'):
        if r['difference'] is None:continue
        possible=[by_population[r['cohort'],condition,seed,r['metric']] for seed in r['seeds'] for condition in (r['first'],r['second'])]
        families=set.intersection(*possible)
        delta=sum(values[r['cohort'],r['first'],seed,f,r['metric']]-values[r['cohort'],r['second'],seed,f,r['metric']] for seed in r['seeds'] for f in families)/(len(families)*len(r['seeds']))
        if len(families)!=r['matched_families'] or abs(delta-r['difference'])>1e-12:raise ValueError('Paired mean does not match family table')
    # Provenance for tables, figures and generated prose.
    for name in ('PRESENTATION_PROVENANCE.json','FIGURE_PROVENANCE.json','NARRATIVE_PROVENANCE.json'):
        p=read(REPORTS/name)
        for path,digest in p['inputs'].items():
            if sha256(REPORTS/path)!=digest:raise ValueError('Presentation input changed')
        for path,digest in p.get('outputs',{}).items():
            root=HERE if name=='NARRATIVE_PROVENANCE.json' else REPORTS
            if sha256(root/path)!=digest:raise ValueError('Presentation output changed')
        for path,digest in p.get('files',{}).items():
            if sha256(REPORTS/'figures'/path)!=digest:raise ValueError('Figure changed')
    status=read(REPORTS/'SEMANTIC_REVIEW_STATUS.json');directory=ROOT/status['reviewer_directory'];items=read(directory/'items.json');ids=[r['item_id'] for r in items]
    if len(ids)!=24 or len(set(ids))!=24:raise ValueError('Review item duplication or missingness')
    if re.search(r'\b(?:C[1-6]|A[1-3]|Jekyll|Hyde|Rival|Traditionalist|Provocateur|Generic)\b',(directory/'items.json').read_text()):raise ValueError('Condition label remains in reviewer data')
    annotations={}
    for number in (1,2):
        path=directory/f'rater_{number}.csv'
        with path.open() as f:form=list(csv.DictReader(f))
        if [r['item_id'] for r in form]!=ids:raise ValueError('Review form identities changed')
        annotations[number]=sum(any(v.strip() for k,v in r.items() if k!='item_id') for r in form)
        if sha256(path)!=status['reviewer_files'][path.name]:raise ValueError('Review forms changed since preparation; preserve and audit annotations')
    prior=read(REPORTS/'REVIEW_PRESENTATION_PROVENANCE.json')
    for path,digest in prior['prior_v2_files_preserved'].items():
        if sha256(ROOT/path)!=digest:raise ValueError('Prior reviewer-v2 file changed')
    results=read(REPORTS/'RESULTS_PROVENANCE.json')
    if results['queue_mismatches']!=0 or results['new_gpu_calls']!=0 or results['new_judge_calls']!=0:raise ValueError('Unexpected observation or execution status')
    write(REPORTS/'PACKAGE_VERIFICATION.json',{'verified_utc':utc(),'prior_scientific_files_unchanged':127,
        'new_original_scientific_files_unchanged':len(science['files']),'amendment_files_verified':amendment_files,
        'cells':len(audit['cells']),'all_opportunities_reconciled':True,'all_point_estimates_recomputed':True,
        'costs_reconciled':True,'verified_existing_exposure_fits':24,'new_review_items':24,'human_annotation_rows':annotations,
        'prior_review_versions_preserved':True,'new_gpu_calls':0,'new_model_judge_calls':0})
    print('Verified prior freezes, new scientific versions, counts, point estimates, costs, figures and review identities.')

if __name__=='__main__':run()
