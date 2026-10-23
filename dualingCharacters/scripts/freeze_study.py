"""Create a local pre-test freeze only after measured engineering gates pass."""
from datetime import datetime, timezone
from pathlib import Path
import json
import subprocess
from pcc.analysis import paired_success
from pcc.campaign import jobs
from pcc.diagnostics import jsonlines
from pcc.environment import digest
from pcc.resources import sha256, used_seconds

root=Path(__file__).resolve().parents[1]
destination=root/"configs/freeze.json"
if destination.exists():raise PermissionError("Existing freeze cannot be overwritten")
branch=subprocess.run(["git","branch","--show-current"],cwd=root,capture_output=True,text=True,check=True).stdout.strip()
if branch!="main":raise PermissionError("Author requires main")
subprocess.run([str(root/".venv/bin/python"),"-m","pytest","-q"],cwd=root,check=True)
plan=json.loads((root/"configs/study_plan.json").read_text())
evidence={};gates={}

def read_run(name):
    path=root/"artifacts/runs"/name/"status.json"
    status=json.loads(path.read_text())
    if status["status"]!="completed":raise ValueError(f"Incomplete gate run: {name}")
    evidence[str(path.relative_to(root))]=sha256(path)
    return path.parent,status

for name in ("profile-bf16-isolated-001","profile-phi-isolated-001","pilot-v4-qwen-c3-fit","pilot-v4-qwen-c5-fit","pilot-v4-phi-c5-fit"):
    run,status=read_run(name);path=run/"training/training_summary.json";report=json.loads(path.read_text())
    if not report["adapter_changed"] or report["optimizer_steps"]<4:raise ValueError("Parameter-update gate failed")
    if sha256(run/"training/final/adapter_model.safetensors")!=report["final_checksums"]["adapter_model.safetensors"]:raise ValueError("Mirrored adapter checksum differs")
    evidence[str(path.relative_to(root))]=sha256(path)
gates["actual_parameter_updates_both_families"]=True
gates["isolated_packed_attention_both_families"]=True

run,status=read_run("mechanism-final-001")
for condition in ("C1","C2","C3","C4","C5","C6","A1","A2","A3"):
    summary=run/f"{condition}_summary.json";rows=json.loads(summary.read_text())
    if len(rows)!=16 or len(paired_success(rows))!=8:raise ValueError("Incomplete final mechanism audit")
    if any(r["message_count"]!=33 for r in rows):raise ValueError("Actual source-message accounting differs")
    evidence[str(summary.relative_to(root))]=sha256(summary)
    turns=jsonlines(run/f"{condition}.jsonl")
    if any(not r["generation"]["parsed"] for r in turns):raise ValueError("Malformed-output nuisance remains")
    if condition=="C1":
        successes=sum(paired_success(rows).values())
        if not 0<successes<8:raise ValueError("Final pilot has no usable task headroom")
gates["schema_and_task_headroom"]=True
actions=jsonlines(run/"C5_characters.jsonl")
if not any(a.get("contradictory_edit_with_source_access") for a in actions):raise ValueError("No observable contradictory interference")
if not any(a["kind"]=="peer" and a["applied"] and a.get("target")!="Jekyll" for a in actions):raise ValueError("Peer channel did not function")
if not any(json.loads(a["prompt"][-1]["content"])["own_history"] for a in actions):raise ValueError("No persistent private history")
for a in actions:
    if any("role" in h for h in json.loads(a["prompt"][-1]["content"])["own_history"]):raise ValueError("Semantic role labels leaked past neutral aliases")
for a in jsonlines(run/"A2_characters.jsonl"):
    if json.loads(a["prompt"][-1]["content"])["own_history"]:raise ValueError("A2 private histories not removed")
for a in jsonlines(run/"A3_characters.jsonl"):
    if a["kind"]=="peer" and a["applied"]:raise ValueError("A3 peer delivery not disabled")
random_actions=jsonlines(run/"C2_characters.jsonl")
if sum(a["kind"]=="edit" for a in random_actions)!=16*8:raise ValueError("C2 direct-action budget differs")
gates["bounded_interference_history_peer_and_alias_controls"]=True

run,status=read_run("pilot-alias-refresh-001")
if not status.get("loaded_adapter_sha256"):raise ValueError("Refresh did not load a trained defender")
counts=json.loads((run/"supervision.counts.json").read_text())
if not counts["clean_valid"] or not counts["failed_eligible"]:raise ValueError("Refresh lacks a required mixture pool")
gates["trained_defender_refresh_and_solvable_teacher_targets"]=True
read_run("pilot-severity-001");gates["severity_diagnostic_completed"]=True
used=used_seconds(root/"artifacts/run_registry.jsonl")/3600
if used+plan["allocation"]["remaining_scheduled_forecast_hours"]>88:raise ValueError("Insufficient budget contingency")
gates["measured_allocation_within_ceiling"]=True

paths=[root/"METHOD.md",root/"STATISTICAL_PLAN.md",root/"pyproject.toml"]
for pattern in ("src/**/*.py","tests/*.py","scripts/*.py","scripts/*.sh","requirements*.txt","data/manifests/*.json"):
    paths.extend(sorted(root.glob(pattern)))
paths.extend(root/"configs"/name for name in ("models.json","study_plan.json","run_exclusions.json"))
names=sorted({str(p.relative_to(root)) for p in paths if p.is_file()})
dirty=subprocess.run(["git","status","--porcelain","--",*names],cwd=root,capture_output=True,text=True,check=True).stdout
if dirty:raise PermissionError("Commit scientific inputs on main before creating the freeze:\n"+dirty)
commit=subprocess.run(["git","rev-parse","HEAD"],cwd=root,capture_output=True,text=True,check=True).stdout.strip()
record={"frozen_utc":datetime.now(timezone.utc).isoformat(),"code_commit":commit,"pilot_gates_passed":True,
        "registration":"Local pre-test hash freeze; not publicly registered","gates":gates,"pilot_evidence":evidence,
        "plan":plan,"queue_hash":digest(list(jobs(plan))),"files":{name:sha256(root/name) for name in names},
        "human_review":"Pending; author requested packet now and raters later"}
destination.write_text(json.dumps(record,indent=2)+"\n")
print(json.dumps({"freeze":str(destination),"sha256":sha256(destination),"files":len(names),"jobs":len(list(jobs(plan))),"source_commit":commit},indent=2))
