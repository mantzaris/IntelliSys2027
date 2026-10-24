"""Update only when new completed evidence exists; never launch model calls."""
import argparse
import json
import subprocess
import sys
from pcc.campaign import jobs,resolve_job,load_overrides
from pcc.freeze import verify_freeze
from .common import ROOT,OUT,CACHE,read,write,utc


def main(force=False):
    queue=[resolve_job(j,load_overrides(ROOT)) for j in jobs(verify_freeze(ROOT)['plan'])]
    new={'evaluate':[],'fit':[],'collect':[]}
    for job in queue:
        if read(ROOT/'artifacts/campaign_state.json',{}).get('active_job',{}).get('id')==job['id']:continue
        command=job['command'];path=ROOT/f'artifacts/runs/{job["id"]}/status.json'
        if command not in new or not path.exists() or read(path)['status']!='completed':continue
        directory={'evaluate':'evaluations','fit':'exposure','collect':'collections'}[command]
        suffix='.validation.json' if command=='evaluate' else '.json'
        if not (CACHE/directory/(job['id']+suffix)).exists():new[command].append(job['id'])
    if not any(new.values()) and not force:
        print(json.dumps({'changed':False,'reason':'No newly completed inputs; unchanged audits/figures skipped'}));return
    if new['evaluate'] or force:
        from .results import generate
        generate()
    if new['fit'] or force:
        from .exposure import main as exposure
        exposure()
    if new['collect'] or force:
        from .collections import main as collections
        collections()
    if new['evaluate'] or new['fit'] or force:
        from .plots import main as plots
        from .draft import main as draft
        plots();draft()
    write(OUT/'LAST_INCREMENTAL_UPDATE.json',{'utc':utc(),'new_completed_inputs':new,'forced':force})
    print(json.dumps({'changed':True,'new':new}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--force',action='store_true');main(p.parse_args().force)
