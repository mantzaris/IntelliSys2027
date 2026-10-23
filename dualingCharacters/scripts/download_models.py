"""Download exact public revisions; record hashes of implementation-relevant files."""
import hashlib
import json
from pathlib import Path
from huggingface_hub import snapshot_download

root = Path(__file__).resolve().parents[1]
models = json.loads((root / "configs/models.json").read_text())
out = root / "artifacts/environment"
out.mkdir(parents=True, exist_ok=True)
for key, spec in models.items():
    path = Path(snapshot_download(spec["name"], revision=spec["revision"],
                                 ignore_patterns=["*.py", "*.msgpack", "*.h5"]))
    record = dict(spec, snapshot_path=str(path), files={})
    for name in ["README.md", "LICENSE", "config.json", "generation_config.json", "tokenizer_config.json"]:
        p = path / name
        if p.exists():
            record["files"][name] = hashlib.sha256(p.read_bytes()).hexdigest()
            (out / f"{key}_{name}").write_bytes(p.read_bytes())
    (out / f"{key}.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"model": key, "revision": spec["revision"], "downloaded": True}), flush=True)
