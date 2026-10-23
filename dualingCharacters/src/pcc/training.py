"""Verified supervision, exact nonpadding token quotas, and real LoRA updates."""
from pathlib import Path
import json
import math
import random
import time
from .backend import Backbone
from .resources import append_json


def select_supervision(backbone: Backbone, windows: list[dict], path: Path,
                       max_candidates: int=128) -> tuple[list[dict],dict]:
    """Bounded recovery attempts; same deterministic teacher fallback in every arm.

    Selection uses the training oracle only. Input messages were already executed.
    Gold completions never become inputs during collection or test evaluation.
    Only examples with all gold references actually retrieved are eligible.
    """
    rng=random.Random(backbone.config.seed)
    clean=[w for w in windows if w["metrics"]["success"] and w["evidence_visible"]]
    failed=[w for w in windows if not w["metrics"]["success"] and w["evidence_visible"]]
    rng.shuffle(clean);rng.shuffle(failed)
    counts={"attempted_windows":len(windows),"source_ineligible":sum(not w["evidence_visible"] for w in windows),
            "clean_valid":len(clean),"failed_eligible":len(failed),"candidate_attempts":0,"candidate_valid":0,
            "candidate_discarded":0,"gold_teacher_examples":0,"reused":0}
    # A common attempt cap; no condition can request extra sampling to hit a quota.
    repair=failed[:max_candidates]
    targets=[]
    for offset in range(0,len(repair),backbone.config.batch_size):
        chunk=repair[offset:offset+backbone.config.batch_size]
        generated=backbone.generate([w["messages"] for w in chunk],sample=True)
        for w,result in zip(chunk,generated):
            counts["candidate_attempts"]+=1
            parsed=result["parsed"]
            valid=all(parsed.get(k)==w["target"][k] for k in ("plan","state","evidence","clarify"))
            counts["candidate_valid"]+=int(valid);counts["candidate_discarded"]+=int(not valid)
            label=parsed if valid else w["target"]
            counts["gold_teacher_examples"]+=int(not valid)
            item={**w,"completion":label,"label_source":"verified_model_recovery" if valid else "common_oracle_teacher",
                  "recovery_attempt":result}
            targets.append(item)
    # All recoverable failures get one common teacher target; fixed attempt cap.
    for w in failed[max_candidates:]:
        targets.append({**w,"completion":w["target"],"label_source":"common_oracle_teacher"})
        counts["gold_teacher_examples"]+=1
    for w in clean:
        # Gold evidence/recall targets are also shared teacher supervision. A
        # behaviorally correct plan need not have a correct memory/evidence trace.
        targets.append({**w,"completion":w["target"],"label_source":"common_oracle_teacher_clean"})
        counts["gold_teacher_examples"]+=1
    for row in targets:append_json(path,row)
    path.with_suffix(".counts.json").write_text(json.dumps(counts,indent=2)+"\n")
    return targets,counts


def balanced_stream(examples: list[dict], seed: int):
    """Fixed 50:50 clean/recovery windows; inability is explicit, never hidden."""
    clean=[x for x in examples if x["metrics"]["success"]]
    recovery=[x for x in examples if not x["metrics"]["success"]]
    if not clean or not recovery:
        raise ValueError(f"Cannot meet 50:50 mixture: {len(clean)} clean, {len(recovery)} recovery. Repair pilot before confirmation.")
    rng=random.Random(seed);rng.shuffle(clean);rng.shuffle(recovery)
    i=0
    while True:
        yield clean[i%len(clean)]
        yield recovery[i%len(recovery)]
        i+=1


