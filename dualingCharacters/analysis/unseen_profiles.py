"""Separately declared exploratory opponent test; never modifies core source files.

Use `check` without a GPU. `run` is one serialized remote job, permitted only
after the entire original queue completes and the supplemental budget gate passes.
All changes to the cast are process-local and recorded with exact source copies.
"""
from pathlib import Path
import argparse
import json
import os
import random
import shutil
import time
from pcc.campaign import jobs
from pcc.config import RunConfig
from pcc.environment import OPTIONS, digest, make_family
from pcc.freeze import verify_freeze
from pcc.resources import RunLedger, sha256, used_seconds


def specification(root: Path) -> tuple[dict, dict]:
    primary=verify_freeze(root)
    freeze=json.loads((root/"analysis/unseen_profiles_freeze.json").read_text())
    path=root/"analysis/unseen_profiles_protocol.json"
    if sha256(path)!=freeze["protocol_sha256"]:
        raise PermissionError("Supplemental protocol changed after its declaration")
    if sha256(root/"configs/freeze.json")!=freeze["amended_primary_freeze_sha256"]:
        raise PermissionError("Review any new primary infrastructure amendment before this supplement")
    protocol=json.loads(path.read_text())
    if protocol["family_numbers"]!=primary["plan"]["extension_family_numbers"]:
        raise ValueError("Supplement must retain the original fixed extension sample")
    return protocol,primary


def resolved_run(root: Path, original: str) -> str:
    path=root/"artifacts/campaign_resume.json"
    overrides=json.loads(path.read_text()) if path.exists() else {}
    return overrides.get(original,{}).get("run_id",original)


def require_core_complete(root: Path, primary: dict) -> dict:
    records={}
    for job in jobs(primary["plan"]):
        run_id=resolved_run(root,job["id"]);path=root/"artifacts/runs"/run_id/"status.json"
        if not path.exists() or json.loads(path.read_text())["status"]!="completed":
            raise PermissionError("Original core queue is incomplete: "+run_id)
        records[run_id]=sha256(path)
    return records


def opponent_cast(protocol: dict, family_id: str, seed: int):
    from pcc.characters import Character
    rng=random.Random(f"{family_id}:{seed}:{protocol['cast_seed_tag']}")
    aliases=list(protocol["aliases"]);rng.shuffle(aliases)
    result=[]
    for index,role in enumerate(("Steward","Broker")):
        spec=protocol["profiles"][role];slot=spec["assigned_slot"]
        option="3000" if role=="Steward" else rng.choice(OPTIONS[slot])
        result.append(Character(role,aliases[index],slot,option,rng.randrange(2)))
    return result


def install_profiles(protocol: dict):
    # Deliberate, explicit runtime substitution for this process only. Files and
    # the primary freeze are unchanged. No evaluator state enters this function.
    import pcc.characters as characters
    import pcc.evaluation as evaluation
    for role,spec in protocol["profiles"].items():
        characters.PROFILES[role]=tuple(spec["wordings"])
        characters.UTILITIES[role]=spec["utility"]
    def cast(condition, family_id, seed):
        if condition!="C5":raise ValueError("Supplement uses the common three-character scheduler")
        return opponent_cast(protocol,family_id,seed)
    evaluation.cast=cast


def permitted_jobs(protocol: dict):
    for condition in protocol["conditions"]:
        for seed in protocol["base_seeds"] if condition=="base" else protocol["trained_seeds"]:
            yield condition,seed,f"supplement-qwen-{condition.lower()}-{seed}-unseen-profiles-v1"


