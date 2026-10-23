"""Deduplicate identical immutable checkpoint files; preserve every named artifact."""
from pathlib import Path
import json
import os
import gzip
import hashlib
import shutil
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


def compact_completed(root: Path) -> dict:
    """Losslessly compress bulky completed traces; verify bytes before unlinking.

    Supervision, optimizer states, adapter files and active traces stay unchanged.
    Readers transparently accept the archived .jsonl.gz form.
    """
    names={"evaluation.jsonl","collection.jsonl","collection_characters.jsonl","collection_interventions.jsonl","natural_structured.jsonl"}
    saved=0;count=0
    for status_path in sorted((root/"artifacts/runs").glob("*/status.json")):
        if json.loads(status_path.read_text())["status"]!="completed":continue
        manifest_path=status_path.parent/"trace_archives.json"
        manifest=json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
        for name in sorted(names):
            source=status_path.parent/name
            if not source.exists():continue
            original_hash=sha256(source);original_size=source.stat().st_size
            archive=source.with_suffix(source.suffix+".gz");temporary=archive.with_suffix(archive.suffix+".tmp")
            with temporary.open("wb") as destination:
                with gzip.GzipFile(filename="",fileobj=destination,mode="wb",mtime=0,compresslevel=6) as compressed:
                    with source.open("rb") as data:shutil.copyfileobj(data,compressed)
            verified=hashlib.sha256()
            with gzip.open(temporary,"rb") as data:
                for chunk in iter(lambda:data.read(1024*1024),b""):verified.update(chunk)
            if verified.hexdigest()!=original_hash:raise ValueError("Lossless trace verification failed")
            os.replace(temporary,archive)
            manifest[name]={"original_sha256":original_hash,"archive":archive.name,"archive_sha256":sha256(archive),
                            "original_bytes":original_size,"archive_bytes":archive.stat().st_size}
            manifest_path.write_text(json.dumps(manifest,indent=2)+"\n")
            source.unlink();saved+=original_size-archive.stat().st_size;count+=1
    return {"traces_compressed":count,"bytes_saved_this_pass":saved,"verification":"Uncompressed SHA256 checked before original trace removal"}


if __name__=="__main__":
    root=Path.cwd();print(json.dumps({"checkpoint_links":deduplicate_completed(root),"trace_archives":compact_completed(root)}))
