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
import shutil
from .config import RunConfig
from .resources import sha256, used_seconds
from .freeze import verify_freeze


def jobs(plan: dict):
    # All jobs predetermined; the order preserves the author's stated priorities.
    for model in ("qwen","phi"):
        yield {"id":f"base-{model}-eval","model":model,"condition":"base","seed":17,"command":"evaluate",
               "horizon":plan["test_horizon"],"families":plan["test_families"],"start_family":0}
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
    for task in ("horizon32","horizon128","short","larger-memory","unfamiliar","recovery"):
        for condition in ("base","C1","C3","C4","C5"):
            for seed in ([17] if condition=="base" or task in {"larger-memory","unfamiliar"} else plan["seeds"]):
                adapter=None if condition=="base" else f"artifacts/runs/main-qwen-{condition.lower()}-{seed}-r1-fit/training/final"
                yield {"id":f"extra-qwen-{condition.lower()}-{seed}-{task}","model":"qwen","condition":condition,"seed":seed,
                       "command":task,"module":"pcc.extensions","adapter":adapter}
    for model in ("qwen","phi"):
        for condition in ("base","C1","C3","C5"):
            adapter=None if condition=="base" else f"artifacts/runs/main-{model}-{condition.lower()}-17-r1-fit/training/final"
            yield {"id":f"extra-{model}-{condition.lower()}-17-external","model":model,"condition":condition,"seed":17,
                   "command":"external","module":"pcc.validation","adapter":adapter}
    for condition in ("C1","C3","C5"):
        yield {"id":f"extra-qwen-{condition.lower()}-17-natural","model":"qwen","condition":condition,"seed":17,
               "command":"natural","module":"pcc.validation","adapter":f"artifacts/runs/main-qwen-{condition.lower()}-17-r1-fit/training/final"}
    for model in ("phi","qwen"):
        yield {"id":f"judge-{model}-001","model":model,"condition":"base","seed":17,"command":"judge","module":"pcc.judging"}