def train(backbone: Backbone, examples: list[dict], output: Path, steps: int | None=None,
          pilot_allow_unbalanced: bool=False, resume_checkpoint: Path | None=None) -> dict:
    torch=backbone.torch;cfg=backbone.config;steps=steps or cfg.train_steps
    backbone.add_adapter();model=backbone.model
    output.mkdir(parents=True,exist_ok=True)
    before=backbone.save_adapter(output/"initial")
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant":False})
    model.config.use_cache=False;model.train()
    optimizer=torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],lr=cfg.learning_rate,weight_decay=0.)
    if not examples:raise ValueError("No eligible supervised examples")
    if pilot_allow_unbalanced:
        def cycling():
            rng=random.Random(cfg.seed);items=list(examples);rng.shuffle(items)
            while True:yield from items
        stream=cycling()
    else:stream=balanced_stream(examples,cfg.seed)
    ids_buffer=[];labels_buffer=[];segments_buffer=[];positions_buffer=[];segment_number=0
    seen={};supervised_tokens=0;start_step=0
    if resume_checkpoint:
        saved=torch.load(resume_checkpoint,map_location="cpu",weights_only=False)
        from peft import set_peft_model_state_dict
        set_peft_model_state_dict(model,saved["adapter_state"])
        optimizer.load_state_dict(saved["optimizer"]);start_step=saved["step"]
        # Token stream offset is replayed deterministically below to preserve quota.
    losses=[];started=time.monotonic()
    for step in range(steps):
        while len(ids_buffer)<cfg.train_tokens_per_step:
            item=next(stream);key=(item["family_id"],item["world"],item["turn"])
            seen[key]=seen.get(key,0)+1
            prefix=backbone.prompt_ids(item["messages"])
            completion=json.dumps(item["completion"],separators=(",",":"))
            suffix=backbone.tokenizer.encode(completion,add_special_tokens=False)+[backbone.tokenizer.eos_token_id]
            ids_buffer.extend(prefix+suffix);labels_buffer.extend([-100]*len(prefix)+suffix)
            segments_buffer.extend([segment_number]*(len(prefix)+len(suffix)))
            positions_buffer.extend(range(len(prefix)+len(suffix)));segment_number+=1
        ids=ids_buffer[:cfg.train_tokens_per_step];labels=labels_buffer[:cfg.train_tokens_per_step]
        segments=segments_buffer[:cfg.train_tokens_per_step];positions=positions_buffer[:cfg.train_tokens_per_step]
        ids_buffer=ids_buffer[cfg.train_tokens_per_step:];labels_buffer=labels_buffer[cfg.train_tokens_per_step:]
        segments_buffer=segments_buffer[cfg.train_tokens_per_step:];positions_buffer=positions_buffer[cfg.train_tokens_per_step:]
        if positions[0]!=0:
            # A window split across optimizer chunks has lost its earlier prompt;
            # do not supervise the orphaned suffix. Count its input cost honestly.
            labels=[-100 if segment==segments[0] else label for segment,label in zip(segments,labels)]
        if step<start_step:continue
        if all(x==-100 for x in labels):raise ValueError("Packed chunk has no supervised tokens")
        tensor=torch.tensor([ids],device="cuda");target=torch.tensor([labels],device="cuda")
        lr=cfg.learning_rate*min(1.,(step+1)/max(1,steps*.1))*(.1+.9*.5*(1+math.cos(math.pi*step/steps)))
        for group in optimizer.param_groups:group["lr"]=lr
        optimizer.zero_grad(set_to_none=True)
        segment_tensor=torch.tensor(segments,device="cuda")
        indices=torch.arange(len(ids),device="cuda")
        allowed=(segment_tensor[:,None]==segment_tensor[None,:]) & (indices[:,None]>=indices[None,:])
        attention_mask=torch.zeros((1,1,len(ids),len(ids)),dtype=torch.bfloat16,device="cuda").masked_fill_(~allowed,torch.finfo(torch.bfloat16).min)
        result=model(input_ids=tensor,labels=target,attention_mask=attention_mask,
                     position_ids=torch.tensor([positions],device="cuda"),use_cache=False)
        if not torch.isfinite(result.loss):raise FloatingPointError("Nonfinite training loss")
        result.loss.backward();grad=torch.nn.utils.clip_grad_norm_(model.parameters(),cfg.max_grad_norm)
        optimizer.step();torch.cuda.synchronize()
        n_labels=sum(x!=-100 for x in labels);supervised_tokens+=n_labels
        row={"step":step+1,"loss":float(result.loss.detach()),"learning_rate":lr,"gradient_norm":float(grad),
             "input_tokens":len(ids),"supervised_tokens":n_labels,"elapsed_seconds":time.monotonic()-started}
        losses.append(row);append_json(output/"loss.jsonl",row)
        backbone.ledger.train_tokens+=len(ids)
        backbone.ledger.peak_vram_bytes=max(backbone.ledger.peak_vram_bytes,torch.cuda.max_memory_allocated())
        backbone.ledger.heartbeat()
        if (step+1)%16==0 or step+1==steps:
            from peft import get_peft_model_state_dict
            state={"adapter_state":get_peft_model_state_dict(model),"optimizer":optimizer.state_dict(),"step":step+1}
            torch.save(state,output/"optimizer.tmp");(output/"optimizer.tmp").replace(output/"optimizer.pt")
            backbone.save_adapter(output/"latest")
            print(json.dumps({"training_step":step+1,"steps":steps,"loss":row["loss"]}),flush=True)
    model.config.use_cache=True;model.gradient_checkpointing_disable();model.eval()
    after=backbone.save_adapter(output/"final")
    report={"optimizer_steps":steps-start_step,"input_tokens":(steps-start_step)*cfg.train_tokens_per_step,
            "supervised_tokens":supervised_tokens,"unique_windows":len(seen),"reused_windows":sum(v-1 for v in seen.values()),
            "seconds":time.monotonic()-started,"initial_checksums":before,"final_checksums":after,
            "adapter_changed":before.get("adapter_model.safetensors")!=after.get("adapter_model.safetensors"),
            "pilot_unbalanced_mixture":pilot_allow_unbalanced,
            "packing":"Block-diagonal causal attention isolates windows; prompt loss masked; orphaned suffix loss masked; exact nonpadding input quota"}
    (output/"training_summary.json").write_text(json.dumps(report,indent=2)+"\n")
    if not report["adapter_changed"]:raise RuntimeError("Adapter checksum did not change")
    return report
