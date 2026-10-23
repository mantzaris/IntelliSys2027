"""One resident base model, batched inference, optional defender adapter."""
from contextlib import nullcontext
from pathlib import Path
import json
import random
import time
from .config import RunConfig
from .resources import RunLedger, append_json, sha256


def parse_object(text: str) -> dict:
    decoder=json.JSONDecoder()
    for i,c in enumerate(text):
        if c=="{":
            try:
                value,_=decoder.raw_decode(text[i:])
                if isinstance(value,dict): return value
            except json.JSONDecodeError: pass
    return {}


class Backbone:
    def __init__(self, config: RunConfig, ledger: RunLedger, model_specs: Path):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, set_seed
        self.torch=torch; self.config=config; self.ledger=ledger
        set_seed(config.seed); torch.set_num_threads(8)
        torch.backends.cuda.matmul.allow_tf32=True
        specs=json.loads(model_specs.read_text()); spec=specs[config.model]
        self.spec=spec
        self.tokenizer=AutoTokenizer.from_pretrained(spec["name"],revision=spec["revision"],trust_remote_code=False,padding_side="left")
        if self.tokenizer.pad_token_id is None: self.tokenizer.pad_token=self.tokenizer.eos_token
        kwargs={"revision":spec["revision"],"trust_remote_code":False,"torch_dtype":torch.bfloat16,
                "device_map":{"":"cuda:0"},"attn_implementation":"sdpa"}
        if config.precision=="nf4":
            kwargs["quantization_config"]=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type="nf4",bnb_4bit_compute_dtype=torch.bfloat16,bnb_4bit_use_double_quant=True)
        start=time.monotonic()
        self.model=AutoModelForCausalLM.from_pretrained(spec["name"],**kwargs)
        self.model.eval(); self.has_adapter=False
        ledger.metadata.update(model_revision=spec["revision"],model_name=spec["name"],model_load_seconds=time.monotonic()-start,
                               chat_template_sha256=__import__('hashlib').sha256(self.tokenizer.chat_template.encode()).hexdigest())
        ledger.peak_vram_bytes=torch.cuda.max_memory_allocated()
        ledger.heartbeat()

    def prompt_ids(self, messages: list[dict], generation: bool=True) -> list[int]:
        ids=self.tokenizer.apply_chat_template(messages,tokenize=True,add_generation_prompt=generation)
        if len(ids)>self.config.max_input_tokens:
            raise ValueError(f"Input has {len(ids)} tokens; budget is {self.config.max_input_tokens}. No silent truncation.")
        return ids

    def generate(self, conversations: list[list[dict]], max_new_tokens: int | None=None,
                 frozen: bool=False, sample: bool=False) -> list[dict]:
        if not conversations:return []
        torch=self.torch; tokenized=[self.prompt_ids(c) for c in conversations]
        batch=self.tokenizer.pad({"input_ids":tokenized},padding=True,return_tensors="pt").to("cuda")
        kwargs={"max_new_tokens":max_new_tokens or self.config.answer_tokens,"do_sample":sample,
                "pad_token_id":self.tokenizer.pad_token_id,"use_cache":True}
        if sample:kwargs.update(temperature=.7,top_p=.9)
        context=self.model.disable_adapter() if frozen and self.has_adapter else nullcontext()
        self.model.eval(); torch.cuda.synchronize(); start=time.monotonic()
        with context,torch.inference_mode():
            generated=self.model.generate(**batch,**kwargs)
        torch.cuda.synchronize(); elapsed=time.monotonic()-start
        results=[]
        for i,output in enumerate(generated):
            suffix=output[batch.input_ids.shape[1]:].tolist()
            # Generation padding can share EOS; count through first EOS inclusive.
            eos=self.model.generation_config.eos_token_id
            eos_ids=set(eos if isinstance(eos,list) else [eos])
            stop=next((j+1 for j,t in enumerate(suffix) if t in eos_ids),len(suffix))
            suffix=suffix[:stop]
            raw=self.tokenizer.decode(suffix,skip_special_tokens=True)
            results.append({"raw":raw,"parsed":parse_object(raw),"input_tokens":len(tokenized[i]),
                            "output_tokens":len(suffix),"batch_seconds":elapsed,
                            "generation_capped":stop==kwargs["max_new_tokens"] and suffix[-1] not in eos_ids if suffix else False})
        self.ledger.tokens_in+=sum(r["input_tokens"] for r in results)
        self.ledger.tokens_out+=sum(r["output_tokens"] for r in results)
        self.ledger.calls+=len(results)
        self.ledger.peak_vram_bytes=max(self.ledger.peak_vram_bytes,torch.cuda.max_memory_allocated())
        append_json(self.ledger.run_dir/"batches.jsonl",{"kind":"frozen_character" if frozen else "defender","n":len(results),"seconds":elapsed,
                    "input_tokens":sum(r["input_tokens"] for r in results),"output_tokens":sum(r["output_tokens"] for r in results),"peak_vram_bytes":self.ledger.peak_vram_bytes})
        self.ledger.heartbeat()
        return results

    def add_adapter(self):
        if self.has_adapter:return
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
        if self.config.precision=="nf4": self.model=prepare_model_for_kbit_training(self.model,use_gradient_checkpointing=True)
        # all-linear covers Qwen and Phi consistently at the same rank; actual
        # parameter counts are reported, not claimed equal across architectures.
        config=LoraConfig(r=self.config.lora_rank,lora_alpha=self.config.lora_alpha,lora_dropout=0.,
                          target_modules="all-linear",bias="none",task_type="CAUSAL_LM")
        self.model=get_peft_model(self.model,config)
        self.model.enable_input_require_grads()
        self.has_adapter=True
        trainable,total=self.model.get_nb_trainable_parameters()
        self.ledger.metadata.update(trainable_parameters=trainable,total_parameters=total)

    def load_adapter(self,path: Path,trainable: bool=False):
        from peft import PeftModel
        self.model=PeftModel.from_pretrained(self.model,str(path),is_trainable=trainable)
        self.has_adapter=True
        if trainable:self.model.enable_input_require_grads()

    def save_adapter(self,path: Path):
        path.mkdir(parents=True,exist_ok=True)
        self.model.save_pretrained(path,safe_serialization=True)
        result={p.name:sha256(p) for p in path.iterdir() if p.is_file()}
        (path/"checksums.json").write_text(json.dumps(result,indent=2)+"\n")
        return result
