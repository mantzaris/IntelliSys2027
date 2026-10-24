"""Small-metadata check of all completed adapter continuations, irrespective of scores."""
from pcc.campaign import jobs,resolve_job,load_overrides
from pcc.freeze import verify_freeze
from pcc.resources import sha256
from .common import ROOT,OUT,read,write


def main():
    overrides=load_overrides(ROOT)
    queue=[resolve_job(j,overrides) for j in jobs(verify_freeze(ROOT)['plan'])]
    resume_by_run={entry['run_id']:entry.get('checkpoint') for entry in overrides.values()}
    active=read(ROOT/'artifacts/campaign_state.json',{}).get('active_job',{}).get('id')
    rows=[];inputs={}
    for job in queue:
        if job['command'] not in {'fit','evaluate'} or job['id']==active:continue
        status_path=ROOT/f'artifacts/runs/{job["id"]}/status.json';status=read(status_path,{})
        if status.get('status')!='completed':continue
        inputs[str(status_path.relative_to(ROOT))]=sha256(status_path)
        report=None
        if job['command']=='fit':
            report_path=status_path.parent/'training/training_summary.json';report=read(report_path)
            inputs[str(report_path.relative_to(ROOT))]=sha256(report_path)
        predecessor=job.get('adapter');expected=None
        if predecessor:
            previous_report=ROOT/predecessor
            previous_report=previous_report.parent/'training_summary.json'
            previous=read(previous_report);inputs[str(previous_report.relative_to(ROOT))]=sha256(previous_report)
            expected=previous['final_checksums']['adapter_model.safetensors']
            actual=report['initial_checksums']['adapter_model.safetensors'] if report else status['loaded_adapter_sha256']
            if actual!=expected:raise ValueError('Adapter lineage mismatch: '+job['id'])
        rows.append({'run_id':job['id'],'model':job['model'],'condition':job['condition'],'seed':job['seed'],
          'task':job['command'],'predecessor_adapter':predecessor,'expected_predecessor_sha256':expected,
          'continuation_verified':True if predecessor else None,
          'initial_adapter_sha256':report['initial_checksums']['adapter_model.safetensors'] if report else None,
          'final_adapter_sha256':report['final_checksums']['adapter_model.safetensors'] if report else status.get('loaded_adapter_sha256'),
          'optimizer_steps':report['optimizer_steps'] if report else None,
          'completion_serialization':report.get('completion_serialization') if report else None})
        rows[-1]['optimizer_resume_checkpoint']=resume_by_run.get(job['id'])
        rows[-1]['effective_optimizer_resume_chain']='requires separate checkpoint evidence' if resume_by_run.get(job['id']) else 'not resumed'
    write(OUT/'ADAPTER_LINEAGE.json',{'runs':rows,'input_hashes':inputs,
      'qualification':'All completed scheduled fit/evaluation metadata checked without score selection. Actual final-weight bytes are separately verified in MIRROR_CHECKS.json; this check follows predecessor-to-initial and final-to-evaluation references. The trainer saves initial weights before any optimizer resume, so a resumed effective checkpoint chain needs separate evidence and is explicitly flagged. Running stages are excluded until final mirroring completes.'})
    print({'lineage_runs':len(rows),'verified_continuations':sum(r['continuation_verified'] is True for r in rows)})


if __name__=='__main__':main()
