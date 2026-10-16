"""Pin authoritative repository revisions before downloading public weights."""
import argparse
import hashlib
import json
import os
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
os.environ["HF_HUB_DISABLE_XET"] = "1"
from pathlib import Path
from datetime import datetime, timezone
from huggingface_hub import HfApi, snapshot_download

MODELS = {"qwen": "Qwen/Qwen2.5-7B-Instruct", "qwen14": "Qwen/Qwen2.5-14B-Instruct", "qwen3": "Qwen/Qwen3-14B", "mistral": "mistralai/Mistral-7B-Instruct-v0.3", "nemo": "mistralai/Mistral-Nemo-Instruct-2407", "mistral24":"RedHatAI/Mistral-Small-24B-Instruct-2501-quantized.w8a8", "phi4":"microsoft/phi-4"}
parser = argparse.ArgumentParser()
parser.add_argument("model", choices=MODELS)
parser.add_argument('--metadata-only',action='store_true')
args = parser.parse_args()
record = Path("records/models") / (args.model + ".json")
record.parent.mkdir(parents=True, exist_ok=True)
api = HfApi(token=False)
if record.exists():
    metadata = json.loads(record.read_text())
else:
    info = api.model_info(MODELS[args.model], files_metadata=True)
    metadata = {"model": info.id, "revision": info.sha, "tokenizer_revision": info.sha,
                "checked_utc": datetime.now(timezone.utc).isoformat(), "license": info.card_data.get('license') if info.card_data else None,
                "model_card": "https://huggingface.co/" + info.id + "/blob/" + info.sha + "/README.md",
                "files": [{"name": f.rfilename, "size": f.size, "lfs_sha256": f.lfs.sha256 if f.lfs else None}
                          for f in info.siblings if f.rfilename.endswith((".safetensors", ".json", ".jinja", ".model", ".model.v3"))]}
    record.write_text(json.dumps(metadata, indent=2) + "\n")
patterns=["config.json","README.md","LICENSE"] if args.metadata_only else ["model-*.safetensors", "model.safetensors.index.json", "config.json",
            "generation_config.json", "tokenizer.json", "tokenizer_config.json", "special_tokens_map.json", "vocab.json", "merges.txt",
            "chat_template.jinja", "tokenizer.model.v3", "tekken.json", "params.json", "README.md", "LICENSE"]
path = snapshot_download(MODELS[args.model], revision=metadata["revision"],
                         cache_dir="artifacts/models", max_workers=4, token=False,
                         allow_patterns=patterns,
                         ignore_patterns=["consolidated.safetensors", "*.bin"])
if not args.metadata_only:
    Path("artifacts/models/" + args.model + "_path.txt").write_text(str(Path(path).resolve()))
print(json.dumps({"model": metadata["model"], "revision": metadata["revision"], "path": path}), flush=True)