def run_and_mirror(command: list[str], root: Path, log: Path) -> int:
    """One GPU job; read-only artifact mirroring every minute while it runs."""
    with log.open("a") as stream:
        child=subprocess.Popen(command,stdout=stream,stderr=subprocess.STDOUT)
        last_mirror=time.monotonic()
        while child.poll() is None:
            try:child.wait(timeout=30)
            except subprocess.TimeoutExpired:pass
            if time.monotonic()-last_mirror>=60:
                mirrored=subprocess.run(["bash",str(root/"scripts/sync.sh"),"pull"],cwd=root,stdout=stream,stderr=subprocess.STDOUT)
                if mirrored.returncode:stream.write("Artifact mirror failed; will retry at the next interval.\n");stream.flush()
                last_mirror=time.monotonic()
        return child.returncode


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--root",type=Path,default=Path.cwd());parser.add_argument("--dry-run",action="store_true")
    args=parser.parse_args();root=args.root.resolve()
    freeze=verify_freeze(root)
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
    overrides_path=root/"artifacts/campaign_resume.json"
    overrides=json.loads(overrides_path.read_text()) if overrides_path.exists() else {}
    for job in queue:
        original_id=job["id"]
        override=overrides.get(original_id,{})
        if set(override)-{"run_id","checkpoint","reason"}:raise ValueError("Resume overrides may not change experimental choices")
        if override and not override.get("reason"):raise ValueError("Resume requires a logged infrastructure reason")
        if override:job["id"]=override["run_id"]
        for field in ("adapter","supervision"):
            if not job.get(field):continue
            for source,replacement in overrides.items():
                job[field]=job[field].replace(f"artifacts/runs/{source}/",f"artifacts/runs/{replacement['run_id']}/")
        if shutil.disk_usage(root).free<3*1024**3:raise RuntimeError("Less than 3 GiB local space remains; preserve artifacts and stop for storage review")
        status=root/"artifacts/runs"/job["id"]/"status.json"
        if status.exists():
            state=json.loads(status.read_text())
            if state["status"]=="completed":continue
            raise RuntimeError(f"{job['id']} is {state['status']}; audit and explicitly resume before proceeding")
        used=used_seconds(root/"artifacts/run_registry.jsonl")
        if used>=plan["gpu_hour_ceiling"]*3600:raise RuntimeError("Authorized ceiling reached")
        cfg=RunConfig(model=job["model"],condition=job["condition"],seed=job["seed"],
                      engine="transformers" if job["command"]=="fit" else plan["engine"],
                      structured_decoding=plan["structured_decoding"],
                      batch_size=plan["batch_size"],train_steps=plan["train_steps_per_round"],
                      train_tokens_per_step=plan["train_tokens_per_step"],phase="confirmatory",max_run_seconds=14400,
                      max_input_tokens=8192 if job["command"]=="larger-memory" else 4096,
                      retrieval_messages=16 if job["command"]=="larger-memory" else 8,
                      recent_messages=8 if job["command"]=="larger-memory" else 4)
        filename=job["id"]+".json";cfg.save(config_dir/filename)
        state_path.write_text(json.dumps({"active_job":job,"started_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"gpu_seconds_before":used},indent=2)+"\n")
        # Upload only the one config. Source was synchronized and frozen earlier.
        subprocess.run(ssh+[f"root@{host}","mkdir -p "+shlex.quote(remote+"/artifacts/campaign_configs")],check=True)
        with (config_dir/filename).open("rb") as f:
            subprocess.run(ssh+[f"root@{host}","cat > "+shlex.quote(remote+"/artifacts/campaign_configs/"+filename)],stdin=f,check=True)
        python=".venv/bin/python" if job["command"]=="fit" else ".venv-infer/bin/python"
        module=job.get("module","pcc.cli")
        cmd=[python,"-m",module,job["command"],"--run-id",job["id"],"--config","artifacts/campaign_configs/"+filename]
        if module=="pcc.cli":
            cmd.extend(["--families",str(job["families"]),"--start-family",str(job["start_family"]),"--horizon",str(job["horizon"]),
                        "--split","test" if job["command"]=="evaluate" else "train"])
        if job.get("adapter"):cmd.extend(["--adapter",job["adapter"]])
        if job.get("supervision"):cmd.extend(["--supervision",job["supervision"]])
        if override.get("checkpoint"):
            if job["command"]!="fit":raise ValueError("Only fit jobs have optimizer checkpoints")
            cmd.extend(["--resume-checkpoint",override["checkpoint"]])
        if job["command"]=="collect":cmd.extend(["--window-turns",",".join(map(str,job["window_turns"]))])
        environment=["env","PYTHONPATH=src",f"HF_HOME={remote}/artifacts/hf-cache",f"PCC_CODE_COMMIT={freeze['code_commit']}","VLLM_WORKER_MULTIPROC_METHOD=spawn"]
        if override:environment.append(f"PCC_SUPERSEDES_JOB={original_id}")
        command="cd "+shlex.quote(remote)+" && "+shlex.join([*environment,*cmd])
        returncode=run_and_mirror(ssh+[f"root@{host}",command],root,config_dir/(job["id"]+".log"))
        subprocess.run(ssh+[f"root@{host}","cd "+shlex.quote(remote)+" && PYTHONPATH=src .venv/bin/python -m pcc.storage"],check=True)
        # Synchronize even a failed job; never leave its only evidence on overlay.
        subprocess.run(["bash",str(root/"scripts/sync.sh"),"pull"],check=True,cwd=root)
        from .storage import deduplicate_completed
        deduplicate_completed(root)
        if returncode:raise RuntimeError(f"Job failed and was mirrored: {job['id']}")
    state_path.write_text(json.dumps({"status":"scheduled_grid_complete","jobs":len(queue)},indent=2)+"\n")
    from .study_analysis import analyze
    from .validation import human_packet
    analyze(root);human_packet(root)


if __name__=="__main__":main()
