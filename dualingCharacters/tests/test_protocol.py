import copy
import json
from pathlib import Path
import pytest
from pcc.validation import external_sources
from pcc.extensions import damage_snapshot
from pcc.environment import make_family
from pcc.memory import observation, WorkingMemory
from pcc.freeze import verify_freeze
from pcc.resources import sha256
from pcc.training import balanced_stream


def test_external_policy_sources_do_not_depend_on_labels():
    item={"answer":"SECRET","haystack_dates":["2026-01-01"],"haystack_sessions":[[{"role":"user","content":"Meeting Thursday","has_answer":True}]]}
    before=external_sources(item)
    item["answer"]="OTHER SECRET";item["haystack_sessions"][0][0]["has_answer"]=False
    assert before==external_sources(item)
    assert "SECRET" not in str(before)


def test_fixed_fault_depends_on_public_snapshot_only():
    s=make_family("pilot",0,32)[0]
    prompt,_=observation(s.spec,list(s.messages),WorkingMemory(["Harbor"]*6,[1]*6))
    row={"prompt":prompt,"target":{"state":["SECRET"]*6},"metrics":{"success":True}}
    before=copy.deepcopy(row)
    damaged=damage_snapshot(row)
    row["target"]={"other":"HIDDEN"};row["metrics"]["success"]=False
    assert damage_snapshot(row)==damaged
    assert before["prompt"]==row["prompt"]
    body=json.loads(damaged[-1]["content"])
    assert body["memory"]["state"][0] is None
    assert body["sources"]==json.loads(prompt[-1]["content"])["sources"]


def test_freeze_detects_missing_gate_and_changed_inputs(tmp_path):
    (tmp_path/"configs").mkdir();(tmp_path/"input").write_text("frozen")
    with pytest.raises(PermissionError):verify_freeze(tmp_path)
    obj={"pilot_gates_passed":True,"files":{"input":sha256(tmp_path/"input")}}
    (tmp_path/"configs/freeze.json").write_text(json.dumps(obj))
    assert verify_freeze(tmp_path)==obj
    (tmp_path/"input").write_text("changed")
    with pytest.raises(ValueError):verify_freeze(tmp_path)


def test_balanced_stream_preserves_mixture_and_reports_impossibility():
    stream=balanced_stream([{"metrics":{"success":True},"id":"clean"},{"metrics":{"success":False},"id":"repair"}],17)
    assert [next(stream)["id"] for _ in range(6)]==["clean","repair"]*3
    with pytest.raises(ValueError):next(balanced_stream([{"metrics":{"success":True}}],17))


def test_all_manifest_family_fingerprints_are_disjoint():
    root=Path(__file__).resolve().parents[1]/"data/manifests"
    seen={}
    for split in ("pilot","train","validation","test","natural"):
        for row in json.loads((root/f"{split}.json").read_text())["families"]:
            # Fingerprints only, never test answers or policy outcomes.
            assert row["graph_hash"] not in seen,(row["id"],seen.get(row["graph_hash"]))
            seen[row["graph_hash"]]=row["id"]
