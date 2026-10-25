"""Correct the legacy format2 naming join using exact verified supervision paths."""
from .common import *
from .secondary import csv_rows

def run():
    verify_science()
    for name,digest in read(HERE/'AMENDMENT_002_MANIFEST.json')['files'].items():
        if sha256(HERE/name)!=digest:raise ValueError('Amendment source changed')
    sources=read(HERE/'SECONDARY_SOURCES.json')['files']
    provenance_path='supplements/long_horizon_intent_002/reports/exposure_provenance.json'
    table_path='supplements/long_horizon_intent_002/reports/supervision_exposure.csv'
    for name in (provenance_path,table_path):
        if sha256(ROOT/name)!=sources[name]:raise ValueError('Locked secondary source changed')
    provenance=read(ROOT/provenance_path);index={r['run_id']:r for r in csv_rows(ROOT/table_path)};rows=[]
    for cell in read(HERE/'DATA_AUDIT.json')['cells']:
        if not cell['cohort'].startswith('main_'):continue
        expected='artifacts/runs/'+cell['run_id']+'/supervision.jsonl'
        matches=[run_id for run_id,record in provenance['runs'].items() if expected in record['inputs']]
        if len(matches)>1:raise ValueError('Ambiguous exposure reconstruction')
        row={'collection_id':cell['id'],'condition':cell['condition'],'seed':cell['seed'],'round':cell['round'],
            'exposure_audit_status':'verified_existing' if matches else 'not_reconstructed_at_prior_cutoff'}
        if matches:
            run_id=matches[0];digest=provenance['runs'][run_id]['inputs'][expected]
            if sha256(ROOT/expected)!=digest:raise ValueError('Supervision bytes differ')
            match=index[run_id]
            if match['condition']!=cell['condition'] or int(match['seed'])!=cell['seed']:raise ValueError('Exposure identity mismatch')
            row.update({k:match[k] for k in ('run_id','training_input_tokens','supervised_target_tokens','loss_contributing_unique_windows','loss_contributing_unique_families','orphaned_target_tokens_masked','resume_replay_input_tokens_not_optimized','label_sources_contributing_loss')})
            row['verified_supervision_path']=expected;row['supervision_sha256']=digest
        rows.append(row)
    write_csv(REPORTS/'supervision_join_v2.csv',rows)
    write(REPORTS/'EXPOSURE_JOIN_V2_PROVENANCE.json',{'original_join_preserved':'reports/supervision_join.csv',
        'source_report_hashes':{n:sources[n] for n in (provenance_path,table_path)},'joined_fits':sum(r['exposure_audit_status']=='verified_existing' for r in rows),
        'missing_fits':[r['collection_id'] for r in rows if r['exposure_audit_status']!='verified_existing'],
        'output_sha256':sha256(REPORTS/'supervision_join_v2.csv'),'no_new_reconstruction':True})

if __name__=='__main__':run()
