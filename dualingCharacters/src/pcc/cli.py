from dataclasses import replace
from pathlib import Path
import argparse
import json
import os
from .config import RunConfig
from .datasets import write_manifests
from .environment import make_family, digest


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("command",choices=["manifests","profile","pilot","collect","evaluate","analyze"])
    parser.add_argument("--root",type=Path,default=Path.cwd())
    parser.add_argument("--config",type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("--families",type=int,default=4)
    parser.add_argument("--start-family",type=int,default=0)
    parser.add_argument("--horizon",type=int,default=16)
    parser.add_argument("--split",default="pilot",choices=["pilot","train","validation","test"])
    parser.add_argument("--adapter",type=Path)
    args=parser.parse_args();root=args.root.resolve()
    if args.command=="manifests":write_manifests(root/"data/manifests");return
    if args.command=="analyze":
        from .analysis import summarize_artifacts
        print(json.dumps(summarize_artifacts(root/"artifacts",root/"reports/tables"),indent=2));return
    if not args.run_id:parser.error("--run-id is required")
    cfg=RunConfig.load(args.config) if args.config else RunConfig()
    if args.split=="test":
        freeze=root/"configs/freeze.json"
        if not freeze.exists() or cfg.phase!="confirmatory":raise PermissionError("Test plan is not frozen")
        plan=json.loads(freeze.read_text())
        if not plan.get("pilot_gates_passed"):raise PermissionError("Pilot gates have not passed")
        # Every locked manifest and analysis source must match the frozen plan.
        from .resources import sha256
        for name,expected in plan["files"].items():
            if sha256(root/name)!=expected:raise ValueError(f"Frozen file changed: {name}")
    from .backend import Backbone
    from .resources import RunLedger
    from .evaluation import run_episodes
    from .training import select_supervision, train
    scenarios=[s for i in range(args.start_family,args.start_family+args.families) for s in make_family(args.split,i,args.horizon)]
    with RunLedger(root/"artifacts",args.run_id,cfg) as ledger:
        ledger.metadata["dataset_hash"]=digest([{"id":s.family_id,"world":s.world,"graph":s.graph_hash} for s in scenarios])
        model=Backbone(cfg,ledger,root/"configs/models.json")
        if args.adapter:model.load_adapter(args.adapter)
        if args.command=="profile":
            # A tiny, explicitly unbalanced engineering profile, not hypothesis evidence.
            _,windows=run_episodes(model,scenarios[:cfg.batch_size],"C1",ledger.run_dir/"profile_before.jsonl",True)
            examples,counts=select_supervision(model,windows,ledger.run_dir/"supervision.jsonl",max_candidates=8)
            report=train(model,examples,ledger.run_dir/"training",steps=4,pilot_allow_unbalanced=True)
            ledger.metadata["profile_training"]=report
        elif args.command=="pilot":
            heldout=[s for i in range(24,24+args.families) for s in make_family("pilot",i,args.horizon)]
            run_episodes(model,heldout,"base",ledger.run_dir/"before.jsonl")
            _,windows=run_episodes(model,scenarios,cfg.condition,ledger.run_dir/"collection.jsonl",True)
            examples,counts=select_supervision(model,windows,ledger.run_dir/"supervision.jsonl",max_candidates=32)
            report=train(model,examples,ledger.run_dir/"training",pilot_allow_unbalanced=True)
            ledger.metadata["training"]=report
            run_episodes(model,heldout,"base",ledger.run_dir/"after.jsonl")
        elif args.command=="collect":
            _,windows=run_episodes(model,scenarios,cfg.condition,ledger.run_dir/"collection.jsonl",True)
            select_supervision(model,windows,ledger.run_dir/"supervision.jsonl")
        elif args.command=="evaluate":
            run_episodes(model,scenarios,"base",ledger.run_dir/"evaluation.jsonl")


if __name__=="__main__":main()
