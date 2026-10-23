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
    names={"evaluation.jsonl","collection.jsonl","collection_characters.jsonl","collection_interventions.jsonl","natural_structured.jsonl","natural_structured_prose.jsonl"}
    saved=0;count=0;prefixes_removed=0
    for status_path in sorted((root/"artifacts/runs").glob("*/status.json")):
        if json.loads(status_path.read_text())["status"]!="completed":continue
        manifest_path=status_path.parent/"trace_archives.json"
        manifest=json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
        for name in sorted(names):
            source=status_path.parent/name
            if not source.exists():continue
            expected_rows=None
            if name in {"evaluation.jsonl","collection.jsonl","natural_structured.jsonl","natural_structured_prose.jsonl"}:
                stem="natural_structured" if name.startswith("natural_structured") else source.stem
                summary=source.with_name(stem+"_summary.json")
                if summary.exists():
                    expected_rows=sum(row["horizon"] for row in json.loads(summary.read_text()))
            original_hash=sha256(source);original_size=source.stat().st_size
            archive=source.with_suffix(source.suffix+".gz");temporary=archive.with_suffix(archive.suffix+".tmp")
            if archive.exists():
                # A completed remote archive can arrive while an earlier live
                # mirror's plain prefix remains locally (rsync does not delete).
                # Validate the authoritative archive before removing that prefix;
                # never replace the complete archive with the stale local copy.
                recorded=manifest.get(name)
                if not recorded or sha256(archive)!=recorded["archive_sha256"]:
                    raise ValueError("Existing archive lacks a matching integrity record; preserve both files")
                verified=hashlib.sha256();size=0;is_prefix=True;verified_rows=0
                with gzip.open(archive,"rb") as data,source.open("rb") as old:
                    for chunk in iter(lambda:data.read(1024*1024),b""):
                        verified.update(chunk);size+=len(chunk);verified_rows+=chunk.count(b"\n")
                        previous=old.read(len(chunk))
                        if chunk[:len(previous)]!=previous:is_prefix=False
                    if old.read(1):is_prefix=False
                if verified.hexdigest()!=recorded["original_sha256"] or size!=recorded["original_bytes"]:
                    raise ValueError("Existing archive failed original-byte verification; preserve both files")
                if expected_rows is not None and verified_rows!=expected_rows:
                    raise ValueError("Completed archive row count differs from episode summaries; preserve both files")
                if not is_prefix:
                    raise ValueError("Plain trace conflicts with verified completed archive; preserve both files")
                source.unlink();saved+=original_size;prefixes_removed+=1
                continue
            with temporary.open("wb") as destination:
                with gzip.GzipFile(filename="",fileobj=destination,mode="wb",mtime=0,compresslevel=6) as compressed:
                    with source.open("rb") as data:shutil.copyfileobj(data,compressed)
            verified=hashlib.sha256();verified_rows=0
            with gzip.open(temporary,"rb") as data:
                for chunk in iter(lambda:data.read(1024*1024),b""):
                    verified.update(chunk);verified_rows+=chunk.count(b"\n")
            if verified.hexdigest()!=original_hash:raise ValueError("Lossless trace verification failed")
            if expected_rows is not None and verified_rows!=expected_rows:
                raise ValueError("Completed trace row count differs from episode summaries; preserve original")
            os.replace(temporary,archive)
            manifest[name]={"original_sha256":original_hash,"archive":archive.name,"archive_sha256":sha256(archive),
                            "original_bytes":original_size,"archive_bytes":archive.stat().st_size}
            manifest_path.write_text(json.dumps(manifest,indent=2)+"\n")
            source.unlink();saved+=original_size-archive.stat().st_size;count+=1
    return {"traces_compressed":count,"stale_or_duplicate_prefixes_removed":prefixes_removed,
            "bytes_saved_this_pass":saved,"verification":"Uncompressed SHA256 checked before original trace removal; existing completed archives never replaced by stale prefixes"}


if __name__=="__main__":
    root=Path.cwd();print(json.dumps({"checkpoint_links":deduplicate_completed(root),"trace_archives":compact_completed(root)}))
