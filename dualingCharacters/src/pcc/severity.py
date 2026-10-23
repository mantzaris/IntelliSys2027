"""Pilot-only action replays against identical frozen reference observations."""
from pathlib import Path
import argparse
import json
from .characters import apply_action, cast
from .config import RunConfig
from .diagnostics import jsonlines
from .environment import make_family, score
from .memory import WorkingMemory
from .resources import RunLedger, append_json, sha256


def main():
    p=argparse.ArgumentParser();p.add_argument("--config",type=Path,required=True);p.add_argument("--run-id",required=True)
    p.add_argument("--source-run",default="mechanism-v3-001");a=p.parse_args();root=Path.cwd();cfg=RunConfig.load(a.config)
    if cfg.phase!="pilot":raise ValueError("This diagnostic is restricted to pilot data")
    run=root/"artifacts/runs"/a.source_run
    refs={(r["family_id"],r["world"],r["turn"]):r for r in jsonlines(run/"C1.jsonl")}
    with RunLedger(root/"artifacts",a.run_id,cfg) as ledger:
        from .fast_backend import FastBackbone
        model=FastBackbone(cfg,ledger,root/"configs/models.json")
        ledger.metadata["reference_sha256"]=sha256(run/"C1.jsonl")
        for condition in ("C3","C5"):
            actions=[x for x in jsonlines(run/f"{condition}_characters.jsonl") if x["kind"] in {"edit","recollect","propose"} and not x["communication_slot"]]
            for start in range(0,len(actions),cfg.batch_size):
                chunk=actions[start:start+cfg.batch_size];prompts=[];saved=[]
                for action in chunk:
                    reference=refs[action["family_id"],action["world"],action["turn"]]
                    prompt=reference["prompt"];body=json.loads(prompt[-1]["content"])
                    m=body["memory"];memory=WorkingMemory(m["state"],m["evidence"],m["notes"])
                    actors=cast(condition,action["family_id"],cfg.seed);actor=next(x for x in actors if x.alias==action["actor"])
                    applied=apply_action(action,actor,actors,memory,condition,cfg.history_actions)
                    body["memory"]=memory.public()
                    prompts.append([prompt[0],{"role":"user","content":json.dumps(body,separators=(",",":"))}])
                    saved.append((reference,action,applied))
                for prompt,generation,(reference,action,applied) in zip(prompts,model.generate(prompts),saved):
                    number=int(action["family_id"].split("-")[-1]);s=next(x for x in make_family("pilot",number,16) if x.world==action["world"])
                    after=score(generation["parsed"],s.truth_at(action["turn"]),s.spec)
                    append_json(ledger.run_dir/"severity.jsonl",{"condition":condition,"family_id":action["family_id"],"world":action["world"],"turn":action["turn"],
                                "before_success":reference["metrics"]["success"],"after_success":after["success"],
                                "success_to_failure":reference["metrics"]["success"] and not after["success"],"applied":applied["applied"],
                                "prompt":prompt,"generation":generation,"action":{k:v for k,v in action.items() if k not in {"generation","prompt"}}})


if __name__=="__main__":main()
