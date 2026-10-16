"""Local offline vLLM inference only. No paid API implementation."""
from dataclasses import asdict
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import time
from .schema import digest
from .storage import immutable_json, utcnow


class LocalModel:
    def __init__(self, alias, max_model_len=12288, max_output=1536, temperature=0.3, top_p=0.95, batch_size=32):
        os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
        os.environ["HF_HUB_DISABLE_XET"] = "1"
        os.environ["VLLM_NO_USAGE_STATS"] = "1"
        os.environ["DO_NOT_TRACK"] = "1"
        from vllm import LLM
        self.alias, self.batch_size = alias, batch_size
        metadata = json.loads((Path("records/models") / (alias + ".json")).read_text())
        path = Path("artifacts/models/" + alias + "_path.txt").read_text().strip()
        self.settings = {"model": metadata["model"], "revision": metadata["revision"],
                         "tokenizer_revision": metadata["revision"], "precision": "bfloat16", "quantization": None,
                         "temperature": temperature, "top_p": top_p, "max_output_tokens": max_output,
                         "max_model_len": max_model_len, "reasoning_mode": "not_applicable",
                         "engine": "vllm", "engine_version": importlib.metadata.version("vllm"),
                         "batch_size": batch_size, "seed_scheme": "sha256(pair_id,repetition,stage); common across arms",
                         "guided_decoding": False, "prefix_caching": False, "enforce_eager": True}
        start = time.monotonic()
        self.engine = LLM(model=path, tokenizer=path, dtype="bfloat16", max_model_len=max_model_len,
                          gpu_memory_utilization=0.85, enforce_eager=True, max_num_seqs=batch_size,
                          enable_prefix_caching=False, seed=1729, trust_remote_code=False)
        self.load_seconds = time.monotonic() - start
        self.tokenizer = self.engine.get_tokenizer()
        self.settings["chat_template_sha256"] = digest(self.tokenizer.chat_template)
        fingerprint = digest(self.settings)
        immutable_json(Path("records/environment") / (alias + "-" + fingerprint[:12] + ".json"),
                       {"settings": self.settings, "chat_template": self.tokenizer.chat_template,
                        "gpu": subprocess.check_output(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"], text=True).strip(),
                        "dependencies": {p: importlib.metadata.version(p) for p in
                                         ["vllm", "torch", "transformers", "huggingface-hub", "numpy"]}})

    def prepare(self, prompt):
        # One user message works with both model families' native chat templates.
        return self.tokenizer.apply_chat_template([{"role": "user", "content": prompt}],
                                                 tokenize=False, add_generation_prompt=True)

    def run(self, requests):
        from vllm import SamplingParams
        formatted = [self.prepare(r["prompt"]) for r in requests]
        counts = [len(self.tokenizer.encode(t, add_special_tokens=False)) for t in formatted]
        if any(n + self.settings["max_output_tokens"] > self.settings["max_model_len"] for n in counts):
            raise ValueError("Input plus output allowance exceeds context. No silent truncation permitted.")
        params = [SamplingParams(temperature=self.settings["temperature"], top_p=self.settings["top_p"],
                                  max_tokens=self.settings["max_output_tokens"], seed=r["seed"]) for r in requests]
        start, utc = time.monotonic(), utcnow()
        outputs = self.engine.generate(formatted, params, use_tqdm=False)
        wall = time.monotonic() - start
        results = []
        for out, count in zip(outputs, counts):
            response = out.outputs[0]
            metrics = out.metrics
            latency = None
            if metrics is not None and metrics.finished_time is not None:
                latency = metrics.finished_time - metrics.arrival_time
            results.append({"text": response.text, "finish_reason": response.finish_reason,
                            "input_tokens": len(out.prompt_token_ids), "output_tokens": len(response.token_ids),
                            "reasoning_tokens": None, "latency_seconds": latency,
                            "batch_wall_seconds": wall, "batch_size": len(requests),
                            "allocated_inference_seconds": wall / len(requests), "started_utc": utc})
        return results
