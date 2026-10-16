"""Local offline vLLM inference only. No paid API implementation."""
from dataclasses import asdict
from datetime import datetime
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import time
from .schema import digest
from .storage import immutable_json, utcnow


class LocalModel:
    def __init__(self, alias, max_model_len=12288, max_output=1536, temperature=0.3, top_p=0.95, batch_size=32, guided=False,
                 enforce_eager=True,gpu_memory_utilization=0.85):
        os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
        os.environ["HF_HUB_DISABLE_XET"] = "1"
        os.environ["VLLM_NO_USAGE_STATS"] = "1"
        os.environ["DO_NOT_TRACK"] = "1"
        from vllm import LLM
        self.alias, self.batch_size = alias, batch_size
        metadata = json.loads((Path("records/models") / (alias + ".json")).read_text())
        path = Path("artifacts/models/" + alias + "_path.txt").read_text().strip()
        weight_config=json.loads((Path(path)/'config.json').read_text())
        tokenizer_path=path
        if alias=="mistral":
            tokenizer_path=Path("artifacts/models/mistral_tokenizer_path.txt").read_text().strip()
        self.settings = {"model": metadata["model"], "revision": metadata["revision"],
                         "tokenizer_revision": metadata["revision"], "precision": "bfloat16", "quantization": weight_config.get('quantization_config'),
                         "temperature": temperature, "top_p": top_p, "max_output_tokens": max_output,
                         "max_model_len": max_model_len, "reasoning_mode": "disabled" if alias == "qwen3" else "not_applicable",
                         "engine": "vllm", "engine_version": importlib.metadata.version("vllm"),
                         "batch_size": batch_size, "seed_scheme": "sha256(pair_id,repetition,stage); common across arms",
                         "guided_decoding": guided, "prefix_caching": False, "enforce_eager": enforce_eager,
                         "gpu_memory_utilization":gpu_memory_utilization}
        self.settings.update(prompt_tokenization='native_chat_template_ids',chat_template_date='2026-10-16')
        if guided:
            from .policies import OUTPUT_SCHEMA,MANAGER_OUTPUT_SCHEMA
            self.settings["output_schema_sha256"] = digest(OUTPUT_SCHEMA)
            self.settings["manager_output_schema_sha256"] = digest(MANAGER_OUTPUT_SCHEMA)
        start = time.monotonic()
        self.engine = LLM(model=path, tokenizer=tokenizer_path, dtype="bfloat16", max_model_len=max_model_len,
                          gpu_memory_utilization=gpu_memory_utilization, enforce_eager=enforce_eager, max_num_seqs=batch_size,
                          enable_prefix_caching=False, seed=1729, trust_remote_code=False)
        self.load_seconds = time.monotonic() - start
        self.tokenizer = self.engine.get_tokenizer()
        self.settings["chat_template_sha256"] = digest(self.tokenizer.chat_template)
        if self.settings['quantization'] is not None:
            self.settings['quantization_engine_dependency']=importlib.metadata.version('compressed-tensors')
        fingerprint = digest(self.settings)
        immutable_json(Path("records/environment") / (alias + "-" + fingerprint[:12] + ".json"),
                       {"settings": self.settings, "chat_template": self.tokenizer.chat_template,
                        "gpu": subprocess.check_output(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"], text=True).strip(),
                        "dependencies": {p: importlib.metadata.version(p) for p in
                                         ["vllm", "torch", "transformers", "huggingface-hub", "numpy"]}})

    def prepare(self, prompt):
        # One user message works with both model families' native chat templates.
        return self.tokenizer.apply_chat_template([{"role": "user", "content": prompt}],
                                                 tokenize=False, add_generation_prompt=True,
                                                 strftime_now=lambda fmt:datetime(2026,10,16).strftime(fmt),
                                                 **({"enable_thinking":False} if self.alias == "qwen3" else {}))

    def token_ids(self,prompt):
        # The native template already emits BOS/control tokens. Never add them twice.
        return self.tokenizer.encode(self.prepare(prompt),add_special_tokens=False)

    def run(self, requests):
        from vllm import SamplingParams
        from vllm.sampling_params import GuidedDecodingParams
        from .policies import OUTPUT_SCHEMA,MANAGER_OUTPUT_SCHEMA
        formatted = [self.prepare(r["prompt"]) for r in requests]
        token_ids = [self.tokenizer.encode(t,add_special_tokens=False) for t in formatted]
        counts = [len(ids) for ids in token_ids]
        caps=[r.get("max_output_tokens",self.settings["max_output_tokens"]) for r in requests]
        if any(n + cap > self.settings["max_model_len"] for n,cap in zip(counts,caps)):
            raise ValueError("Input plus output allowance exceeds context. No silent truncation permitted.")
        params = [SamplingParams(temperature=self.settings["temperature"], top_p=self.settings["top_p"],
                                  max_tokens=r.get("max_output_tokens",self.settings["max_output_tokens"]), seed=r["seed"],
                                  guided_decoding=GuidedDecodingParams(json=OUTPUT_SCHEMA if r['stage']=='root' else MANAGER_OUTPUT_SCHEMA) if self.settings["guided_decoding"] else None) for r in requests]
        start, utc = time.monotonic(), utcnow()
        outputs = self.engine.generate([{'prompt_token_ids':ids} for ids in token_ids], params, use_tqdm=False)
        wall = time.monotonic() - start
        results = []
        for out, count, cap, ids, text in zip(outputs, counts, caps, token_ids, formatted):
            if out.prompt_token_ids!=ids:raise RuntimeError('Engine changed native prompt token IDs')
            response = out.outputs[0]
            metrics = out.metrics
            latency = None
            if metrics is not None and metrics.finished_time is not None:
                latency = metrics.finished_time - metrics.arrival_time
            results.append({"text": response.text, "finish_reason": response.finish_reason,
                            "formatted_prompt_sha256":digest(text),"prompt_token_ids_sha256":digest(ids),
                            "output_token_cap": cap,
                            "input_tokens": len(out.prompt_token_ids), "output_tokens": len(response.token_ids),
                            "reasoning_tokens": None, "latency_seconds": latency,
                            "batch_wall_seconds": wall, "batch_size": len(requests),
                            "allocated_inference_seconds": wall / len(requests), "started_utc": utc})
        return results
