"""Prespecified descriptive transfer metrics and transparent failure examples."""
from collections import defaultdict, Counter
from pathlib import Path
import hashlib
import json
import statistics
from .analysis import paired_success
from .diagnostics import jsonlines, trace_path
from .environment import make_family
from .resources import sha256
from .eligibility import exclusions
from .study_analysis import write_csv


def final_diagnostics(row: dict, horizon: int) -> dict:
    number=int(row["family_id"].split("-")[-1]);s=next(s for s in make_family(row["split"],number,horizon) if s.world==row["world"])
    slot,alternate=s.events[s.switch_turn-1].updates[0]
    parsed=row["generation"]["parsed"];plan=parsed.get("plan",[]);gold=row["target"]
    selected=plan[slot] if isinstance(plan,list) and len(plan)>slot else None
    return {"authorized_update_accepted":selected==alternate if row["world"]=="authorized" else None,
            "hypothetical_falsely_accepted":selected==alternate if row["world"]=="hypothetical" else None,
            "unnecessary_clarification":bool(parsed.get("clarify")) and not gold["clarify"],
            "missing_clarification":bool(gold["clarify"]) and parsed.get("clarify")!=gold["clarify"],
            "all_null_plan_proxy":isinstance(plan,list) and bool(plan) and all(x is None for x in plan),
            "recalled_but_violated":row["metrics"]["recall_accuracy"]==1 and not row["metrics"]["success"],
            "malformed":not bool(parsed),"source_reference_error":row["metrics"]["evidence_accuracy"]<1,
            "dependency_error":row["metrics"]["dependency_accuracy"]<1,
            "switch_dependency_distance":horizon-s.switch_turn,
            "mean_source_dependency_distance":statistics.mean(horizon-(index+1)//2 for index in gold["evidence"] if index is not None),
            "max_source_dependency_distance":max(horizon-(index+1)//2 for index in gold["evidence"] if index is not None)}


def analyze(root: Path):
    tables=root/"reports/tables";tables.mkdir(parents=True,exist_ok=True)
    transfer=[];diagnostics=[];failures=defaultdict(list);recovery=[];external=[];trace=[];excluded=exclusions(root)
    freeze_path=root/"configs/freeze.json"
    subset={f"test-{i:04d}" for i in json.loads(freeze_path.read_text())["plan"]["extension_family_numbers"]} if freeze_path.exists() else set()
    for status_path in sorted((root/"artifacts/runs").glob("*/status.json")):
        meta=json.loads(status_path.read_text());run=status_path.parent;name=run.name
        if meta["status"]!="completed" or meta["config"]["phase"]!="confirmatory" or name in excluded:continue
        cfg=meta["config"];identity={"run_id":name,"model":cfg["model"],"condition":cfg["condition"],"seed":cfg["seed"]}
        summary=run/"evaluation_summary.json"
        if summary.exists():
            rows=json.loads(summary.read_text());paired=paired_success(rows)
            transfer.append({**identity,"setting":meta.get("extension","antagonist-free"),"horizon":rows[0]["horizon"],"families":len(paired),
                             "paired_success":statistics.mean(paired.values()),"conversation_success":statistics.mean(r["success"] for r in rows),
                             "gpu_reserved_seconds":meta["gpu_reserved_seconds"],"input_tokens":meta["input_tokens"],"output_tokens":meta["output_tokens"]})
            if subset and rows[0]["horizon"]==64 and "extension" not in meta:
                selected=[r for r in rows if r["family_id"] in subset]
                transfer.append({**identity,"setting":"horizon64-subset","horizon":64,"families":len(paired_success(selected)),
                                 "paired_success":statistics.mean(paired_success(selected).values()),"conversation_success":statistics.mean(r["success"] for r in selected),
                                 "gpu_reserved_seconds":0,"input_tokens":sum(r["input_tokens"] for r in selected),"output_tokens":sum(r["output_tokens"] for r in selected)})
            trace.append({"path":str(summary.relative_to(root)),"sha256":sha256(summary)})
            horizon=rows[0]["horizon"];finals=[r for r in jsonlines(run/"evaluation.jsonl") if r["turn"]==horizon]
            measurements=[final_diagnostics(r,horizon) for r in finals]
            aggregate={k:statistics.mean(x[k] for x in measurements if x[k] is not None) if any(x[k] is not None for x in measurements) else None for k in measurements[0]}
            diagnostics.append({**identity,**aggregate,"recall_accuracy":statistics.mean(r["recall_accuracy"] for r in rows),
                                "behavioral_plan_accuracy":statistics.mean(r["plan_accuracy"] for r in rows),"dependency_accuracy":statistics.mean(r["dependency_accuracy"] for r in rows)})
            if name.startswith("main-"):
                for row,m in zip(finals,measurements):
                    categories=[k for k,v in m.items() if v is True and k not in {"authorized_update_accepted"}]
                    if row["metrics"]["success"]:categories.append("success")
                    if row["world"]=="authorized" and not m["authorized_update_accepted"]:categories.append("authorized_update_rejected")
                    for category in categories:
                        key=f"{name}:{row['family_id']}:{row['world']}"
                        failures[category].append((hashlib.sha256(("failure-audit-v1:"+key).encode()).hexdigest(),{**identity,"family_id":row["family_id"],"world":row["world"],
                                     "category":category,"response":row["generation"]["raw"],"target":row["target"],"source_path":str(trace_path(run/"evaluation.jsonl").relative_to(root))}))
        path=run/"recovery.jsonl"
        if path.exists():
            rows=jsonlines(path)
            for attempt in range(1,5):
                selected=[r for r in rows if r["attempt"]==attempt]
                recovery.append({**identity,"attempt":attempt,"cases":len(selected),"model_calls_per_case":attempt*2,
                                 "cumulative_recovery":statistics.mean(r["first_recovered"] is not None for r in selected),
                                 "cumulative_detection":statistics.mean(r.get("first_detected") is not None for r in selected),
                                 "not_recovered":sum(r["first_recovered"] is None for r in selected)})
            trace.append({"path":str(path.relative_to(root)),"sha256":sha256(path)})
        path=run/"external_judgments.jsonl"
        if path.exists():
            by_run=defaultdict(list)
            for row in jsonlines(path):by_run[row["source_run"]].append(row)
            for source,rows in by_run.items():external.append({"source_run":source,"judge_model":cfg["model"],"questions":len(rows),
                                "adapted_judge_accuracy":statistics.mean(r["label"] for r in rows),"calibration_threshold_passed":all(r["calibration_threshold_passed"] for r in rows),
                                "status":"exploratory adapted judge; official/human scoring pending"})
    samples=[value for group in failures.values() for _,value in sorted(group)[:3]]
    for name,rows in (("transfer",transfer),("secondary_metrics",diagnostics),("recovery",recovery),("external",external),("failure_examples",samples),("secondary_trace",trace)):
        (tables/(name+".json")).write_text(json.dumps(rows,indent=2)+"\n")
        if name not in {"failure_examples","secondary_trace"}:write_csv(tables/(name+".csv"),rows)
    return transfer,recovery


if __name__=="__main__":analyze(Path.cwd())
