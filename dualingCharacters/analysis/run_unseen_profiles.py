"""Local serialized controller for the fixed, budget-gated supplement.

Optional waiting is CPU-only. The shared campaign lock and the remote GPU lock
prevent overlap with the original queue. No endpoint, sample or seed is selected
from outcomes. Existing failed supplemental IDs stop the controller for audit.
"""
from pathlib import Path
import argparse
import fcntl
import json
import os
import shlex
import shutil
import subprocess
import time
from unseen_profiles import specification, require_core_complete, permitted_jobs
from pcc.campaign import run_and_mirror, commit_generated_package
from pcc.resources import sha256, used_seconds
from pcc.storage import compact_completed, deduplicate_completed


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--wait-for-core",action="store_true")
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    state_path=root/"artifacts/unseen_profiles_controller_state.json"
    protocol,primary=specification(root)
    controller_lock=(root/"artifacts/unseen_profiles_controller.lock").open("a+")
    fcntl.flock(controller_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    def state(status,**extra):
        temporary=state_path.with_suffix(".tmp")
        temporary.write_text(json.dumps({"status":status,"classification":protocol["classification"],
            "controller_sha256":sha256(Path(__file__).resolve()),**extra},indent=2)+"\n")
        temporary.replace(state_path)
    while True:
        current=root/"artifacts/campaign_state.json"
        try:complete=json.loads(current.read_text()).get("status")=="scheduled_grid_complete"
        except (FileNotFoundError,json.JSONDecodeError):complete=False
        if complete:break
        if not args.wait_for_core:raise PermissionError("Original controller has not completed")
        if not state_path.exists() or json.loads(state_path.read_text())["status"]!="waiting_for_core":state("waiting_for_core")
        time.sleep(30)
    # The core records completion before its report/commit finishes. Wait for
    # its lock to be released before any upload or model operation.
    shared=(root/"artifacts/campaign.lock").open("a+")
    while True:
        try:fcntl.flock(shared,fcntl.LOCK_EX|fcntl.LOCK_NB);break
        except BlockingIOError:time.sleep(30)
    require_core_complete(root,primary)
    activation=root/"artifacts/unseen_profiles_activation.json"
    remaining=protocol["project_reserved_gpu_hour_ceiling"]-used_seconds(root/"artifacts/run_registry.jsonl")/3600
    if not activation.exists() and remaining<protocol["budget_gate_remaining_reserved_gpu_hours"]:
        state("not_executed_budget_gate",remaining_reserved_gpu_hours=remaining)
        print("Supplement not executed: fixed remaining-budget gate did not pass.",flush=True)
        return
    host=os.environ["PCC_SSH_HOST"];port=os.environ["PCC_SSH_PORT"]
    remote=os.environ.get("PCC_REMOTE_DIR","/workspace/dualingCharacters")
    key=os.environ.get("PCC_SSH_KEY",str(Path.home()/".ssh/id_rsa"))
    known=os.environ.get("PCC_KNOWN_HOSTS","/tmp/intellisys-runpod-known-hosts")
    ssh=["ssh","-F","/dev/null","-i",key,"-p",port,"-o","BatchMode=yes","-o","IdentitiesOnly=yes",
         "-o","StrictHostKeyChecking=yes","-o",f"UserKnownHostsFile={known}"]
    target=f"root@{host}"
    commit=subprocess.run(["git","rev-parse","HEAD"],cwd=root,capture_output=True,text=True,check=True).stdout.strip()
    subprocess.run(ssh+[target,"mkdir -p "+shlex.quote(remote+"/analysis")],check=True)
    filenames=["unseen_profiles.py","unseen_profiles_protocol.json","unseen_profiles_freeze.json","unseen_profiles_implementation.json"]
    subprocess.run(["rsync","-az","-e",shlex.join(ssh),*[str(root/"analysis"/name) for name in filenames],target+":"+remote+"/analysis/"],check=True)
    resume=root/"artifacts/campaign_resume.json"
    if resume.exists():subprocess.run(["rsync","-az","-e",shlex.join(ssh),str(resume),target+":"+remote+"/artifacts/"],check=True)
    logs=root/"artifacts/supplement_configs";logs.mkdir(exist_ok=True)
    shutil.copyfile(Path(__file__).resolve(),logs/"controller_source.py")
    for condition,seed,run_id in permitted_jobs(protocol):
        status=root/"artifacts/runs"/run_id/"status.json"
        if status.exists():
            if json.loads(status.read_text())["status"]=="completed":continue
            raise RuntimeError("Preserve and audit the existing incomplete supplement: "+run_id)
        if shutil.disk_usage(root).free<3*1024**3:
            state("incomplete_storage_guard",run_id=run_id)
            raise RuntimeError("Less than 3 GiB local space remains; no supplemental stage started")
        state("running",run_id=run_id,source_commit=commit)
        environment=["env","PYTHONPATH=src",f"HF_HOME={remote}/artifacts/hf-cache",
            f"PCC_CODE_COMMIT={primary['code_commit']}",f"PCC_SUPPLEMENT_COMMIT={commit}","VLLM_WORKER_MULTIPROC_METHOD=spawn"]
        command="cd "+shlex.quote(remote)+" && "+shlex.join([*environment,".venv-infer/bin/python",
            "analysis/unseen_profiles.py","run","--condition",condition,"--seed",str(seed)])
        rc=run_and_mirror(ssh+[target,command],root,logs/(run_id+".log"))
        compact=subprocess.run(ssh+[target,"cd "+shlex.quote(remote)+" && PYTHONPATH=src .venv/bin/python -m pcc.storage"])
        subprocess.run(["bash",str(root/"scripts/sync.sh"),"pull"],cwd=root,check=True)
        if compact.returncode:
            state("incomplete_archive_check",run_id=run_id)
            raise RuntimeError("Supplement archive check failed; copied artifacts retained for audit")
        deduplicate_completed(root);compact_completed(root)
        if rc:
            state("incomplete",run_id=run_id,returncode=rc)
            raise RuntimeError("Supplement failed; artifacts retained and mirrored: "+run_id)
    state("scheduled_supplement_complete",jobs=len(list(permitted_jobs(protocol))))
    subprocess.run(["bash","analysis/regenerate_all.sh"],cwd=root,check=True)
    commit_generated_package(root,"Original queue and the separately declared exploratory unseen-profile supplement completed; human ratings and author review pending")


if __name__=="__main__":
    try:main()
    except Exception as error:
        path=Path(__file__).resolve().parents[1]/"artifacts/unseen_profiles_controller_state.json"
        previous=json.loads(path.read_text()) if path.exists() else {}
        previous.update(status="controller_error",error=str(error))
        temporary=path.with_suffix(".tmp");temporary.write_text(json.dumps(previous,indent=2)+"\n");temporary.replace(path)
        raise
