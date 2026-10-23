"""Verify final packing boundaries and alias-controlled refreshed interactions."""
from pathlib import Path
import json
import os
import shlex
import subprocess
import time
from .campaign import run_and_mirror


def main():
    root=Path.cwd();host=os.environ["PCC_SSH_HOST"];port=os.environ["PCC_SSH_PORT"]
    remote="/workspace/dualingCharacters"
    ssh=["ssh","-F","/dev/null","-i",str(Path.home()/".ssh/id_rsa"),"-p",port,"-o","BatchMode=yes","-o","IdentitiesOnly=yes","-o","StrictHostKeyChecking=yes","-o","UserKnownHostsFile=/tmp/intellisys-runpod-known-hosts",f"root@{host}"]
    state=root/"artifacts/pilot_controller/state.json"
    while not state.exists() or json.loads(state.read_text()).get("status")!="completed":time.sleep(30)
    subprocess.run(["bash",str(root/"scripts/sync.sh"),"push"],check=True)
    commit=subprocess.run(["git","rev-parse","HEAD"],capture_output=True,text=True,check=True).stdout.strip()
    queue=[("profile-bf16-isolated-001",[".venv/bin/python","-m","pcc.cli","profile","--config","configs/profile_bf16.json","--families","1","--horizon","16"]),
           ("profile-phi-isolated-001",[".venv/bin/python","-m","pcc.cli","profile","--config","configs/profile_phi.json","--families","1","--horizon","16"]),
           ("pilot-alias-refresh-001",[".venv-infer/bin/python","-m","pcc.cli","collect","--config","configs/pilot_fast_qwen_c5.json","--adapter","artifacts/runs/pilot-v4-qwen-c5-fit/training/final","--families","4","--start-family","20","--horizon","32","--window-turns","6,17,32"])]
    logs=root/"artifacts/final_pilot_checks";logs.mkdir(parents=True,exist_ok=True)
    for run_id,cmd in queue:
        path=root/"artifacts/runs"/run_id/"status.json"
        if path.exists():
            if json.loads(path.read_text())["status"]=="completed":continue
            raise RuntimeError(f"Inspect incomplete final check {run_id}")
        (logs/"state.json").write_text(json.dumps({"status":"running","active_job":run_id},indent=2)+"\n")
        command="cd "+shlex.quote(remote)+" && "+shlex.join(["env","PYTHONPATH=src",f"HF_HOME={remote}/artifacts/hf-cache",f"PCC_CODE_COMMIT={commit}","VLLM_WORKER_MULTIPROC_METHOD=spawn",*cmd,"--run-id",run_id])
        result=run_and_mirror(ssh+[command],root,logs/(run_id+".log"))
        subprocess.run(["bash",str(root/"scripts/sync.sh"),"pull"],check=True)
        if result:raise RuntimeError(f"Final check failed: {run_id}")
    (logs/"state.json").write_text(json.dumps({"status":"completed","jobs":len(queue)},indent=2)+"\n")


if __name__=="__main__":main()
