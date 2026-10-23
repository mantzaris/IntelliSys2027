"""Observable pilot diagnostics; semantic intent and coalitions require audit."""
from collections import Counter, defaultdict
from pathlib import Path
import json
import statistics
import gzip
from .analysis import paired_success


def trace_path(path: Path) -> Path:
    return path if path.exists() else path.with_suffix(path.suffix+".gz")


def jsonlines(path: Path) -> list[dict]:
    path=trace_path(path)
    if not path.exists():return []
    opener=gzip.open if path.suffix==".gz" else open
    with opener(path,"rt") as stream:return [json.loads(line) for line in stream if line.strip()]


def audit_run(run: Path) -> dict:
    status=json.loads((run/"status.json").read_text())
    actions=jsonlines(run/"collection_characters.jsonl")
    rows=jsonlines(run/"collection.jsonl")
    per_role={}
    for role in sorted({a["role"] for a in actions}):
        group=[a for a in actions if a["role"]==role]
        per_role[role]={"n":len(group),"action_types":dict(Counter(a["kind"] for a in group)),
                        "applied":sum(a["applied"] for a in group),
                        "contradictory_value":sum(a["contrary_to_truth"] for a in group),
                        "contradictory_edit_with_source_access":sum(a.get("contradictory_edit_with_source_access",False) for a in group),
                        "memory_changes":sum(a["memory_changed"] for a in group)}
    summary={"run_id":run.name,"phase":status["config"]["phase"],"condition":status["config"]["condition"],
             "status":status["status"],"roles":per_role,"peer_messages":sum(a["kind"]=="peer" and a["applied"] for a in actions)}
    for name in ("before","collection","after"):
        p=run/f"{name}_summary.json"
        if p.exists():
            items=json.loads(p.read_text());pair=paired_success(items)
            turns=jsonlines(run/f"{name}.jsonl")
            summary[name]={"conversations":len(items),"families":len(pair),"paired_success":statistics.mean(pair.values()),
                           "conversation_success":statistics.mean(r["success"] for r in items),
                           "malformed_rate":statistics.mean(not bool(r["generation"]["parsed"]) for r in turns),
                           "turn_success":statistics.mean(r["metrics"]["success"] for r in turns)}
    counts=run/"supervision.counts.json"
    if counts.exists():summary["supervision"]=json.loads(counts.read_text())
    batches=jsonlines(run/"batches.jsonl")
    summary["resources"]={"gpu_reserved_seconds":status["gpu_reserved_seconds"],"peak_vram_gib":status["peak_vram_bytes"]/2**30,
                          "input_tokens":status["input_tokens"],"output_tokens":status["output_tokens"],
                          "generation_seconds":sum(b["seconds"] for b in batches),
                          "aggregate_output_tokens_per_second":sum(b["output_tokens"] for b in batches)/max(.001,sum(b["seconds"] for b in batches))}
    return summary


def write_audit(root: Path, output: Path):
    output.mkdir(parents=True,exist_ok=True)
    rows=[audit_run(p.parent) for p in sorted(root.glob("runs/*/status.json"))]
    (output/"pilot_audit.json").write_text(json.dumps(rows,indent=2)+"\n")
    return rows


if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--root",type=Path,default=Path.cwd());a=p.parse_args()
    print(json.dumps(write_audit(a.root/"artifacts",a.root/"reports/tables"),indent=2))