def run(root: Path, condition: str, seed: int):
    protocol,primary=specification(root)
    allowed={(c,s):r for c,s,r in permitted_jobs(protocol)}
    if (condition,seed) not in allowed:raise ValueError("Undeclared condition or seed")
    run_id=allowed[condition,seed]
    implementation=root/"analysis/unseen_profiles_implementation.json"
    pinned=json.loads(implementation.read_text())
    if sha256(Path(__file__).resolve())!=pinned["runner_sha256"]:
        raise PermissionError("Supplemental runner differs from its recorded implementation")
    core_records=require_core_complete(root,primary)
    activation=root/"artifacts/unseen_profiles_activation.json"
    registry=root/"artifacts/run_registry.jsonl";consumed=used_seconds(registry)
    if not activation.exists():
        remaining=protocol["project_reserved_gpu_hour_ceiling"]-consumed/3600
        if remaining<protocol["budget_gate_remaining_reserved_gpu_hours"]:
            raise PermissionError("Insufficient authorized budget for the predeclared supplement")
        activation.write_text(json.dumps({"protocol_sha256":sha256(root/"analysis/unseen_profiles_protocol.json"),
            "activated_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
            "before_reserved_gpu_seconds":consumed,"core_completed_status_hashes":core_records},indent=2)+"\n")
    gate=json.loads(activation.read_text())
    if gate["protocol_sha256"]!=sha256(root/"analysis/unseen_profiles_protocol.json"):
        raise PermissionError("Activation belongs to another supplemental protocol")
    # Count every run since activation, including failed runs and any unexpected
    # intervening work, conservatively against this supplemental allowance.
    remaining_seconds=protocol["supplement_reserved_gpu_hour_ceiling"]*3600-(consumed-gate["before_reserved_gpu_seconds"])
    if remaining_seconds<=0:raise PermissionError("Supplemental ceiling reached")
    cfg=RunConfig(model=protocol["model"],condition=condition,seed=seed,phase="confirmatory",
        engine=primary["plan"]["engine"],structured_decoding=primary["plan"]["structured_decoding"],
        batch_size=primary["plan"]["batch_size"],
        max_run_seconds=min(protocol["per_run_seconds_ceiling"],remaining_seconds))
    if cfg.intervention_opportunities!=protocol["intervention_opportunities"] or cfg.history_actions!=protocol["private_history_actions"]:
        raise ValueError("Common interface differs from the declared supplement")
    scenarios=[s for n in protocol["family_numbers"] for s in make_family("test",n,protocol["horizon"])]
    with RunLedger(root/"artifacts",run_id,cfg) as ledger:
        for name in ("unseen_profiles.py","unseen_profiles_protocol.json","unseen_profiles_freeze.json","unseen_profiles_implementation.json"):
            shutil.copyfile(root/"analysis"/name,ledger.run_dir/name)
        ledger.metadata.update(extension="unseen_profiles_v1",classification=protocol["classification"],
            family_numbers=protocol["family_numbers"],supplement_protocol_sha256=sha256(root/"analysis/unseen_profiles_protocol.json"),
            supplement_runner_sha256=sha256(Path(__file__).resolve()),supplement_commit=os.environ.get("PCC_SUPPLEMENT_COMMIT","UNRECORDED"),
            dataset_hash=digest([{"id":s.family_id,"world":s.world,"sources":[m.public() for m in s.source_messages()]} for s in scenarios]))
        from pcc.fast_backend import FastBackbone
        model=FastBackbone(cfg,ledger,root/"configs/models.json")
        if condition!="base":
            fit=resolved_run(root,f"main-qwen-{condition.lower()}-{seed}-r1-fit")
            model.load_adapter(root/"artifacts/runs"/fit/"training/final")
        install_profiles(protocol)
        from pcc.evaluation import run_episodes
        run_episodes(model,scenarios,"C5",ledger.run_dir/"evaluation.jsonl")


def check(root: Path):
    """Exercise public observations and isolation without loading a model."""
    from pcc.characters import action_prompt
    from pcc.memory import WorkingMemory
    protocol,primary=specification(root);install_profiles(protocol)
    for seed in protocol["trained_seeds"]:
        for n in protocol["family_numbers"]:
            scenario=make_family("test",n,64)[0]
            cast=opponent_cast(protocol,scenario.family_id,seed)
            second=opponent_cast(protocol,scenario.family_id,seed)
            if cast!=second or len({a.alias for a in cast})!=2:raise AssertionError("Cast must be reproducible and distinct")
            for actor in cast:
                messages,sources=action_prompt(actor,cast,scenario.spec,list(scenario.messages[:8]),WorkingMemory(),"C5",6,8,True)
                body=json.loads(messages[-1]["content"])
                if set(body)!={"catalog","memory","sources","own_history","inbox","peers"}:raise AssertionError("Unexpected observation channel")
                actor.record({"actor":actor.alias,"kind":"peer","role":actor.role,"oracle_target":"MUST NOT ENTER HISTORY"},6)
                if "oracle_target" in actor.history[-1] or "role" in actor.history[-1]:raise AssertionError("Private audit information leaked")
            if any(a.history for a in second):raise AssertionError("Histories shared across independent casts")
    print(json.dumps({"public_interface_checks":len(protocol["family_numbers"])*len(protocol["trained_seeds"])*2,
                      "declared_jobs":len(list(permitted_jobs(protocol))),"model_calls":0,
                      "scientific_input_hashes_verified":len(primary["files"])}))


if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("task",choices=("check","run"))
    parser.add_argument("--condition",choices=("base","C1","C3","C5"));parser.add_argument("--seed",type=int)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    if args.task=="check":check(root)
    else:
        if args.condition is None or args.seed is None:parser.error("run requires condition and seed")
        run(root,args.condition,args.seed)
