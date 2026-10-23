"""External and prose validation without feeding rubric answers to the policy."""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import random
from .config import RunConfig
from .environment import Message, make_family
from .memory import retrieve, WorkingMemory
from .resources import RunLedger, append_json, sha256
from .backend import Backbone


def external(model, root: Path, out: Path):
    manifest=json.loads((root/"data/manifests/external.json").read_text())
    rows=json.loads((root/"artifacts/public_assets/longmemeval_s_cleaned.json").read_text())
    by_id={r["question_id"]:r for r in rows};prompts=[];items=[]
    for qid in manifest["question_ids"]:
        item=by_id[qid];sources=[];index=0
        for session,date in zip(item["haystack_sessions"],item["haystack_dates"]):
            for m in session:
                index+=1
                # Strip answer-bearing metadata such as has_answer and labels.
                sources.append(Message(index,str(m["role"]),f"Session date {date}: "+str(m["content"])))
        retrieved=retrieve(sources,item["question"],20)
        public=[{"index":m.index,"author":m.author,"text":" ".join(m.text.split()[:100])} for m in retrieved]
        system="Answer the user's question from the retrieved dated conversation messages. Distinguish later updates from earlier facts. If the history does not supply the answer, state what information is missing. Give a concise prose answer, not JSON."
        while True:
            prompt=[{"role":"system","content":system},{"role":"user","content":json.dumps({"question":item["question"],"question_date":item.get("question_date"),"retrieved_history":public},separators=(",",":"))}]
            try:model.prompt_ids(prompt);break
            except ValueError:
                if not public:raise
                public.pop(0)
        prompts.append(prompt);items.append((item,public))
    for offset in range(0,len(prompts),model.config.batch_size):
        chunk=prompts[offset:offset+model.config.batch_size]
        for result,(item,sources),prompt in zip(model.generate(chunk,192),items[offset:offset+model.config.batch_size],chunk):
            append_json(out,{"question_id":item["question_id"],"question_type":item["question_type"],"question":item["question"],
                             "answer":item["answer"],"generation":result,"prompt":prompt,"retrieved_indices":[s["index"] for s in sources],
                             "scoring_status":"official scoring / independent judge calibration pending"})


def natural(model,root: Path,out: Path):
    from .evaluation import run_episodes
    # 20 paired families = 40 genuinely unseen conversations, domain-balanced.
    scenarios=[s for i in range(20) for s in make_family("natural",i,64)]
    run_episodes(model,scenarios,"base",out.with_name("natural_structured.jsonl"))
    rows=[json.loads(x) for x in out.with_name("natural_structured.jsonl").read_text().splitlines()]
    final=[r for r in rows if r["turn"]==64]
    prompts=[]
    for row in final:
        body=json.loads(row["prompt"][-1]["content"])
        body["memory"]={"state":row["generation"]["parsed"].get("state",[]),"evidence":row["generation"]["parsed"].get("evidence",[])}
        prompts.append([{"role":"system","content":"Write a concise natural-language final project plan using the supplied conversation evidence and fallible memory. Honor actual user decisions, accept approved changes, and do not treat hypotheticals as approval. Include the six commitments, transport, equipment, source references where helpful, and any targeted clarification needed. Do not output JSON."},
                        {"role":"user","content":json.dumps(body,separators=(",",":"))}])
    for start in range(0,len(prompts),model.config.batch_size):
        for result,row,prompt in zip(model.generate(prompts[start:start+model.config.batch_size],320),final[start:start+model.config.batch_size],prompts[start:start+model.config.batch_size]):
            append_json(out,{"family_id":row["family_id"],"world":row["world"],"domain":row["domain"],"generation":result,
                             "prompt":prompt,"rubric_target":row["target"],"human_score":None})


def human_packet(root: Path):
    rows=[]
    for path in sorted((root/"artifacts/runs").glob("extra-qwen-*-17-natural/natural.jsonl")):
        for row in map(json.loads,path.read_text().splitlines()):rows.append((path.parent.name,row))
    rng=random.Random(40719);rng.shuffle(rows)
    out=root/"artifacts/human_review";out.mkdir(parents=True,exist_ok=True)
    key={};packet=[]
    for i,(run,row) in enumerate(rows):
        blind=f"P{i+1:04d}";key[blind]={"run_id":run,"family_id":row["family_id"],"world":row["world"]}
        packet.append({"id":blind,"source_material":row["prompt"][-1]["content"],"response":row["generation"]["raw"],"rubric_target":row["rubric_target"]})
    (out/"packet.json").write_text(json.dumps(packet,indent=2)+"\n")
    (out/"condition_key_private.json").write_text(json.dumps(key,indent=2)+"\n")
    for rater in (1,2):
        path=out/f"rater_{rater}.csv"
        if not path.exists():path.write_text("id,site,mode,cap,day,audience,partner,transport,equipment,update_authority,clarification,comments\n"+"\n".join(p["id"]+","*11 for p in packet)+"\n")
    return len(packet)


def main():
    p=argparse.ArgumentParser();p.add_argument("task",choices=["external","natural","packet"]);p.add_argument("--config",type=Path);p.add_argument("--adapter",type=Path);p.add_argument("--run-id")
    a=p.parse_args();root=Path.cwd()
    if a.task=="packet":print(json.dumps({"outputs":human_packet(root),"human_annotations":"pending"}));return
    if not (root/"configs/freeze.json").exists():raise PermissionError("Validation subset/plan must be frozen first")
    cfg=RunConfig.load(a.config)
    with RunLedger(root/"artifacts",a.run_id,cfg) as ledger:
        if cfg.engine=="vllm":
            from .fast_backend import FastBackbone
            model=FastBackbone(cfg,ledger,root/"configs/models.json")
        else:model=Backbone(cfg,ledger,root/"configs/models.json")
        if a.adapter:model.load_adapter(a.adapter)
        {"external":external,"natural":natural}[a.task](model,root,ledger.run_dir/(a.task+".jsonl"))


if __name__=="__main__":main()
