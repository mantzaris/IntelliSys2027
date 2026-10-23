"""Deduplicate identical immutable checkpoint files; preserve every named artifact."""
from pathlib import Path
import json
import os
from .resources import sha256


def deduplicate_completed(root: Path) -> dict:
    by_hash={};linked=0;saved=0
    for status_path in sorted((root/"artifacts/runs").glob("*/status.json")):
        if json.loads(status_path.read_text())["status"]!="completed":continue
        for path in sorted(status_path.parent.glob("training/*/*.safetensors")):
            digest=sha256(path);key=(path.stat().st_size,digest)
            if key not in by_hash:by_hash[key]=path;continue
            original=by_hash[key]
            if path.stat().st_ino==original.stat().st_ino:continue
            replacement=path.with_name(path.name+".dedup.tmp")
            os.link(original,replacement);os.replace(replacement,path)
            linked+=1;saved+=key[0]
    result={"identical_files_linked":linked,"bytes_saved_this_pass":saved,
            "policy":"Only completed-run safetensors; no artifact path or content removed; active checkpoints untouched."}
    if linked:
        with (root/"artifacts/storage_deduplication.jsonl").open("a") as f:f.write(json.dumps(result)+"\n")
    return result


if __name__=="__main__":print(json.dumps(deduplicate_completed(Path.cwd())))
