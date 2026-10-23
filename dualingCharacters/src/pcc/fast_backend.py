"""Optional vLLM inference process: one backbone with per-request LoRA switching.

Training runs in a separate, serialized process after this engine exits. There
are never five resident model copies or a competing inference/training service.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import time
from .backend import Backbone, parse_object
from .config import RunConfig
from .resources import RunLedger, append_json


class FastBackbone:
    prompt_ids=Backbone.prompt_ids

    def __init__(self, config: RunConfig, ledger: RunLedger, model_specs: Path):
        import torch
        from transformers import AutoTokenizer
        from vllm import LLM
        self.torch=torch;self.config=config;self.ledger=ledger;self.adapter=None;self.adapter_id=0
        self.spec=json.loads(model_specs.read_text())[config.model];spec=self.spec
        self.tokenizer=AutoTokenizer.from_pretrained(spec["name"],revision=spec["revision"],trust_remote_code=False)
        started=time.monotonic()
        self.llm=LLM(model=spec["name"],revision=spec["revision"],tokenizer_revision=spec["revision"],
                     dtype="bfloat16",trust_remote_code=False,tensor_parallel_size=1,
                     max_model_len=config.max_input_tokens+max(config.answer_tokens,config.character_tokens),
                     gpu_memory_utilization=.8,enable_lora=True,max_lora_rank=16,max_loras=1,
                     max_cpu_loras=4,enable_prefix_caching=True,seed=config.seed,
                     max_num_seqs=max(64,config.batch_size),disable_log_stats=True)
        ledger.metadata.update(model_revision=spec["revision"],model_name=spec["name"],model_load_seconds=time.monotonic()-started,
                               chat_template_sha256=hashlib.sha256(self.tokenizer.chat_template.encode()).hexdigest(),
                               vram_measurement="nvidia-smi total device use including vLLM KV reservation; not comparable to torch allocated peak")
        ledger.heartbeat()

    def load_adapter(self,path: Path,trainable: bool=False):
        if trainable:raise ValueError("Parameter updates require the separate Transformers training process")
        from vllm.lora.request import LoRARequest
        self.adapter_id+=1
        self.adapter=LoRARequest(f"defender-{self.adapter_id}",self.adapter_id,str(path.resolve()))

    def generate(self,conversations: list[list[dict]],max_new_tokens: int | None=None,
                 frozen: bool=False,sample: bool=False) -> list[dict]:
        if not conversations:return []
        from vllm import SamplingParams
        tokenized=[self.prompt_ids(c) for c in conversations]
        params=SamplingParams(max_tokens=max_new_tokens or self.config.answer_tokens,
                              temperature=.7 if sample else 0.,top_p=.9 if sample else 1.,
                              seed=self.config.seed+self.ledger.calls)
        started=time.monotonic()
        outputs=self.llm.generate([{"prompt_token_ids":ids} for ids in tokenized],params,
                                 lora_request=None if frozen else self.adapter,use_tqdm=False)
        elapsed=time.monotonic()-started;results=[]
        for ids,out in zip(tokenized,outputs):
            result=out.outputs[0]
            results.append({"raw":result.text,"parsed":parse_object(result.text),"input_tokens":len(ids),
                            "output_tokens":len(result.token_ids),"batch_seconds":elapsed,"generation_capped":result.finish_reason=="length"})
        self.ledger.tokens_in+=sum(r["input_tokens"] for r in results)
        self.ledger.tokens_out+=sum(r["output_tokens"] for r in results)
        self.ledger.calls+=len(results)
        used=subprocess.run(["nvidia-smi","--query-gpu=memory.used","--format=csv,noheader,nounits"],capture_output=True,text=True,check=True).stdout.strip()
        self.ledger.peak_vram_bytes=max(self.ledger.peak_vram_bytes,int(used)*1024**2)
        append_json(self.ledger.run_dir/"batches.jsonl",{"kind":"frozen_character" if frozen else "defender","n":len(results),"seconds":elapsed,
                    "input_tokens":sum(r["input_tokens"] for r in results),"output_tokens":sum(r["output_tokens"] for r in results),"peak_vram_bytes":self.ledger.peak_vram_bytes})
        self.ledger.heartbeat();return results
