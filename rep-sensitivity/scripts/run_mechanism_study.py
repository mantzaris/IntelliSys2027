"""Dated extension, interleaved only after the active original model stage finishes."""
import argparse
import fcntl
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from rep_sensitivity.schema import digest
from rep_sensitivity.storage import immutable_json,utcnow
from rep_sensitivity.targeted_replay import run
from rep_sensitivity.targeted_analysis import summarize,planning
from rep_sensitivity.fresh_probe import run as run_fresh
from rep_sensitivity.fresh_analysis import summarize as summarize_fresh


def read(path):return json.loads(Path(path).read_text())


def wait_for_idle_gpu():
    deadline=time.monotonic()+300
    while subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip():
        if time.monotonic()>deadline:raise RuntimeError('GPU occupied after completed stage; no process interrupted')
        time.sleep(5)


def publish(config,evidence):
    config={**config,'status':'frozen'}
    immutable_json(Path('records/freezes')/(config['name']+'.json'),{
        'frozen_utc':utcnow(),'config_sha256':digest(config),'amendment':'mechanism-v1','evidence':evidence,
        'source_sha256':digest({p.name:p.read_text() for p in (Path(__file__).parent/'rep_sensitivity').glob('*.py')}),
        'registration':'Prospective repository freeze; no external registration.'})
    immutable_json(Path('configs/frozen')/(config['name']+'.json'),config)
    return config


def frozen_or_publish(config,evidence):
    path=Path('configs/frozen')/(config['name']+'.json')
    return read(path) if path.exists() else publish(config,evidence)


def extension(templates):
    for package,version in [('vllm','0.10.2'),('transformers','4.55.4')]:
        if importlib.metadata.version(package)!=version:raise RuntimeError('Changed inference environment')
    dev=read('configs/frozen/mechanism-development-v1.json')
    source=digest({p.name:p.read_text() for p in (Path(__file__).parent/'rep_sensitivity').glob('*.py')})
    for name in ('mechanism-development-v1','fresh-probe-v1'):
        if read(Path('records/freezes',name+'.json'))['source_sha256']!=source:
            raise RuntimeError('Execution snapshot differs from extension freeze')
    model=run(dev);result=summarize('artifacts/runs/'+dev['name'],'results/'+dev['name'])
    if not result['complete']:raise RuntimeError('Incomplete targeted development')
    fresh=read('configs/frozen/fresh-probe-v1.json');model=run_fresh(fresh,model)
    summarize_fresh('artifacts/runs/'+fresh['name'],'results/'+fresh['name'])
    rule=read(Path(templates)/'mechanism-allocation-v1.json')
    val={**dev,**rule['validation'],'name':'mechanism-validation-v1','phase':'validation','targeted_subset_indices':[]}
    val=frozen_or_publish(val,{'development_analysis_sha256':digest(result),'allocation_rule_sha256':digest(rule)})
    model=run(val,model);validation=summarize('artifacts/runs/'+val['name'],'results/'+val['name'])
    decision=planning('artifacts/runs/'+val['name'],rule)
    immutable_json('records/planning/mechanism-v1.json',decision)
    if not decision['eligible_to_launch']:
        immutable_json('artifacts/runs/mechanism-execution/heldout-not-launched.json',{'utc':utcnow(),'reason':decision,
            'action':'Preserve development/validation and continue original study. No gate relaxation.'})
        return
    main={**dev,'split':rule['heldout']['split'],'pair_start':rule['heldout']['pair_start'],
          'base_pairs':decision['selected_base_pairs'],'name':'mechanism-heldout-v1','phase':'heldout','targeted_subset_indices':[]}
    main=frozen_or_publish(main,{'validation_analysis_sha256':digest(validation),'allocation':decision,
                               'analysis_manifest_sha256':digest(read(Path(templates)/'mechanism-analysis-v1.json'))})
    run(main,model);summarize('artifacts/runs/'+main['name'],'results/'+main['name'])


def main():
    p=argparse.ArgumentParser();p.add_argument('--templates',required=True);p.add_argument('--after-pid',type=int)
    p.add_argument('--original-snapshot',required=True);p.add_argument('--replay-snapshot',required=True)
    p.add_argument('--stage',choices=['all','extension'],default='all');a=p.parse_args()
    records=Path('artifacts/runs/mechanism-execution');records.mkdir(parents=True,exist_ok=True)
    if a.stage=='extension':extension(a.templates);return
    while a.after_pid:
        try:
            os.kill(a.after_pid,0)
            command=Path('/proc',str(a.after_pid),'cmdline').read_bytes()
            if b'runner.py' not in command:break
        except (ProcessLookupError,FileNotFoundError):break
        time.sleep(5)
    old_records=Path('artifacts/runs/study-execution-v8')
    if not (old_records/'primary_replay_and_live-complete.json').exists():
        raise RuntimeError('Original primary stage did not complete; do not interrupt or bypass it')
    lock=(records/'.controller.lock').open('a')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    extension_args=[sys.executable,__file__,'--templates',a.templates,'--original-snapshot',a.original_snapshot,
                    '--replay-snapshot',a.replay_snapshot,'--stage','extension']
    if not (records/'extension-stage.json').exists():
        wait_for_idle_gpu()
        with Path('logs/mechanism-extension-v1.log').open('a') as log:
            outcome=subprocess.run(extension_args,stdout=log,stderr=subprocess.STDOUT)
        if outcome.returncode==0:
            immutable_json(records/'extension-stage.json',{'returncode':0,'completed':True,
                'note':'Held-out eligibility is separately recorded; completion is not human scientific review.'})
        else:
            immutable_json(records/('extension-failure-'+str(time.time_ns())+'.json'),
                           {'utc':utcnow(),'returncode':outcome.returncode,'action':'Preserve checkpoints and continue original frozen second family.'})
    # A new-extension failure must not suppress the original frozen second family.
    old=Path(a.original_snapshot)
    env=dict(os.environ,PYTHONPATH=str(old.resolve()))
    if not (old_records/'secondary_replay_and_live-complete.json').exists():
        wait_for_idle_gpu()
        with Path('logs/mechanism-original-secondary.log').open('a') as log:
            outcome=subprocess.run([sys.executable,str(old/'runner.py'),'--templates',str(old/'configuration'),
                 '--replay-snapshot',a.replay_snapshot,'--stage','secondary_replay_and_live'],env=env,stdout=log,stderr=subprocess.STDOUT)
        if outcome.returncode!=0:
            immutable_json(records/('secondary-failure-'+str(time.time_ns())+'.json'),{'utc':utcnow(),'returncode':outcome.returncode})
            raise RuntimeError('Original secondary stage stopped; immutable checkpoints retained')
        immutable_json(old_records/'secondary_replay_and_live-complete.json',{'stage':'secondary_replay_and_live','complete':True})
    immutable_json(records/'original-secondary-stage.json',{'returncode':0,'completed':True})


if __name__=='__main__':main()
