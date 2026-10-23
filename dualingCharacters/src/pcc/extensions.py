"""Predetermined horizon, retrieval, corruption and fixed-state recovery checks."""
from pathlib import Path
import argparse
import copy
import json
from .config import RunConfig
from .environment import make_family, score, FIELDS, digest
from .evaluation import run_episodes
from .freeze import verify_freeze
from .memory import WorkingMemory
from .resources import RunLedger, append_json, sha256
from .diagnostics import jsonlines, trace_path


def damage_snapshot(row: dict) -> list[dict]:
    """Erase site in an executed base-policy observation, without reading labels.

    This is an explicit missing-memory fault, not a claim to reproduce deception.
    Other baseline memory errors remain. Original retrieved sources are unchanged.
    The oracle target is not used to construct any part of the observation.
    """
    prompt=copy.deepcopy(row["prompt"])
    body=json.loads(prompt[-1]["content"])
    body["memory"]["state"][0]=None
    body["memory"]["evidence"][0]=None
    body["memory"]["notes"]=[]
    prompt[-1]["content"]=json.dumps(body,separators=(",",":"))
    return prompt


def recovery(model, source: Path, family_ids: set[str], out: Path, attempts: int=4):
    # Fixed turn 32 of the 64-turn untrained-base run. Both paired worlds retained.
    source=trace_path(source);snapshots=jsonlines(source)
    snapshots=[r for r in snapshots if r["family_id"] in family_ids and r["turn"]==32]
    if len(snapshots)!=2*len(family_ids):raise ValueError("Incomplete fixed-state source")
    model.ledger.metadata["snapshot_source_sha256"]=sha256(source)
    for offset in range(0,len(snapshots),model.config.batch_size):
        rows=snapshots[offset:offset+model.config.batch_size]
        prompts=[damage_snapshot(r) for r in rows]
        first=[None]*len(rows)
        detected=[None]*len(rows)
        for attempt in range(1,attempts+1):
            diagnosis_prompts=[[{"role":"system","content":"Identify which of the six working-memory fields require correction or completion using the supplied original user sources. An explicit user update can require correction of an earlier memory. Return only JSON with conflicts (field names) and evidence (supporting original user message indices). Do not guess from unsupported recollections."},p[-1]] for p in prompts]
            diagnosis_schema={"type":"object","properties":{"conflicts":{"type":"array","items":{"enum":list(FIELDS)}},"evidence":{"type":"array","items":{"type":"integer"}}},"required":["conflicts","evidence"],"additionalProperties":False}
            diagnoses=model.generate(diagnosis_prompts,64,response_schema=diagnosis_schema)
            results=model.generate(prompts)
            for i,(row,prompt,result,diagnosis) in enumerate(zip(rows,prompts,results,diagnoses)):
                number=int(row["family_id"].split("-")[-1])
                pair=make_family("test",number,64)
                scenario=next(s for s in pair if s.world==row["world"])
                body=json.loads(prompt[-1]["content"])
                truth=scenario.truth_at(32)
                metrics=score(result["parsed"],truth,scenario.spec,{s["index"] for s in body["sources"]})
                expected=[FIELDS[j] for j in range(6) if body["memory"]["state"][j]!=truth.values[j]]
                diagnosis_correct=set(diagnosis["parsed"].get("conflicts",[]))==set(expected)
                if expected and diagnosis_correct and detected[i] is None:detected[i]=attempt
                if metrics["success"] and first[i] is None:first[i]=attempt
                append_json(out,{"family_id":row["family_id"],"world":row["world"],"attempt":attempt,
                                 "generation":result,"metrics":metrics,"first_recovered":first[i],
                                 "diagnosis":diagnosis,"diagnosis_expected":expected,"diagnosis_correct":diagnosis_correct,"first_detected":detected[i],
                                 "prompt":prompt,"snapshot_source_sha256":model.ledger.metadata["snapshot_source_sha256"]})
                memory=WorkingMemory();memory.update(result["parsed"])
                body["memory"]=memory.public()
                # Sources remain the identical actually retrieved evidence set.
                # Only the evaluated policy's own memory changes across attempts.
                prompts[i]=[prompt[0],{"role":"user","content":json.dumps(body,separators=(",",":"))}]


def main():
    p=argparse.ArgumentParser();p.add_argument("task",choices=["horizon32","horizon128","short","larger-memory","unfamiliar","recovery"])
    p.add_argument("--config",type=Path,required=True);p.add_argument("--adapter",type=Path);p.add_argument("--run-id",required=True)
    p.add_argument("--snapshot-source",type=Path)
    a=p.parse_args();root=Path.cwd();freeze=verify_freeze(root);plan=freeze["plan"]
    cfg=RunConfig.load(a.config)
    if cfg.phase!="confirmatory":raise PermissionError("Extensions require the frozen phase")
    ids=plan["extension_family_numbers"];horizon={"horizon32":32,"horizon128":128,"short":16}.get(a.task,64)
    scenarios=[s for i in ids for s in make_family("test",i,horizon)]
    with RunLedger(root/"artifacts",a.run_id,cfg) as ledger:
        ledger.metadata.update(extension=a.task,family_numbers=ids,
                               dataset_hash=digest([{"id":s.family_id,"world":s.world,"sources":[m.public() for m in s.source_messages()]} for s in scenarios]))
        from .fast_backend import FastBackbone
        model=FastBackbone(cfg,ledger,root/"configs/models.json")
        if a.adapter:model.load_adapter(a.adapter)
        if a.task=="recovery":
            source=a.snapshot_source or root/f"artifacts/runs/base-{cfg.model}-eval/evaluation.jsonl"
            recovery(model,source,{f"test-{i:04d}" for i in ids},ledger.run_dir/"recovery.jsonl")
        else:
            run_episodes(model,scenarios,"base",ledger.run_dir/"evaluation.jsonl",unfamiliar_corruption=a.task=="unfamiliar")


if __name__=="__main__":main()
