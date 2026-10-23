"""Frozen deterministic main-grid analysis, with explicit missing cells."""
from collections import defaultdict
from pathlib import Path
import csv
import json
import statistics
import numpy as np
from .analysis import paired_success, contrast, holm
from .resources import sha256


def write_csv(path: Path,rows: list[dict]):
    if not rows:return
    with path.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n");w.writeheader();w.writerows(rows)


def family_signflip_p(left: list[dict],right: list[dict],draws: int=20000) -> float:
    """Paired family randomization conditional on the observed training seeds."""
    a,b=paired_success(left),paired_success(right)
    if set(a)!=set(b):raise ValueError("Mismatched paired observations")
    families=sorted({f for s,f in a});seeds=sorted({s for s,f in a})
    d=np.array([statistics.mean(a[s,f]-b[s,f] for s in seeds) for f in families])
    observed=abs(d.mean());rng=np.random.default_rng(7241)
    perm=(rng.choice([-1,1],size=(draws,len(d)))*d).mean(axis=1)
    return float((1+np.sum(np.abs(perm)>=observed-1e-12))/(draws+1))


def analyze(root: Path):
    out=root/"reports/tables";out.mkdir(parents=True,exist_ok=True)
    groups=defaultdict(list);resources=defaultdict(lambda:defaultdict(float));trace=[]
    for status_path in sorted((root/"artifacts/runs").glob("main-*/status.json")):
        status=json.loads(status_path.read_text());cfg=status["config"];key=(cfg["model"],cfg["condition"])
        for field in ("gpu_reserved_seconds","input_tokens","output_tokens","train_tokens"):
            resources[key][field]+=status.get(field,0)
        path=status_path.parent/"evaluation_summary.json"
        if status["status"]!="completed" or not path.exists():continue
        rows=json.loads(path.read_text());groups[key].extend(rows)
        trace.append({"run_id":status["run_id"],"path":str(path.relative_to(root)),"sha256":sha256(path),
                      "model_revision":status["model_revision"],"code_commit":status["code_commit"],"dataset_hash":status["dataset_hash"]})
    summary=[];per_seed=[];contrasts=[]
    for model,conditions in [("qwen",["C1","C2","C3","C4","C5","C6","A1","A2","A3"]),("phi",["C1","C3","C5"])]:
        for condition in conditions:
            rows=groups.get((model,condition),[])
            if rows:
                pairs=paired_success(rows);seeds=sorted({s for s,f in pairs})
                values=[]
                for seed in seeds:
                    rate=statistics.mean(v for (s,f),v in pairs.items() if s==seed);values.append(rate)
                    per_seed.append({"model":model,"condition":condition,"seed":seed,"families":sum(s==seed for s,f in pairs),"paired_success":rate})
                summary.append({"model":model,"condition":condition,"executed_seeds":len(seeds),"paired_success":statistics.mean(values),
                                "seed_sd":statistics.stdev(values) if len(values)>1 else None,"conversation_success":statistics.mean(r["success"] for r in rows),
                                "status":"complete" if len(seeds)==3 else "partial",**resources[model,condition]})
            else:summary.append({"model":model,"condition":condition,"executed_seeds":0,"paired_success":None,"seed_sd":None,
                                 "conversation_success":None,"status":"pending",**{k:resources[model,condition][k] for k in ("gpu_reserved_seconds","input_tokens","output_tokens","train_tokens")}})
        reference=groups.get((model,"C5"),[])
        pvalues={};pending=[]
        for other in conditions:
            if other=="C5" or not reference or not groups.get((model,other)):continue
            comparator=groups[model,other]
            if set(paired_success(reference))!=set(paired_success(comparator)):continue
            result=contrast(reference,comparator)
            result.update(model=model,contrast=f"C5-{other}",p_conditional_family=family_signflip_p(reference,comparator),
                          qualification="Bootstrap includes family and seed axes; randomization p is conditional on the realized seeds. Three training seeds limit seed-population inference.")
            pending.append(result)
            if other!="C3":pvalues[other]=result["p_conditional_family"]
        adjusted=holm(pvalues)
        for result in pending:
            other=result["contrast"].split("-")[1];result["holm_p_secondary"]=adjusted.get(other);contrasts.append(result)
    (out/"main_results.json").write_text(json.dumps(summary,indent=2)+"\n")
    (out/"main_contrasts.json").write_text(json.dumps(contrasts,indent=2)+"\n")
    (out/"main_evidence_trace.json").write_text(json.dumps(trace,indent=2)+"\n")
    write_csv(out/"main_results.csv",summary);write_csv(out/"per_seed_results.csv",per_seed)
    write_csv(out/"ablations.csv",[r for r in summary if r["condition"] in {"C5","A1","A2","A3"} and r["model"]=="qwen"])
    write_csv(out/"second_model.csv",[r for r in summary if r["model"]=="phi"])
    write_csv(out/"character_count_compute.csv",[r for r in summary if r["model"]=="qwen" and r["condition"] in {"C4","C5","C6"}])
    return summary,contrasts


if __name__=="__main__":analyze(Path.cwd())
