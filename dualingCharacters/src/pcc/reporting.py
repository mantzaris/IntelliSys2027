"""Regenerate compact measured tables, figures and evidence trace from saved runs."""
from pathlib import Path
import hashlib
import json
import statistics
from .analysis import contrast, summarize_artifacts
from .diagnostics import jsonlines, write_audit


def generate(root: Path):
    import os
    os.environ.setdefault("MPLCONFIGDIR",str(root/"artifacts/matplotlib-cache"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    output=root/"reports";figures=output/"figures";figures.mkdir(parents=True,exist_ok=True)
    tables=summarize_artifacts(root/"artifacts",output/"tables")
    audits=write_audit(root/"artifacts",output/"tables")
    exclusions=json.loads((root/"configs/run_exclusions.json").read_text())
    valid=[a for a in audits if a["run_id"] not in exclusions and "after" in a and a["status"]=="completed"]
    trace=[]
    fig,ax=plt.subplots(figsize=(6,3.6))
    for a in valid:
        run=root/"artifacts/runs"/a["run_id"]
        path=run/"training/loss.jsonl";losses=jsonlines(path)
        if losses:
            ax.plot([r["step"] for r in losses],[r["loss"] for r in losses],label=a["run_id"])
            trace.append({"figure":"training_curves","path":str(path.relative_to(root)),"sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
    ax.set(xlabel="Optimizer step",ylabel="Completion-token loss",title="Engineering pilots: actual LoRA updates")
    if valid:ax.legend(fontsize=7)
    fig.tight_layout();fig.savefig(figures/"training_curves.pdf");fig.savefig(figures/"training_curves.png",dpi=160);plt.close(fig)
    fig,ax=plt.subplots(figsize=(6,3.6))
    for a in valid:
        before=a["before"]["paired_success"];after=a["after"]["paired_success"]
        ax.scatter(a["resources"]["gpu_reserved_seconds"]/60,100*(after-before),label=a["run_id"])
    ax.axhline(0,color="grey",lw=.8);ax.set(xlabel="Total reserved GPU minutes (collection + training + evaluation)",
             ylabel="Paired success change (percentage points)",title="Pilot gain versus total process compute; one seed, four families")
    if valid:ax.legend(fontsize=7)
    fig.tight_layout();fig.savefig(figures/"pilot_gain_vs_compute.pdf");fig.savefig(figures/"pilot_gain_vs_compute.png",dpi=160);plt.close(fig)
    # Method diagram drawn from the specification; no fabricated result curves.
    fig,ax=plt.subplots(figsize=(9,3.6));ax.set_axis_off()
    nodes={"source":(.12,.6,"Immutable attributed\nuser/assistant transcript"),"memory":(.43,.6,"Bounded shared memory\n+ source-only retrieval"),
           "learner":(.76,.6,"Jekyll / defender\nLoRA policy"),"characters":(.43,.1,"Frozen character weights\nprivate histories + peer channel"),
           "oracle":(.76,.1,"Private evaluator\nscore / training targets only")}
    for x,y,label in nodes.values():ax.text(x,y,label,ha="center",va="center",bbox={"boxstyle":"round,pad=0.6","fc":"#edf4fa","ec":"#49647a"},fontsize=9)
    for a,b in [("source","memory"),("memory","learner"),("characters","memory"),("learner","oracle")]:
        x,y,_=nodes[a];u,v,_=nodes[b];ax.annotate("",(u,v),xytext=(x,y),arrowprops={"arrowstyle":"->","color":"#49647a","shrinkA":45,"shrinkB":45})
    ax.set_xlim(-.05,1.05);ax.set_ylim(-.15,.95);fig.tight_layout();fig.savefig(figures/"method.pdf");fig.savefig(figures/"method.png",dpi=160);plt.close(fig)
    pilot_effect=None
    c3=root/"artifacts/runs/pilot-c3-002/after_summary.json";c5=root/"artifacts/runs/pilot-c5-001/after_summary.json"
    if c3.exists() and c5.exists():
        pilot_effect=contrast(json.loads(c5.read_text()),json.loads(c3.read_text()))
        pilot_effect["qualification"]="Exploratory engineering pilot only; four families, one training seed, old optional-peer protocol. Not H1 evidence."
        (output/"tables/exploratory_pilot_contrast.json").write_text(json.dumps(pilot_effect,indent=2)+"\n")
    lines=["# Executed pilot evidence — not confirmatory results","", "Generated from saved run artifacts by `PYTHONPATH=src python -m pcc.reporting`.","",
           "| Run | Before paired success | After paired success | GPU minutes | Status |","|---|---:|---:|---:|---|"]
    for a in valid:
        lines.append(f"| {a['run_id']} | {a['before']['paired_success']:.3f} | {a['after']['paired_success']:.3f} | {a['resources']['gpu_reserved_seconds']/60:.2f} | Pilot, one seed |")
    if pilot_effect:
        lo,hi=pilot_effect['ci95'];lines.extend(["",f"Exploratory C5−C3 paired difference: {pilot_effect['difference']:+.3f}; family-bootstrap 95% interval [{lo:+.3f}, {hi:+.3f}]. This four-family interval does not estimate training-seed variation and cannot establish the primary hypothesis."])
    lines.extend(["","Both evaluated learners had antagonists removed. This is an antagonist-free pilot retest, not established general transfer. The revised mandatory communication protocol requires a fresh mechanism audit.","",
                  "Main three-seed results, learned ablations, independent-family replication, external scores, horizon curves, fixed-state recovery curves and human validation remain pending. Empty cells and absent figures must not be filled with invented measurements.","",
                  "Invalid/engineering-only runs are retained in `configs/run_exclusions.json`; their resource usage remains counted."])
    (output/"PILOT_RESULTS.md").write_text("\n".join(lines)+"\n")
    (output/"tables/figure_trace.json").write_text(json.dumps(trace,indent=2)+"\n")
    tex=[r"\begin{table}[ht]",r"\centering",r"\caption{Engineering pilot only: one seed, four paired families.}",r"\begin{tabular}{lrrr}\toprule",r"Condition & Before & After & GPU min.\\\midrule"]
    for a in valid:tex.append(f"{a['condition']} & {a['before']['paired_success']:.2f} & {a['after']['paired_success']:.2f} & {a['resources']['gpu_reserved_seconds']/60:.2f}\\\\")
    tex.extend([r"\bottomrule\end{tabular}\end{table}","These pilot values do not establish the prespecified primary effect or a relationship mechanism. Confirmatory results remain unavailable."])
    (root/"paper/generated_results.tex").write_text("\n".join(tex)+"\n")
    return tables


if __name__=="__main__":generate(Path.cwd())
