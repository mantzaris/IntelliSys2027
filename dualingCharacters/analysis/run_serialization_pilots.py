"""Serialized repair gates on existing pilot-only collections; no test selection."""
from pathlib import Path
import fcntl
import json
import os
import shlex
import subprocess
import time
from pcc.campaign import run_and_mirror
from pcc.storage import compact_completed,deduplicate_completed

root=Path.cwd();remote='/workspace/dualingCharacters'
ssh=['ssh','-F','/dev/null','-i',str(Path.home()/'.ssh/id_rsa'),'-p',os.environ['PCC_SSH_PORT'],'-o','BatchMode=yes','-o','IdentitiesOnly=yes','-o','StrictHostKeyChecking=yes','-o','UserKnownHostsFile=/tmp/intellisys-runpod-known-hosts',f"root@{os.environ['PCC_SSH_HOST']}"]
lock=(root/'artifacts/campaign.lock').open('a+')
while True:
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);break
    except BlockingIOError:time.sleep(15)
# Main hold remains installed throughout all repair pilots.
if not (root/'artifacts/campaign_boundary_hold.json').exists():raise PermissionError('Repair requires a held main queue')
subprocess.run(['bash','scripts/sync.sh','push'],check=True)
commit=subprocess.run(['git','rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip()
logs=root/'artifacts/serialization_pilots';logs.mkdir(exist_ok=True)
base=['env','PYTHONPATH=src',f'HF_HOME={remote}/artifacts/hf-cache',f'PCC_CODE_COMMIT={commit}','VLLM_WORKER_MULTIPROC_METHOD=spawn']
command='cd '+shlex.quote(remote)+' && '+shlex.join(['env','CUDA_VISIBLE_DEVICES=','PYTHONPATH=src','.venv-infer/bin/python','analysis/audit_serialization.py'])
with (logs/'grammar.log').open('a') as out:subprocess.run(ssh+[command],stdout=out,stderr=subprocess.STDOUT,check=True)
subprocess.run(['bash','scripts/sync.sh','pull'],check=True)
for model,condition in [('qwen','c3'),('qwen','c5'),('phi','c5')]:
    stem=f'pilot-format2-{model}-{condition}'
    jobs=[(stem+'-fit',['.venv/bin/python','-m','pcc.cli','fit','--config',f'configs/pilot_fit_{model}_{condition}.json','--supervision',f'artifacts/runs/pilot-v4-{model}-{condition}-collect/supervision.jsonl']),
          (stem+'-eval',['.venv-infer/bin/python','-m','pcc.cli','evaluate','--config',f'configs/pilot_fast_{model}_{condition}.json','--adapter',f'artifacts/runs/{stem}-fit/training/final','--split','pilot','--start-family','16','--families','16','--horizon','32'])]
    for name,args in jobs:
        status=root/'artifacts/runs'/name/'status.json'
        if status.exists():
            if json.loads(status.read_text())['status']=='completed':continue
            raise RuntimeError('Existing incomplete repair pilot: '+name)
        (logs/'state.json').write_text(json.dumps({'status':'running','active_job':name,'source_commit':commit},indent=2)+'\n')
        command='cd '+shlex.quote(remote)+' && '+shlex.join(base+args+['--run-id',name])
        result=run_and_mirror(ssh+[command],root,logs/(name+'.log'))
        subprocess.run(ssh+['cd '+shlex.quote(remote)+' && PYTHONPATH=src .venv/bin/python -m pcc.storage'],check=True)
        subprocess.run(['bash','scripts/sync.sh','pull'],check=True)
        deduplicate_completed(root);compact_completed(root)
        if result:raise RuntimeError('Repair pilot failed: '+name)
(logs/'state.json').write_text(json.dumps({'status':'completed','jobs':6,'source_commit':commit},indent=2)+'\n')
