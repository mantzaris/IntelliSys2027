"""One-command regeneration of the author-review evidence package."""
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import statistics
from .analysis import paired_success, contrast
from .diagnostics import jsonlines
from .resources import sha256, used_seconds
from .study_analysis import analyze as main_analysis
from .secondary_analysis import analyze as secondary_analysis


def regenerate(root: Path):
    from .reporting import generate
    from .mechanism_analysis import audit
    from .validation import human_packet
    generate(root);main,contrasts=main_analysis(root);transfer,recovery=secondary_analysis(root)
    mechanisms=audit(root);human_count=human_packet(root)
    statuses=[json.loads(p.read_text()) for p in sorted((root/"artifacts/runs").glob("*/status.json"))]
    first=min(datetime.fromisoformat(r["started_utc"].replace("Z","+00:00")) for r in statuses)
    observed_end=max(datetime.fromisoformat(r["started_utc"].replace("Z","+00:00")).timestamp()+r["gpu_reserved_seconds"] for r in statuses)
    resources={"reserved_gpu_hours":used_seconds(root/"artifacts/run_registry.jsonl")/3600,
               "observed_pod_wall_hours_first_to_latest_run":(observed_end-first.timestamp())/3600,
               "pod_start_time":None,"actual_hourly_rate_usd":None,"actual_cost_usd":None,
               "inference_input_tokens":sum(r["input_tokens"] for r in statuses),"generated_output_tokens":sum(r["output_tokens"] for r in statuses),
               "training_input_tokens":sum(r["train_tokens"] for r in statuses),"generation_requests":sum(r["model_calls"] for r in statuses),
               "runs":len(statuses),"completed":sum(r["status"]=="completed" for r in statuses),
               "qualification":"Reservation includes model load and failed runs. Observed pod interval is not total billed lifetime. Five-second utilization telemetry exists only for later runs."}
    (root/"reports/tables/resource_totals.json").write_text(json.dumps(resources,indent=2)+"\n")
    pilots=[]
    for name in ("pilot-v4-qwen-base","pilot-v4-qwen-c3-eval","pilot-v4-qwen-c5-eval","pilot-v4-phi-base","pilot-v4-phi-c5-eval"):
        path=root/"artifacts/runs"/name/"evaluation_summary.json"
        if path.exists():
            rows=json.loads(path.read_text());pairs=paired_success(rows)
            pilots.append({"run_id":name,"paired_success":statistics.mean(pairs.values()),"families":len(pairs),"conversation_success":statistics.mean(r["success"] for r in rows),"sha256":sha256(path)})
    (root/"reports/tables/matched_pilots.json").write_text(json.dumps(pilots,indent=2)+"\n")
    c3=root/"artifacts/runs/pilot-v4-qwen-c3-eval/evaluation_summary.json";c5=root/"artifacts/runs/pilot-v4-qwen-c5-eval/evaluation_summary.json"
    effect=contrast(json.loads(c5.read_text()),json.loads(c3.read_text())) if c3.exists() and c5.exists() else None
    if effect:
        effect["qualification"]="One-seed 16-family pilot at 32 turns; concatenated training packing and pre-final alias history. Not the confirmatory estimand."
        (root/"reports/tables/matched_pilot_contrast.json").write_text(json.dumps(effect,indent=2)+"\n")
    os.environ.setdefault("MPLCONFIGDIR",str(root/"artifacts/matplotlib-cache"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    figures=root/"reports/figures"
    # Never draw invented pending curves. An explicit empty panel is an audit artifact.
    for kind in ("horizon_performance","recovery_curve","gain_versus_compute"):
        fig,ax=plt.subplots(figsize=(6.4,3.8));drawn=False
        if kind=="horizon_performance":
            for condition in ("base","C1","C3","C4","C5"):
                points=defaultdict(list)
                for r in transfer:
                    if r["model"]=="qwen" and r["condition"]==condition and r["seed"]==17 and r["setting"] in {"horizon64-subset","horizon32","horizon128"}:
                        points[r["horizon"]].append(r["paired_success"])
                if points:
                    xs=sorted(points);ax.plot(xs,[statistics.mean(points[x]) for x in xs],marker="o",label=condition);drawn=True
            ax.set(xlabel="User/assistant turns",ylabel="Paired task success",ylim=(0,1),title="Antagonist-free horizon sensitivity; seed 17, common families")
        elif kind=="recovery_curve":
            for condition in ("base","C1","C3","C4","C5"):
                points=defaultdict(list)
                for r in recovery:
                    if r["condition"]==condition:points[r["attempt"]].append(r["cumulative_recovery"])
                if points:
                    xs=sorted(points);ax.plot(xs,[statistics.mean(points[x]) for x in xs],marker="o",label=condition);drawn=True
            ax.set(xlabel="Recovery attempt (plus one separate diagnosis call)",ylabel="Cumulative recovery probability",ylim=(0,1),title="Identical faulty states; unrecovered cases retained")
        else:
            base=next((r["paired_success"] for r in transfer if r["run_id"]=="base-qwen-eval"),None)
            if base is not None:
                for r in main:
                    if r["model"]=="qwen" and r["paired_success"] is not None:
                        ax.scatter(r["gpu_reserved_seconds"]/3600,100*(r["paired_success"]-base),label=r["condition"]);drawn=True
            ax.axhline(0,color="gray",lw=.7)
            ax.set(xlabel="Condition's total reserved GPU hours, including primary evaluation",ylabel="Gain over untrained base (percentage points)",title="Learning gain versus measured process compute")
        if drawn:ax.legend(fontsize=8)
        else:ax.text(.5,.5,"Required measurements pending",ha="center",va="center",transform=ax.transAxes)
        fig.tight_layout();fig.savefig(figures/(kind+".pdf"));fig.savefig(figures/(kind+".png"),dpi=160);plt.close(fig)
    figure_trace={name:sha256(root/name) for name in ("reports/tables/main_results.json","reports/tables/transfer.json","reports/tables/recovery.json","src/pcc/package.py")}
    (root/"reports/tables/publication_figure_trace.json").write_text(json.dumps(figure_trace,indent=2)+"\n")
    fig,axes=plt.subplots(1,2,figsize=(10,3.5));loss_trace={}
    for ax,model in zip(axes,("qwen","phi")):
        for condition in ("C1","C3","C4","C5","C6","A1","A2","A3","C2"):
            points=defaultdict(list)
            for meta in statuses:
                if not meta["run_id"].startswith(f"main-{model}-") or meta["status"]!="completed" or meta["config"]["condition"]!=condition:continue
                path=root/"artifacts/runs"/meta["run_id"]/"training/loss.jsonl"
                if not path.exists():continue
                round_index=1 if "-r1-" in meta["run_id"] else 0
                for r in jsonlines(path):points[r["step"]+round_index*meta["config"]["train_steps"]].append(r["loss"])
                loss_trace[str(path.relative_to(root))]=sha256(path)
            if points:
                xs=sorted(points);ax.plot(xs,[statistics.mean(points[x]) for x in xs],label=condition,lw=.8)
        ax.set(title=model,xlabel="Optimizer step across two rounds",ylabel="Completion-token loss")
        if ax.lines:ax.legend(fontsize=6)
        else:ax.text(.5,.5,"Main training pending",ha="center",transform=ax.transAxes)
    fig.tight_layout();fig.savefig(figures/"main_training_curves.pdf");fig.savefig(figures/"main_training_curves.png",dpi=160);plt.close(fig)
    (root/"reports/tables/main_training_trace.json").write_text(json.dumps(loss_trace,indent=2)+"\n")
    lines=["# Author-review evidence package","","This is not a submission-ready paper. Human scientific review remains required.","",
           f"Measured reservation: {resources['reserved_gpu_hours']:.3f} GPU-hours; inference {resources['inference_input_tokens']:,} input and {resources['generated_output_tokens']:,} output tokens; {resources['training_input_tokens']:,} training input tokens. Actual dollar cost is unknown.","",
           "## Matched learning pilots (one seed; 32 turns)","","| Run | Paired success | Conversations |","|---|---:|---:|"]
    for r in pilots:lines.append(f"| {r['run_id']} | {r['paired_success']:.4f} ({r['families']} families) | {r['conversation_success']:.4f} |")
    if effect:lines.extend(["",f"Exploratory C5−C3 difference {effect['difference']:+.4f}, 95% family interval [{effect['ci95'][0]:+.4f}, {effect['ci95'][1]:+.4f}]. This does not estimate training-seed variation or establish H1."])
    lines.extend(["","## Main grid","","| Model | Condition | Seeds | Paired success | Status |","|---|---|---:|---:|---|"])
    for r in main:lines.append(f"| {r['model']} | {r['condition']} | {r['executed_seeds']} | {r['paired_success'] if r['paired_success'] is not None else '—'} | {r['status']} |")
    for result in contrasts:lines.append(f"\n{result['model']} {result['contrast']}: {result['difference']:+.4f}, paired seed/family interval {result['ci95']}; {result['seeds']} seeds.")
    lines.extend(["","## Unfinished or limited evidence","",f"Human-review packet: {human_count} actual outputs; no human ratings have been supplied.",
                  "External evaluation uses a fixed 50-question subset and an adapted independent-family judge; it is not an official comparable LongMemEval score. Structured synthetic planning and scripted users limit naturalistic and domain-transfer claims.",
                  "No coalition or narrative-profile benefit follows merely from peer messages, character labels, or a positive point estimate. Consult the ablations and mechanism diagnostics.",
                  "Empty tables and panels identify unexecuted requirements. The actual run registry, not queued commands, determines completion.","",
                  "Regenerate: `PYTHONPATH=src .venv/bin/python -m pcc.package`, then `bash scripts/build_paper.sh`."])
    (root/"reports/AUTHOR_REVIEW.md").write_text("\n".join(lines)+"\n")
    return resources


if __name__=="__main__":print(json.dumps(regenerate(Path.cwd()),indent=2))
