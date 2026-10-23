"""Bounded pre-confirmation GPU pilots, serialized behind the mechanism audit."""
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
    logs=root/"artifacts/pilot_controller";logs.mkdir(parents=True,exist_ok=True)
    # Wait only for our named audit; RunLedger separately refuses any other GPU job.
    while True:
        result=subprocess.run(ssh+["cat "+remote+"/artifacts/runs/mechanism-v3-001/status.json"],capture_output=True,text=True,check=True)
        status=json.loads(result.stdout)
        if status["status"]!="running":break
        time.sleep(30)
    subprocess.run(["bash",str(root/"scripts/sync.sh"),"pull"],check=True)
    if status["status"]!="completed":raise RuntimeError("Mechanism audit failed; inspect before continuing")
    subprocess.run(["bash",str(root/"scripts/sync.sh"),"push"],check=True)
    commit=subprocess.run(["git","rev-parse","HEAD"],capture_output=True,text=True,check=True).stdout.strip()
    queue=[]
    for model in ("qwen","phi"):
        queue.append((f"pilot-v4-{model}-base",[".venv-infer/bin/python","-m","pcc.cli","evaluate","--config",f"configs/pilot_fast_{model}_c5.json","--split","pilot","--start-family","16","--families","16","--horizon","32"]))
    for model,condition in (("qwen","c3"),("qwen","c5"),("phi","c5")):
        stem=f"pilot-v4-{model}-{condition}"
        queue.append((stem+"-collect",[".venv-infer/bin/python","-m","pcc.cli","collect","--config",f"configs/pilot_fast_{model}_{condition}.json","--split","pilot","--families","16","--horizon","16","--window-turns","6,9,16"]))
        queue.append((stem+"-fit",[".venv/bin/python","-m","pcc.cli","fit","--config",f"configs/pilot_fit_{model}_{condition}.json","--supervision",f"artifacts/runs/{stem}-collect/supervision.jsonl"]))
        queue.append((stem+"-eval",[".venv-infer/bin/python","-m","pcc.cli","evaluate","--config",f"configs/pilot_fast_{model}_{condition}.json","--adapter",f"artifacts/runs/{stem}-fit/training/final","--split","pilot","--start-family","16","--families","16","--horizon","32"]))
    queue.append(("pilot-severity-001",[".venv-infer/bin/python","-m","pcc.severity","--config","configs/mechanism_fast.json"]))
    for run_id,args in queue:
        status_path=root/"artifacts/runs"/run_id/"status.json"
        if status_path.exists():
            if json.loads(status_path.read_text())["status"]=="completed":continue
            raise RuntimeError(f"Existing incomplete pilot {run_id}; explicit audit required")
        args += ["--run-id",run_id]
        command="cd "+shlex.quote(remote)+" && "+shlex.join(["env","PYTHONPATH=src",f"HF_HOME={remote}/artifacts/hf-cache",f"PCC_CODE_COMMIT={commit}","VLLM_WORKER_MULTIPROC_METHOD=spawn",*args])
        (logs/"state.json").write_text(json.dumps({"status":"running","active_job":run_id},indent=2)+"\n")
        result=run_and_mirror(ssh+[command],root,logs/(run_id+".log"))
        subprocess.run(["bash",str(root/"scripts/sync.sh"),"pull"],check=True)
        if result:raise RuntimeError(f"Pilot failed: {run_id}")
    (logs/"state.json").write_text(json.dumps({"status":"completed","jobs":len(queue)},indent=2)+"\n")


if __name__=="__main__":main()
