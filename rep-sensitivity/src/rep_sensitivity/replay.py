"""Frozen replay with per-call immutable persistence and resumable stage scheduling."""
from dataclasses import asdict
from itertools import product
import json
from pathlib import Path
import time
from .generation import generate
from .graphs import partition, build_graphs
from .metrics import parse, score_assertions, score_root
from .policies import make_prompt
from .reports import freeze, thaw, repeat, registry, ancestry_registry
from .schema import canonical, digest
from .storage import Ledger, immutable_json, utcnow


def prepare(config, directory):
    directory = Path(directory)
    pairs = generate(config["split"], config["base_pairs"], config.get("benchmark_version",1))
    corpus = {p["pair_id"]: freeze(p) for p in pairs}
    immutable_json(directory / "pairs.json", pairs)
    immutable_json(directory / "frozen-reports.json", corpus)
    trials = []
    for p, model, world, condition, org, policy, repetition in product(
            pairs, config["models"], config["worlds"], config["repetition_conditions"],
            config["organizations"], config["policies"], range(config["stochastic_repetitions"])):
        trial = {"pair_id": p["pair_id"], "model": model, "world": world, "condition": condition,
                 "organization": org, "policy": policy, "repetition": repetition,
                 "suite": config["name"]}
        trial["trial_id"] = digest(trial)[:24]
        trials.append(trial)
    manifest = {"config": config, "pairs_sha256": digest(pairs), "corpus_sha256": digest(corpus),
                "trajectories": len(trials), "manager_calls": sum(1 if t["organization"] == "flat" else 3 for t in trials),
                "trials": trials}
    if "expected_trajectories" in config: assert len(trials) == config["expected_trajectories"]
    if "expected_manager_calls" in config: assert manifest["manager_calls"] == config["expected_manager_calls"]
    immutable_json(directory / "manifest.json", manifest)
    immutable_json(Path("records/manifests") / (config["name"] + ".json"),
                   {k: v for k, v in manifest.items() if k != "trials"} | {"manifest_sha256": digest(manifest)})
    return manifest, {p["pair_id"]: p for p in pairs}, corpus


def seed_for(trial, stage):
    return int(digest([trial["pair_id"], trial["repetition"], stage])[:8], 16) % (2**31)


def execute_requests(requests, model, ledger):
    out, pending = {}, []
    for request in requests:
        key = ledger.key(request["prompt"], model.settings, request["trial"], request["stage"])
        request = {**request, "request_hash": key, "seed": seed_for(request["trial"], request["stage"])}
        saved = ledger.get(key)
        if saved is None: pending.append(request)
        else: out[(request["trial"]["trial_id"], request["stage"])] = saved
    for offset in range(0, len(pending), model.batch_size):
        batch = pending[offset:offset + model.batch_size]
        for r in batch: ledger.event("started", request_hash=r["request_hash"], trial_id=r["trial"]["trial_id"], stage=r["stage"])
        # Offline inference has no transport retries. Engine failures stop the run.
        # A crash before acceptance can be retried on resume, explicitly journaled.
        try:
            responses = model.run(batch)
        except Exception as error:
            ledger.event("batch_failed", requests=[r["request_hash"] for r in batch], error=repr(error))
            raise
        for request, response in zip(batch, responses):
            saved = {"request_hash": request["request_hash"], "trial_id": request["trial"]["trial_id"],
                     "trial": request["trial"], "stage": request["stage"], "seed": request["seed"],
                     "settings": model.settings, "prompt": request["prompt"], "response": response,
                     "accepted_utc": utcnow()}
            ledger.accept(request["request_hash"], saved)
            out[(saved["trial_id"], saved["stage"])] = saved
        print(canonical({"accepted_calls": offset + len(batch), "pending_calls_this_phase": len(pending),
                         "last_batch_wall_seconds": responses[0]["batch_wall_seconds"]}), flush=True)
    return out


