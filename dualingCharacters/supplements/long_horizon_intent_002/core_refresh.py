"""Reuse completed-core CPU analyses without generating a second main manuscript."""
import json
import subprocess
import sys
from pcc.campaign import jobs,resolve_job,load_overrides
from pcc.freeze import verify_freeze
from analysis.overnight.common import ROOT,OUT,CACHE,read,write,utc


def main():
    active=read(ROOT/'artifacts/campaign_state.json',{}).get('active_job',{}).get('id')
    new={'evaluate':[],'fit':[],'collect':[]}
    for original in jobs(verify_freeze(ROOT)['plan']):
        job=resolve_job(original,load_overrides(ROOT));command=job['command']
        if command not in new or job['id']==active:continue
        if read(ROOT/'artifacts/runs'/job['id']/'status.json',{}).get('status')!='completed':continue
        folder={'evaluate':'evaluations','fit':'exposure','collect':'collections'}[command]
        suffix='.validation.json' if command=='evaluate' else '.json'
        if not (CACHE/folder/(job['id']+suffix)).exists():new[command].append(job['id'])
    if not any(new.values()):print({'changed':False,'reason':'No new completed core inputs'});return
    if new['evaluate']:
        from analysis.overnight.results import generate
        generate()
    if new['fit']:
        from analysis.overnight.exposure import main as exposure
        exposure()
    if new['collect']:
        from analysis.overnight.collections import main as collections
        collections()
    from analysis.overnight.associations import main as associations
    from analysis.overnight.lineage import main as lineage
    from analysis.overnight.compute import main as compute
    associations();lineage();compute()
    if new['evaluate'] or new['fit']:
        from analysis.overnight.plots import main as plots
        plots()
    if new['fit']:
        from analysis.overnight.training_curves import main as curves
        curves()
    subprocess.run([sys.executable,str(ROOT/'analysis/execution_report.py')],cwd=ROOT,check=True)
    write(OUT/'LAST_INCREMENTAL_UPDATE.json',{'utc':utc(),'new_completed_inputs':new,'classification':'Existing frozen core evidence, not fresh intent scores'})
    print(json.dumps({'new_completed_core':new}))


if __name__=='__main__':main()
