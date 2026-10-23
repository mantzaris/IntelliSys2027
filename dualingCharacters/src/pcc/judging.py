"""Exploratory cross-family LongMemEval judging with the original rubric function.

The small judge is an adaptation, not official benchmark scoring. Programmatic
calibration covers structured planning only; human agreement remains pending.
"""
from pathlib import Path
import argparse
import ast
import hashlib
import json
import statistics
from .config import RunConfig
from .diagnostics import jsonlines
from .freeze import verify_freeze
from .resources import RunLedger, append_json, sha256


def official_prompt_function(path: Path):
    # The pinned, inspected MIT script also imports API clients. Extract only its
    # pure prompt-construction function, never execute those imports or its main.
    tree=ast.parse(path.read_text())
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="get_anscheck_prompt")
    namespace={};exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),"exec"),namespace)
    return namespace["get_anscheck_prompt"]


def calibration_rows(root: Path) -> list[dict]:
    rows=[]
    for condition in ("C1","C3","C5"):
        for r in jsonlines(root/f"artifacts/runs/mechanism-v3-001/{condition}.jsonl"):
            if r["turn"]!=16:continue
            rows.append({"id":f"{condition}:{r['family_id']}:{r['world']}","expected":r["metrics"]["success"],
                         "question":"Return the exact executable plan (all eight entries, in order) and unresolved clarification fields.",
                         "answer":json.dumps({k:r["target"][k] for k in ("plan","clarify")},sort_keys=True),
                         "response":json.dumps({k:r["generation"]["parsed"].get(k) for k in ("plan","clarify")},sort_keys=True)})
    selected=[]
    for label in (True,False):
        group=sorted((r for r in rows if r["expected"]==label),key=lambda r:hashlib.sha256(("judge-calibration-v1:"+r["id"]).encode()).hexdigest())
        selected.extend(group[:40])
    if len(selected)!=80:raise ValueError("Need forty positive and forty negative programmatic calibration cases")
    return selected


def main():
    p=argparse.ArgumentParser();p.add_argument("task",choices=["judge"]);p.add_argument("--config",type=Path,required=True);p.add_argument("--run-id",required=True)
    a=p.parse_args();root=Path.cwd();verify_freeze(root);cfg=RunConfig.load(a.config)
    prompt_path=root/"artifacts/public_assets/longmemeval_evaluate_qa.py"
    expected=json.loads((root/"data/manifests/external_assets.json").read_text())[prompt_path.name]
    if sha256(prompt_path)!=expected:raise ValueError("Official rubric source bytes changed")
    prompt_function=official_prompt_function(prompt_path)
    generator="qwen" if cfg.model=="phi" else "phi"
    with RunLedger(root/"artifacts",a.run_id,cfg) as ledger:
        from .fast_backend import FastBackbone
        model=FastBackbone(cfg,ledger,root/"configs/models.json")
        ledger.metadata.update(judge_rubric_sha256=sha256(prompt_path),generator_family=generator,
                               adaptation="Official rubric function, different small cross-family judge; no human calibration")
        calibrations=calibration_rows(root);labels=[]
        prompts=[[{"role":"user","content":prompt_function("multi-session",r["question"],r["answer"],r["response"])}] for r in calibrations]
        for start in range(0,len(prompts),cfg.batch_size):
            for result,row in zip(model.generate(prompts[start:start+cfg.batch_size],10),calibrations[start:start+cfg.batch_size]):
                label="yes" in result["raw"].lower();labels.append((row["expected"],label))
                append_json(ledger.run_dir/"calibration.jsonl",{**row,"judgment":result,"label":label})
        sensitivity=statistics.mean(b for a,b in labels if a);specificity=statistics.mean(not b for a,b in labels if not a)
        quality={"n":len(labels),"accuracy":statistics.mean(a==b for a,b in labels),"sensitivity":sensitivity,"specificity":specificity,
                 "balanced_accuracy":(sensitivity+specificity)/2,"human_agreement":None,
                 "descriptive_threshold_passed":(sensitivity+specificity)/2>=.85 and specificity>=.8,
                 "limitation":"Structured-planning calibration does not validate open-ended memory QA judgments; all external scores remain exploratory."}
        (ledger.run_dir/"calibration_summary.json").write_text(json.dumps(quality,indent=2)+"\n")
        for path in sorted((root/"artifacts/runs").glob(f"extra-{generator}-*/external.jsonl")):
            if json.loads((path.parent/"status.json").read_text())["status"]!="completed":continue
            rows=jsonlines(path)
            prompts=[[{"role":"user","content":prompt_function(r["question_type"],r["question"],r["answer"],r["generation"]["raw"],abstention="_abs" in r["question_id"])}] for r in rows]
            for start in range(0,len(prompts),cfg.batch_size):
                for result,row,prompt in zip(model.generate(prompts[start:start+cfg.batch_size],10),rows[start:start+cfg.batch_size],prompts[start:start+cfg.batch_size]):
                    append_json(ledger.run_dir/"external_judgments.jsonl",{"source_run":path.parent.name,"source_sha256":sha256(path),
                                "question_id":row["question_id"],"question_type":row["question_type"],"judgment":result,
                                "label":"yes" in result["raw"].lower(),"prompt":prompt,"calibration_threshold_passed":quality["descriptive_threshold_passed"]})


if __name__=="__main__":main()