def run(config, alias, root="artifacts/runs"):
    if config.get("interface_version") != 5:
        raise ValueError("Archived v1-v4 protocols require their recorded implementation, not the current v5 output contract")
    if config.get("freeze_required") or config.get("status", "").startswith("PROVISIONAL"):
        raise ValueError("Held-out protocol is not frozen; execution blocked")
    from .models import LocalModel
    directory = Path(root) / config["name"]
    source={p.name:p.read_text() for p in Path(__file__).parent.glob("*.py")}
    immutable_json(directory / "implementation.json",source)
    manifest, pairs, corpus = prepare(config, directory)
    model = LocalModel(alias, config["max_context_tokens"], config["max_output_tokens"],
                       config["temperature"], config["top_p"], config["batch_size"], config.get("guided_decoding",False),
                       enforce_eager=config.get('enforce_eager',True),gpu_memory_utilization=config.get('gpu_memory_utilization',0.85))
    ledger = Ledger(directory / alias)
    ledger.event("run_start", settings=model.settings, model_load_seconds=model.load_seconds)
    trials = [t for t in manifest["trials"] if t["model"] == alias]
    # Keep a complete base cluster near each checkpoint; bounded-memory batches.
    pair_list=list(pairs.values())
    block_size=config.get("cluster_batch_pairs",4 if config["organizations"]==["flat"] else 1)
    for block_start in range(0,len(pair_list),block_size):
        block=pair_list[block_start:block_start+block_size]
        block_ids={p["pair_id"] for p in block}
        cluster_trials = [t for t in trials if t["pair_id"] in block_ids]
        requests, inputs = [], {}
        for t in cluster_trials:
            p=pairs[t["pair_id"]]
            world = p["worlds"][t["world"]]
            rs = repeat(thaw(corpus[p["pair_id"]]["reports"][t["world"]]), corpus[p["pair_id"]]["selected"], t["condition"], p["split"])
            inputs[t["trial_id"]] = rs
            if t["organization"] == "flat":
                requests.append({"trial": t, "stage": "root", "prompt": make_prompt(world, rs, t["policy"])})
            else:
                for i, branch in enumerate(partition(rs, p["seed"])):
                    requests.append({"trial": t, "stage": "manager" + str(i),
                                     "prompt": make_prompt(world, branch, t["policy"], role="manager")})
        calls = execute_requests(requests, model, ledger)
        root_requests = []
        for t in cluster_trials:
            if t["organization"] == "flat": continue
            p=pairs[t["pair_id"]]
            world, rs = p["worlds"][t["world"]], inputs[t["trial_id"]]
            summaries = []
            for i in range(2):
                raw = calls[(t["trial_id"], "manager" + str(i))]["response"]
                obj, status = parse(raw["text"], world["tie_order"] + ["NONE"], manager=True)
                summaries.append({"manager": i, "summary": obj if obj is not None else raw["text"], "parse_status": status})
            root_requests.append({"trial": t, "stage": "root",
                "prompt": make_prompt(world, [], t["policy"], summaries=summaries, public_registry=registry(rs),
                                      public_ancestry=ancestry_registry(rs) if config.get('root_ancestry_registry',False) else None)})
        calls.update(execute_requests(root_requests, model, ledger))
        rows = []
        for t in cluster_trials:
            p=pairs[t["pair_id"]]
            world, rs = p["worlds"][t["world"]], inputs[t["trial_id"]]
            current = [v for (tid, stage), v in calls.items() if tid == t["trial_id"]]
            root_call = calls[(t["trial_id"], "root")]
            score = score_root(root_call["response"], world, p["evaluation"]["oracle"][t["world"]], rs)
            summary_scores = []
            if t["organization"] != "flat":
                for i, branch in enumerate(partition(rs, p["seed"])):
                    raw = calls[(t["trial_id"], "manager" + str(i))]["response"]
                    obj, status = parse(raw["text"], world["tie_order"] + ["NONE"], manager=True)
                    if raw["finish_reason"] == "length": obj = None; status = "truncated"
                    summary_scores.append({"manager": i, "parse_status": status, **score_assertions(obj, branch)})
                if any(s["parse_status"] != "valid" for s in summary_scores):
                    score["operational_failure"] = True
                    score["root_choice_correct_despite_summary_failure"] = score["correct"]
                    score["correct"] = False
            rows.append({**t, "kind": p["evaluation"]["kind"], "family": p["evaluation"]["family"],
                         "decision_changed": p["evaluation"]["decision_changed"], **score,
                         "summary_scores": summary_scores,
                         "calls": len(current), "input_tokens": sum(c["response"]["input_tokens"] for c in current),
                         "output_tokens": sum(c["response"]["output_tokens"] for c in current),
                         "inference_seconds_allocated": sum(c["response"]["allocated_inference_seconds"] for c in current),
                         "displayed_reports": len(rs), "original_model_worker_calls": 0,
                         "verification_operations": len({r.claim.verification_execution_identifier for r in rs}),
                         "distinct_evidence_sources": len({s for r in rs for s in r.claim.source_identifiers}),
                         "request_hashes": [c["request_hash"] for c in current],
                         "graphs": build_graphs(world, rs, t["organization"], p["seed"])})
        for p in block:
            cluster_rows=[r for r in rows if r["pair_id"]==p["pair_id"]]
            immutable_json(directory / alias / "scores" / (p["pair_id"] + ".json"), cluster_rows)
            ledger.event("cluster_complete", pair_id=p["pair_id"], trajectories=len(cluster_rows))
            print(canonical({"cluster_complete": p["pair_id"], "trajectories": len(cluster_rows)}), flush=True)
    ledger.event("run_complete", trajectories=len(trials))
