"""Serialized repair gates on existing pilot-only collections; no test selection."""
from pathlib import Path
import argparse
import fcntl
import json
import os
import shlex
import subprocess
import time
from pcc.campaign import run_and_mirror
from pcc.storage import compact_completed,deduplicate_completed

parser=argparse.ArgumentParser();parser.add_argument('--reference-refresh',action='store_true')
options=parser.parse_args()
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
queue=[]
if options.reference_refresh:
    for model in ('qwen','phi'):
        queue.append((f'pilot-format2-{model}-base',['.venv-infer/bin/python','-m','pcc.cli','evaluate','--config',f'configs/pilot_fast_{model}_c5.json','--split','pilot','--start-family','16','--families','16','--horizon','32']))
    queue.append(('pilot-format2-refresh',['.venv-infer/bin/python','-m','pcc.cli','collect','--config','configs/pilot_fast_qwen_c5.json','--adapter','artifacts/runs/pilot-format2-qwen-c5-fit/training/final','--split','pilot','--families','4','--horizon','32','--window-turns','6,17,32']))
else:
    for model,condition in [('qwen','c3'),('qwen','c5'),('phi','c5')]:
        stem=f'pilot-format2-{model}-{condition}'
        queue.extend([(stem+'-fit',['.venv/bin/python','-m','pcc.cli','fit','--config',f'configs/pilot_fit_{model}_{condition}.json','--supervision',f'artifacts/runs/pilot-v4-{model}-{condition}-collect/supervision.jsonl']),
                      (stem+'-eval',['.venv-infer/bin/python','-m','pcc.cli','evaluate','--config',f'configs/pilot_fast_{model}_{condition}.json','--adapter',f'artifacts/runs/{stem}-fit/training/final','--split','pilot','--start-family','16','--families','16','--horizon','32'])])
state_path=logs/('reference_state.json' if options.reference_refresh else 'state.json')
for name,args in queue:
    status=root/'artifacts/runs'/name/'status.json'
    if status.exists():
        if json.loads(status.read_text())['status']=='completed':continue
        raise RuntimeError('Existing incomplete repair pilot: '+name)
    state_path.write_text(json.dumps({'status':'running','active_job':name,'source_commit':commit},indent=2)+'\n')
    command='cd '+shlex.quote(remote)+' && '+shlex.join(base+args+['--run-id',name])
    result=run_and_mirror(ssh+[command],root,logs/(name+'.log'))
    subprocess.run(ssh+['cd '+shlex.quote(remote)+' && PYTHONPATH=src .venv/bin/python -m pcc.storage'],check=True)
    subprocess.run(['bash','scripts/sync.sh','pull'],check=True)
    deduplicate_completed(root);compact_completed(root)
    if result:raise RuntimeError('Repair pilot failed: '+name)
state_path.write_text(json.dumps({'status':'completed','jobs':len(queue),'source_commit':commit},indent=2)+'\n')
