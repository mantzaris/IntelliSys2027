"""Resumable serialized local controller with per-stage durable artifact mirroring.

Requires an explicitly frozen plan, not the draft. No services are published,
no GPUs rented, and no unrelated processes stopped. SSH arguments are separate
strings; only a shlex-quoted fixed command is interpreted on the authorized pod.
"""
from dataclasses import asdict
from pathlib import Path
import argparse
import json
import os
import shlex
import subprocess
import time
from .config import RunConfig
from .resources import sha256, used_seconds


def jobs(plan: dict):
    # All jobs predetermined; the order preserves the author's stated priorities.
    groups=[("qwen",["C1","C3","C4","C5","A1"]),("phi",["C1","C3","C5"]),
            ("qwen",["A2","A3","C2","C6"])]
    for model,conditions in groups:
        for seed in plan["seeds"]:
            for condition in conditions:
                previous=None
                for round_index,round_cfg in enumerate(plan["rounds"]):
                    stem=f"main-{model}-{condition.lower()}-{seed}-r{round_index}"
                    collect=stem+"-collect";fit=stem+"-fit"
                    yield {"id":collect,"model":model,"condition":condition,"seed":seed,"command":"collect",**round_cfg,"adapter":previous}
                    yield {"id":fit,"model":model,"condition":condition,"seed":seed,"command":"fit",**round_cfg,"adapter":previous,
                           "supervision":f"artifacts/runs/{collect}/supervision.jsonl"}
                    previous=f"artifacts/runs/{fit}/training/final"
                yield {"id":f"main-{model}-{condition.lower()}-{seed}-eval","model":model,"condition":condition,"seed":seed,
                       "command":"evaluate","adapter":previous,"horizon":plan["test_horizon"],"families":plan["test_families"],"start_family":0}


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--root",type=Path,default=Path.cwd());parser.add_argument("--dry-run",action="store_true")
    args=parser.parse_args();root=args.root.resolve()
    freeze_path=root/"configs/freeze.json"
    if not freeze_path.exists():raise PermissionError("No frozen plan exists; run pilot gates first")
    freeze=json.loads(freeze_path.read_text())
    if not freeze.get("pilot_gates_passed"):raise PermissionError("Pilot gates incomplete")
    for path,expected in freeze["files"].items():
        if sha256(root/path)!=expected:raise ValueError(f"Frozen input changed: {path}")
    plan=freeze["plan"];queue=list(jobs(plan))
    if args.dry_run:
        print(json.dumps(queue,indent=2));return
    host=os.environ["PCC_SSH_HOST"];port=os.environ["PCC_SSH_PORT"]
    remote=os.environ.get("PCC_REMOTE_DIR","/workspace/dualingCharacters")
    key=os.environ.get("PCC_SSH_KEY",str(Path.home()/".ssh/id_rsa"))
    known=os.environ.get("PCC_KNOWN_HOSTS","/tmp/intellisys-runpod-known-hosts")
    ssh=["ssh","-F","/dev/null","-i",key,"-p",port,"-o","BatchMode=yes","-o","IdentitiesOnly=yes", "-o","StrictHostKeyChecking=yes","-o",f"UserKnownHostsFile={known}"]
    config_dir=root/"artifacts/campaign_configs";config_dir.mkdir(parents=True,exist_ok=True)
    state_path=root/"artifacts/campaign_state.json"
    for job in queue:
        status=root/"artifacts/runs"/job["id"]/"status.json"
        if status.exists():
            state=json.loads(status.read_text())
            if state["status"]=="completed":continue
            raise RuntimeError(f"{job['id']} is {state['status']}; audit and explicitly resume before proceeding")
        used=used_seconds(root/"artifacts/run_registry.jsonl")
        if used>=plan["gpu_hour_ceiling"]*3600:raise RuntimeError("Authorized ceiling reached")
        cfg=RunConfig(model=job["model"],condition=job["condition"],seed=job["seed"],
                      engine="transformers" if job["command"]=="fit" else plan["engine"],
                      batch_size=plan["batch_size"],train_steps=plan["train_steps_per_round"],
                      train_tokens_per_step=plan["train_tokens_per_step"],phase="confirmatory",max_run_seconds=14400)
        filename=job["id"]+".json";cfg.save(config_dir/filename)
        state_path.write_text(json.dumps({"active_job":job,"started_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"gpu_seconds_before":used},indent=2)+"\n")
        # Upload only the one config. Source was synchronized and frozen earlier.
        subprocess.run(ssh+[f"root@{host}","mkdir -p "+shlex.quote(remote+"/artifacts/campaign_configs")],check=True)
        with (config_dir/filename).open("rb") as f:
            subprocess.run(ssh+[f"root@{host}","cat > "+shlex.quote(remote+"/artifacts/campaign_configs/"+filename)],stdin=f,check=True)
        python=".venv/bin/python" if job["command"]=="fit" else ".venv-infer/bin/python"
        cmd=[python,"-m","pcc.cli",job["command"],"--run-id",job["id"],"--config","artifacts/campaign_configs/"+filename,
             "--families",str(job["families"]),"--start-family",str(job["start_family"]),"--horizon",str(job["horizon"]),
             "--split","test" if job["command"]=="evaluate" else "train"]
        if job.get("adapter"):cmd.extend(["--adapter",job["adapter"]])
        if job.get("supervision"):cmd.extend(["--supervision",job["supervision"]])
        if job["command"]=="collect":cmd.extend(["--window-turns",",".join(map(str,job["window_turns"]))])
        command="cd "+shlex.quote(remote)+" && "+shlex.join(["env","PYTHONPATH=src",f"HF_HOME={remote}/artifacts/hf-cache",f"PCC_CODE_COMMIT={freeze['code_commit']}","VLLM_WORKER_MULTIPROC_METHOD=spawn",*cmd])
        result=subprocess.run(ssh+[f"root@{host}",command])
        # Synchronize even a failed job; never leave its only evidence on overlay.
        subprocess.run(["bash",str(root/"scripts/sync.sh"),"pull"],check=True,cwd=root)
        if result.returncode:raise RuntimeError(f"Job failed and was mirrored: {job['id']}")
    state_path.write_text(json.dumps({"status":"main_grid_complete","jobs":len(queue)},indent=2)+"\n")


if __name__=="__main__":main()
