"""Pilot-derived allocation and predetermined manifests, before any test outcomes."""
from dataclasses import asdict
from pathlib import Path
import hashlib
import json
import math
import statistics
from .campaign import jobs
from .diagnostics import jsonlines
from .environment import make_family, digest
from .resources import used_seconds, sha256
from .power import simulate


def build(root: Path):
    if (root/"configs/freeze.json").exists():raise PermissionError("Plan already frozen")
    indices=[]
    for domain in range(4):
        for structural in (0,1):
            candidates=[i for i in range(240) if i%4==domain and (i//4)%2==structural]
            indices.extend(sorted(candidates,key=lambda i:hashlib.sha256(f"pcc-horizon-v1:test-{i:04d}".encode()).hexdigest())[:6])
    indices.sort()
    plan={"status":"READY_FOR_HASH_FREEZE","seeds":[17,29,43],"primary_model":"qwen",
          "primary_conditions":["C1","C2","C3","C4","C5","C6"],"ablations":["A1","A2","A3"],
          "replication_model":"phi","replication_conditions":["C1","C3","C5"],"training_families":300,
          "rounds":[{"start_family":0,"families":150,"horizon":16,"window_turns":[6,9,16]},
                    {"start_family":150,"families":150,"horizon":32,"window_turns":[6,17,32]}],
          "train_steps_per_round":256,"train_tokens_per_step":4096,"training_input_tokens_per_condition_seed":2097152,
          "training_mixture":"50:50 eligible clean/recovery windows; report exact target tokens and reuse",
          "checkpoint_rule":"Final fixed-token checkpoint after two rounds; AdamW and common schedule reset per round; no outcome selection",
          "test_families":240,"test_horizon":64,"extension_family_numbers":indices,
          "horizon_seeds":[17],
          "extension_subset_rule":"Six lowest SHA256(pcc-horizon-v1:family_id) in each domain by structural-pattern cell",
          "engine":"vllm","structured_decoding":True,"batch_size":64,"gpu_hour_ceiling":96,
          "data_generation_cap_seconds_per_round":5400,"training_stage_cap_seconds":3600,"evaluation_stage_cap_seconds":5400,
          "known_hourly_rate_usd":None,"external_questions":50,"natural_conversations_per_condition":40,
          "human_review_outputs":120,"human_review_status":"Author requested packet now; raters later",
          "notes":"No test outcomes inspected. Modest-effect power is limited; no significance-based changes or extensions."}
    # Use twice the measured 32-request batch cost as a conservative 64-request
    # forecast, and the measured full mechanism rollout when that is slower.
    timings={}
    for model in ("qwen","phi"):
        inference=[];collection=[];characters=[];training=[];trace=[]
        for condition in (["c3","c5"] if model=="qwen" else ["c5"]):
            for phase,target in (("eval",inference),("collect",collection)):
                path=root/f"artifacts/runs/pilot-v4-{model}-{condition}-{phase}/batches.jsonl"
                rows=jsonlines(path);target.append(2*statistics.mean(r["seconds"] for r in rows if r["kind"]=="defender"))
                if phase=="collect":characters.append(2*statistics.mean(r["seconds"] for r in rows if r["kind"]=="frozen_character"))
                trace.append({"path":str(path.relative_to(root)),"sha256":sha256(path)})
            training.append(json.loads((root/f"artifacts/runs/pilot-v4-{model}-{condition}-fit/training/training_summary.json").read_text())["seconds"]/32)
        isolated=root/f"artifacts/runs/profile-{'bf16' if model=='qwen' else 'phi'}-isolated-001/training/training_summary.json"
        t=json.loads(isolated.read_text());training.append(t["seconds"]/t["optimizer_steps"])
        timings[model]={"answer_batch64_seconds":max(inference),"collection_batch64_seconds":max(collection),
                        "character_batch64_seconds":max(characters),"optimizer_step_seconds":max(training),"trace":trace}
    mechanism=jsonlines(root/"artifacts/runs/mechanism-v3-001/batches.jsonl")
    timings["qwen"]["collection_batch64_seconds"]=max(timings["qwen"]["collection_batch64_seconds"],statistics.mean(r["seconds"] for r in mechanism if r["kind"]=="defender"))
    timings["qwen"]["character_batch64_seconds"]=max(timings["qwen"]["character_batch64_seconds"],statistics.mean(r["seconds"] for r in mechanism if r["kind"]=="frozen_character"))
    estimates=[]
    for job in jobs(plan):
        t=timings[job["model"]];task=job["command"];seconds=60.
        if task=="fit":seconds=12+plan["train_steps_per_round"]*t["optimizer_step_seconds"]
        elif task=="collect":
            batches=math.ceil(2*job["families"]/64)
            seconds+=batches*job["horizon"]*t["collection_batch64_seconds"]+2*t["collection_batch64_seconds"]
            if job["condition"] not in {"C1","C2"}:seconds+=batches*12*t["character_batch64_seconds"]
        elif task=="evaluate":seconds+=math.ceil(2*job["families"]/64)*job["horizon"]*t["answer_batch64_seconds"]
        elif task in {"horizon32","horizon128","short","larger-memory","unfamiliar"}:
            horizon={"horizon32":32,"horizon128":128,"short":16}.get(task,64)
            seconds+=2*horizon*t["answer_batch64_seconds"]*(1.5 if task=="larger-memory" else 1.2 if task=="unfamiliar" else 1)
        elif task=="recovery":seconds+=2*4*t["answer_batch64_seconds"]*1.5
        elif task=="natural":seconds+=64*t["answer_batch64_seconds"]*2+4*t["answer_batch64_seconds"]
        elif task=="external":seconds+=3*t["answer_batch64_seconds"]
        elif task=="judge":seconds+=20
        estimates.append({"run_id":job["id"],"stage":task,"model":job["model"],"seconds_forecast":seconds})
    used=used_seconds(root/"artifacts/run_registry.jsonl")
    forecast=sum(r["seconds_forecast"] for r in estimates)
    (root/"reports/tables/allocation_candidates.json").write_text(json.dumps({"steps_per_round":plan["train_steps_per_round"],"total_forecast_hours_including_pilot":(used+forecast)/3600,"timings":timings,"jobs":estimates},indent=2)+"\n")
    print(json.dumps({"candidate_steps_per_round":plan["train_steps_per_round"],"total_forecast_hours":(used+forecast)/3600}),flush=True)
    if (used+forecast)/3600>88:raise ValueError("Measured forecast leaves insufficient contingency; reduce optional scope before freezing")
    plan["allocation"]={"already_reserved_gpu_hours":used/3600,"remaining_scheduled_forecast_hours":forecast/3600,
                        "contingency_hours":96-(used+forecast)/3600,"inference_engine_start_allowance_seconds":60,
                        "qualification":"Conservative linear batch scaling from measured pilots; forecast, not consumption or a spending target"}
    (root/"configs/study_plan.json").write_text(json.dumps(plan,indent=2)+"\n")
    (root/"reports/tables/workload_forecast.json").write_text(json.dumps({"allocation":plan["allocation"],"timings":timings,"jobs":estimates},indent=2)+"\n")
    horizons=[]
    for horizon in (16,32,64,128):
        for i in indices:
            pair=make_family("test",i,horizon)
            horizons.append({"family_id":pair[0].family_id,"horizon":horizon,"graph_hash":pair[0].graph_hash,
                             "source_hashes":[digest([m.public() for m in s.source_messages()]) for s in pair]})
    (root/"data/manifests/horizons.json").write_text(json.dumps({"selection_rule":plan["extension_subset_rule"],"records":horizons},indent=2)+"\n")
    training=[]
    for round_number,cfg in enumerate(plan["rounds"]):
        for i in range(cfg["start_family"],cfg["start_family"]+cfg["families"]):
            pair=make_family("train",i,cfg["horizon"])
            training.append({"round":round_number,"family_id":pair[0].family_id,"horizon":cfg["horizon"],"window_turns":cfg["window_turns"],
                             "graph_hash":pair[0].graph_hash,"source_hashes":[digest([m.public() for m in s.source_messages()]) for s in pair]})
    (root/"data/manifests/training_windows.json").write_text(json.dumps(training,indent=2)+"\n")
    sensitivity=[simulate(n,.375,d,s,trials=2000) for n in (240,480) for d in (.1,.3125,.4) for s in (0.,.02,.05)]
    (root/"reports/tables/pilot_based_precision.json").write_text(json.dumps({"pilot_families":16,"pilot_discordance":.3125,"effect":.05,"design_sensitivity":sensitivity},indent=2)+"\n")
    print(json.dumps({"jobs":len(estimates),"allocation":plan["allocation"]},indent=2))


if __name__=="__main__":build(Path.cwd())
