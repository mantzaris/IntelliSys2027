"""Family/seed-aware deterministic aggregation; no turns as independent samples."""
from collections import defaultdict
from pathlib import Path
import csv
import json
import random
import statistics
from .eligibility import exclusions


def paired_success(rows: list[dict]) -> dict[tuple,int]:
    families=defaultdict(dict)
    for r in rows:
        key=(r["seed"],r["family_id"])
        if r["world"] in families[key]:raise ValueError("Duplicate family-world observation")
        families[key][r["world"]]=bool(r["success"])
    if any(set(worlds)!={"authorized","hypothetical"} for worlds in families.values()):
        raise ValueError("Paired success requires both worlds; no dropping failures")
    return {key:int(all(worlds.values())) for key,worlds in families.items()}


def contrast(left: list[dict], right: list[dict], draws: int=10000, seed: int=90210) -> dict:
    a,b=paired_success(left),paired_success(right)
    if set(a)!=set(b):raise ValueError("Comparators must have identical seed-family coverage")
    seeds=sorted({s for s,f in a});families=sorted({f for s,f in a})
    if len(a)!=len(seeds)*len(families):raise ValueError("Incomplete seed-family grid")
    differences={(s,f):a[s,f]-b[s,f] for s in seeds for f in families}
    rng=random.Random(seed);samples=[]
    for _ in range(draws):
        ss=rng.choices(seeds,k=len(seeds));ff=rng.choices(families,k=len(families))
        samples.append(statistics.mean(differences[s,f] for s in ss for f in ff))
    samples.sort()
    return {"difference":statistics.mean(differences.values()),"ci95":[samples[int(.025*draws)],samples[min(draws-1,int(.975*draws))]],
            "families":len(families),"seeds":len(seeds),"per_seed":{str(s):statistics.mean(differences[s,f] for f in families) for s in seeds},
            "analysis":"paired two-way seed/family percentile bootstrap; only three seeds cannot characterize seed tails reliably"}


def holm(pvalues: dict[str,float]) -> dict[str,float]:
    ordered=sorted(pvalues,key=pvalues.get);out={};last=0.
    for i,key in enumerate(ordered):
        last=max(last,min(1.,(len(ordered)-i)*pvalues[key]));out[key]=last
    return out


def summarize_artifacts(root: Path, output: Path):
    output.mkdir(parents=True,exist_ok=True)
    table=[];excluded=exclusions(root.parent)
    for status in sorted(root.glob("runs/*/status.json")):
        meta=json.loads(status.read_text());run=status.parent
        for path in sorted(run.glob("*_summary.json")):
            rows=json.loads(path.read_text())
            if not isinstance(rows,list) or not rows:continue
            pairs=paired_success(rows)
            table.append({"run_id":meta["run_id"],"model":meta["config"]["model"],"training_condition":meta["config"]["condition"],
                          "evaluation":path.stem,"seed":meta["config"]["seed"],"phase":meta["config"]["phase"],
                          "families":len(pairs),"paired_success":statistics.mean(pairs.values()),
                          "conversation_success":statistics.mean(r["success"] for r in rows),
                          "recall_accuracy":statistics.mean(r["recall_accuracy"] for r in rows),
                          "gpu_reserved_seconds":meta["gpu_reserved_seconds"],"status":meta["status"],
                          "scientific_exclusion":excluded.get(meta["run_id"])})
    if table:
        with (output/"executed_results.csv").open("w",newline="") as f:
            writer=csv.DictWriter(f,fieldnames=list(table[0]),lineterminator="\n");writer.writeheader();writer.writerows(table)
    (output/"executed_results.json").write_text(json.dumps(table,indent=2)+"\n")
    return table
