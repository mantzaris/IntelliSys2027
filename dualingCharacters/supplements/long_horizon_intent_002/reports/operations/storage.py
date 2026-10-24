"""Read-only size projection for the unchanged queue; never deletes artifacts."""
from pathlib import Path
from pcc.campaign import jobs,resolve_job,load_overrides
from pcc.freeze import verify_freeze
from pcc.resources import sha256
from supplements.long_horizon_intent_002.common import ROOT,REPORTS,read,write,utc


def main():
    queue=[resolve_job(j,load_overrides(ROOT)) for j in jobs(verify_freeze(ROOT)['plan'])]
    fits=[j for j in queue if j['command']=='fit'];completed=[]
    for job in fits:
        folder=ROOT/'artifacts/runs'/job['id'];status=folder/'status.json'
        if read(status,{}).get('status')!='completed':continue
        inodes={};files=[]
        for path in sorted((folder/'training').rglob('*')):
            if not path.is_file():continue
            info=path.stat();inodes[(info.st_dev,info.st_ino)]=info.st_size
            files.append({'path':str(path.relative_to(ROOT)),'size_bytes':info.st_size})
        completed.append({'run_id':job['id'],'status_sha256':sha256(status),'unique_inode_bytes':sum(inodes.values()),'files':files})
    live=read(REPORTS/'LATEST_STATE.json');largest=max((r['unique_inode_bytes'] for r in completed),default=0);remaining=len(fits)-len(completed)
    result={'generated_utc':utc(),'monitor_utc':live['utc'],'monitor_sha256':sha256(REPORTS/'LATEST_STATE.json'),
      'completed_fits':len(completed),'remaining_fits':remaining,'largest_completed_fit_bytes':largest,
      'remaining_fit_size_projection_bytes':largest*remaining,'local_free_bytes':live['local_free_bytes'],'remote_free_bytes':live['remote']['free_bytes'],
      'local_after_projected_fits_bytes':live['local_free_bytes']-largest*remaining,'remote_after_projected_fits_bytes':live['remote']['free_bytes']-largest*remaining,
      'qualification':'Maximum observed completed fit size times remaining unchanged fit count; excludes future traces, caches, temporary writes and filesystem overhead. An operational extrapolation, not guaranteed capacity or a cleanup authorization. Shared inodes counted once within each fit. No artifact was deleted.',
      'existing_local_stage_gate':'Core controller stops before a new stage if local free space is below 3 GiB; no new remote gate is asserted.',
      'inputs':completed,'source_sha256':sha256(Path(__file__)),'reproduction_command':'PYTHONPATH=src .venv/bin/python -m supplements.long_horizon_intent_002.reports.operations.storage'}
    write(REPORTS/'STORAGE_PROJECTION.json',result)
    print({k:result[k] for k in ('completed_fits','remaining_fits','remaining_fit_size_projection_bytes','local_free_bytes','remote_free_bytes')})


if __name__=='__main__':main()
