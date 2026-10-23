"""Deterministic manifests and split ownership; no locked-test evaluation here."""
from pathlib import Path
import json
from .environment import digest, make_family

SPLITS = {"pilot":32, "train":300, "validation":80, "test":240, "natural":48}


def manifest(split: str, count: int | None = None, horizon: int = 32) -> dict:
    count = SPLITS[split] if count is None else count
    families = []
    for i in range(count):
        a,b = make_family(split,i,horizon)
        families.append({"id":a.family_id,"graph_hash":a.graph_hash,"domain":a.spec.domain,
                         "worlds":[a.world,b.world],"horizon":horizon,
                         "structural_holdout":a.spec.online_override,
                         "source_hashes":[digest([m.public() for m in x.messages]) for x in (a,b)]})
    result = {"schema_version":1,"split":split,"families":families,"turn_definition":"one user message followed by one generated assistant response"}
    result["sha256"] = digest(result)
    return result


def write_manifests(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    for split in SPLITS:
        data = manifest(split,horizon=64 if split in {"test","natural"} else 32)
        (root/f"{split}.json").write_text(json.dumps(data,indent=2)+"\n")
