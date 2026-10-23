"""Post-baseline descriptive reporting; never a new confirmatory hypothesis test.

Reads all completed primary conditions and all predefined domain/structure cells.
No model calls, checkpoint selection, sampling, p-values or experimental mutations.
The pre-test analysis remains unchanged in src/pcc/{study,secondary}_analysis.py.
"""
from collections import defaultdict
from pathlib import Path
import csv
import hashlib
import json
import statistics
from pcc.analysis import paired_success
from pcc.resources import sha256
from pcc.eligibility import exclusions


def write_table(path: Path, rows: list[dict]):
    path.with_suffix(".json").write_text(json.dumps(rows,indent=2)+"\n")
    if not rows:
        path.with_suffix(".csv").write_text("")
        return
    with path.with_suffix(".csv").open("w",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator="\n")
        writer.writeheader();writer.writerows(rows)


def regenerate(root: Path):
    excluded=exclusions(root)
    out=root/"reports/tables";out.mkdir(parents=True,exist_ok=True)
    inputs={};cells=[];domains=[];exposure=[];resources=[];collections={}
    statuses=[]
    def read(path):
        data=path.read_bytes()
        inputs[str(path.relative_to(root))]=hashlib.sha256(data).hexdigest()
        return json.loads(data)
    for path in sorted((root/"artifacts/runs").glob("*/status.json")):
        data=path.read_bytes();meta=json.loads(data)
        if meta["status"] in {"completed","failed"}:
            inputs[str(path.relative_to(root))]=hashlib.sha256(data).hexdigest()
            statuses.append((path.parent,meta))
    # Link training exposure to its actual supervision bytes, including fresh
    # infrastructure resume IDs, rather than guessing a collection filename.
    for run,meta in statuses:
        counts=run/"supervision.counts.json";examples=run/"supervision.jsonl"
        if meta["status"]=="completed" and counts.exists() and examples.exists() and run.name not in excluded:
            cfg=meta["config"];key=(cfg["model"],cfg["condition"],cfg["seed"],sha256(examples))
            if key in collections:raise ValueError("Ambiguous identical supervision sources")
            inputs[str(examples.relative_to(root))]=key[-1]
            collections[key]=(run.name,read(counts))
    for run,meta in statuses:
        cfg=meta["config"];identity={"run_id":run.name,"model":cfg["model"],"condition":cfg["condition"],"seed":cfg["seed"]}
        resources.append({**identity,"phase":cfg["phase"],"status":meta["status"],"engine":cfg.get("engine","not recorded in early configuration"),
                          "reserved_gpu_seconds":meta["gpu_reserved_seconds"],
                          "sampled_busy_seconds":meta.get("sampled_gpu_busy_seconds"),
                          "sampled_utilization_weighted_seconds":meta.get("utilization_weighted_seconds"),
                          "model_load_seconds":meta.get("model_load_seconds"),
                          "inference_input_tokens":meta["input_tokens"],"generated_tokens":meta["output_tokens"],
                          "training_input_tokens":meta["train_tokens"],"generation_requests":meta["model_calls"],
                          "peak_vram_GiB":meta["peak_vram_bytes"]/2**30,
                          "vram_definition":meta.get("vram_measurement","torch allocated peak"),
                          "known_cost_usd":meta.get("known_cost_usd"),"source_commit":meta["code_commit"]})
        if meta["status"]!="completed" or cfg["phase"]!="confirmatory" or run.name in excluded:continue
        training=run/"training/training_summary.json"
        if training.exists():
            report=read(training);key=(cfg["model"],cfg["condition"],cfg["seed"],meta.get("supervision_sha256"))
            if key not in collections:raise ValueError("Completed fit lacks its verified supervision source")
            collection,counts=collections[key]
            exposure.append({**identity,"collection_run":collection,"supervision_sha256":key[-1],
                             "optimizer_steps_in_this_process":report["optimizer_steps"],
                             "training_input_tokens_in_this_process":report["input_tokens"],
                             "supervised_target_tokens_in_this_process":report["supervised_tokens"],
                             "unique_windows_sampled_into_buffer":report["unique_windows"],
                             "window_reuses_including_replayed_prefix":report["reused_windows"],
                             "attempted_windows":counts["attempted_windows"],"source_ineligible":counts["source_ineligible"],
                             "clean_eligible":counts["clean_valid"],"failed_eligible":counts["failed_eligible"],
                             "model_candidates_attempted":counts["candidate_attempts"],"model_candidates_valid":counts["candidate_valid"],
                             "model_candidates_discarded":counts["candidate_discarded"],"oracle_teacher_examples":counts["gold_teacher_examples"],
                             "resumed_from_run":meta.get("supersedes_run_id"),"adapter_changed":report["adapter_changed"]})
        summary=run/"evaluation_summary.json"
        if not summary.exists() or "extension" in meta or not run.name.startswith(("main-","base-")):continue
        rows=read(summary)
        if len(rows)!=480 or {r["horizon"] for r in rows}!={64}:raise ValueError("Incomplete primary evaluation")
        by_cell=defaultdict(list);by_domain=defaultdict(list)
        for row in rows:
            by_cell[row["domain"],bool(row["structural_holdout"])].append(row)
            group="familiar_domain" if row["domain"] in {"event","software"} else "held_out_framing"
            by_domain[group].append(row)
        for (domain,structural),group in sorted(by_cell.items()):
            pairs=paired_success(group)
            if len(pairs)!=30:raise ValueError("Domain-by-pattern balance differs from the frozen design")
            cells.append({**identity,"domain":domain,"structural_holdout":structural,"families":len(pairs),
                          "paired_successes":sum(pairs.values()),"paired_success":statistics.mean(pairs.values()),
                          "conversation_success":statistics.mean(r["success"] for r in group),
                          "recall_accuracy":statistics.mean(r["recall_accuracy"] for r in group),
                          "behavioral_plan_accuracy":statistics.mean(r["plan_accuracy"] for r in group)})
        for group_name,group in sorted(by_domain.items()):
            pairs=paired_success(group)
            if len(pairs)!=120:raise ValueError("Domain-group sample differs from the frozen design")
            domains.append({**identity,"domain_group":group_name,"families":len(pairs),"paired_successes":sum(pairs.values()),
                            "paired_success":statistics.mean(pairs.values()),"conversation_success":statistics.mean(r["success"] for r in group)})
    for name,rows in (("domain_structure",cells),("domain_transfer",domains),("training_exposure",exposure),("resources_by_run",resources)):
        write_table(out/("exploratory_"+name),rows)
    trace={"classification":"Descriptive reporting code added after baseline outcomes, before first trained test outcomes. No additional confirmatory tests.",
           "selection":"Every completed primary run, every predefined domain and structural cell; per-seed rows, no outcome-based selection",
           "dependence":"The same families repeat across seeds; do not count seed-family rows or paired worlds as independent families.",
           "training_counts":"Window counts describe the packed stream buffer, including replay on resume. Target-token and optimizer-step counts are actual work in that process. Failed process costs remain in the resource table.",
           "resource_scope":"Completed and failed runs only; active reservations are excluded from this stable descriptive table. Five-second activity samples are approximate and absent for early runs. Dollars remain unknown without an actual rate.",
           "analysis_source_sha256":sha256(Path(__file__).resolve()),"inputs":inputs}
    (out/"exploratory_descriptive_trace.json").write_text(json.dumps(trace,indent=2)+"\n")
    print(json.dumps({"domain_cells":len(cells),"domain_groups":len(domains),"completed_fit_processes":len(exposure),"finished_run_records":len(resources)}))


if __name__=="__main__":regenerate(Path(__file__).resolve().parents[1])
