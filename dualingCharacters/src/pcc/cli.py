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
    parser.add_argument("command",choices=["manifests","profile","batch-profile","mechanism-pilot","pilot","collect","fit","evaluate","analyze"])
    parser.add_argument("--root",type=Path,default=Path.cwd())
    parser.add_argument("--config",type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("--families",type=int,default=4)
    parser.add_argument("--start-family",type=int,default=0)
    parser.add_argument("--horizon",type=int,default=16)
    parser.add_argument("--split",default="pilot",choices=["pilot","train","validation","test"])
    parser.add_argument("--adapter",type=Path)
    parser.add_argument("--supervision",type=Path)
    parser.add_argument("--resume-checkpoint",type=Path)
    parser.add_argument("--window-turns",help="Comma-separated predetermined training-window turns")
    args=parser.parse_args();root=args.root.resolve()
    if args.command=="manifests":write_manifests(root/"data/manifests");return
    if args.command=="analyze":
        from .analysis import summarize_artifacts
        print(json.dumps(summarize_artifacts(root/"artifacts",root/"reports/tables"),indent=2));return
    if not args.run_id:parser.error("--run-id is required")
    cfg=RunConfig.load(args.config) if args.config else RunConfig()
    if args.split=="test":
        if cfg.phase!="confirmatory":raise PermissionError("Test plan is not frozen")
        from .freeze import verify_freeze
        verify_freeze(root)
    from .backend import Backbone
    from .resources import RunLedger
    from .evaluation import run_episodes
    from .training import select_supervision, train
    scenarios=[s for i in range(args.start_family,args.start_family+args.families) for s in make_family(args.split,i,args.horizon)]
    with RunLedger(root/"artifacts",args.run_id,cfg) as ledger:
        ledger.metadata.update(task=args.command,split=args.split,horizon=args.horizon,start_family=args.start_family,
                               families=args.families,selected_window_turns=args.window_turns)
        ledger.metadata["dataset_hash"]=digest([{"id":s.family_id,"world":s.world,"graph":s.graph_hash} for s in scenarios])
        if cfg.engine=="vllm":
            if args.command in {"profile","pilot","fit"}:raise ValueError("Train with transformers in a separate serialized process")
            from .fast_backend import FastBackbone
            model=FastBackbone(cfg,ledger,root/"configs/models.json")
        else:model=Backbone(cfg,ledger,root/"configs/models.json")
        if args.adapter:model.load_adapter(args.adapter,trainable=args.command=="fit")
        if args.command=="batch-profile":
            from .memory import observation, WorkingMemory
            from .resources import append_json
            # Throughput only: repeated public prompts are not independent data.
            pool=[observation(s.spec,list(s.messages[:8]),WorkingMemory(),cfg.retrieval_messages,cfg.recent_messages)[0] for s in scenarios]
            for size in (4,8,16,32,64):
                try:
                    results=model.generate([pool[i%len(pool)] for i in range(size)])
                    append_json(ledger.run_dir/"throughput.jsonl",{"batch_size":size,"seconds":results[0]["batch_seconds"],
                                "output_tokens":sum(r["output_tokens"] for r in results),"peak_vram_bytes":ledger.peak_vram_bytes})
                    print(json.dumps({"batch_size":size,"seconds":results[0]["batch_seconds"]}),flush=True)
                except model.torch.cuda.OutOfMemoryError:
                    model.torch.cuda.empty_cache()
                    append_json(ledger.run_dir/"throughput.jsonl",{"batch_size":size,"status":"oom"})
                    break
        elif args.command=="mechanism-pilot":
            if cfg.phase!="pilot" or args.split!="pilot":raise ValueError("Mechanism development uses pilot families only")
            for condition in ("C1","C3","C4","C5","C6","A1","A2","A3"):
                run_episodes(model,scenarios,condition,ledger.run_dir/f"{condition}.jsonl")
        elif args.command=="profile":
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
            if args.window_turns:
                selected={int(x) for x in args.window_turns.split(",")}
                windows=[w for w in windows if w["turn"] in selected]
            select_supervision(model,windows,ledger.run_dir/"supervision.jsonl")
        elif args.command=="fit":
            if not args.supervision:raise ValueError("--supervision required")
            examples=[json.loads(line) for line in args.supervision.read_text().splitlines()]
            allowed="pilot-" if cfg.phase=="pilot" else "train-"
            if any(not str(e["family_id"]).startswith(allowed) for e in examples):
                raise ValueError(f"This phase requires {allowed} family supervision")
            ledger.metadata["supervision_sha256"]=__import__('hashlib').sha256(args.supervision.read_bytes()).hexdigest()
            train(model,examples,ledger.run_dir/"training",resume_checkpoint=args.resume_checkpoint)
        elif args.command=="evaluate":
            run_episodes(model,scenarios,"base",ledger.run_dir/"evaluation.jsonl")


if __name__=="__main__":main()
