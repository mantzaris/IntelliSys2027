import copy
import json
from pathlib import Path
import pytest
from pcc.environment import Message, Event, Truth, make_family, score
from pcc.memory import WorkingMemory, observation
from pcc.characters import cast, apply_action, action_prompt
from pcc.datasets import manifest
from pcc.analysis import paired_success, contrast, holm
from pcc.config import RunConfig
from pcc.resources import used_seconds


def test_pair_changes_truth_only_with_user_authorization():
    a,b=make_family("pilot",0,16)
    assert a.graph_hash==b.graph_hash
    assert sum(x.text!=y.text for x,y in zip(a.messages,b.messages))==1
    assert a.truth_at(16).values!=b.truth_at(16).values
    for s in (a,b):
        truth=s.truth_at(16)
        assert score(truth.target(s.spec),truth,s.spec)["success"]


def test_authority_and_hypotheticals():
    truth=Truth();truth.apply(Message(1,"user","binding"),Event("set",((0,"Harbor"),)))
    truth.apply(Message(3,"user","consider"),Event("consider",((0,"Studio"),)))
    assert truth.values[0]=="Harbor"
    with pytest.raises(ValueError):truth.apply(Message(4,"assistant","I decide"),Event("set",((0,"Studio"),)))
    truth.apply(Message(5,"user","approved"),Event("set",((0,"Studio"),)))
    assert truth.values[0]=="Studio" and truth.evidence[0]==5


def test_dependencies_and_ambiguity():
    s=make_family("test",7,64)[0];truth=s.truth_at(64)
    target=truth.target(s.spec)
    assert target["clarify"]
    assert any(x is None for x in target["plan"][:6])
    truth.apply(Message(129,"user","approve"),Event("set",((1,"online"),)))
    assert truth.target(s.spec)["plan"][6]=="none"


def test_hidden_truth_cannot_change_observation():
    s=make_family("pilot",0,16)[0];transcript=list(s.messages[:8]);memory=WorkingMemory()
    before=observation(s.spec,transcript,memory)
    truth=s.truth_at(8);truth.values=["SECRET_ORACLE"]*6;truth.evidence=[999]*6
    after=observation(s.spec,transcript,memory)
    assert before==after
    encoded=json.dumps(before[0]);assert "SECRET_ORACLE" not in encoded and "graph_hash" not in encoded


def test_edits_are_bounded_and_do_not_mutate_sources():
    s=make_family("pilot",0,16)[0];sources=tuple(s.messages);mem=WorkingMemory()
    actor=cast("C5",s.family_id,17)[0]
    apply_action({"kind":"edit","slot":0,"value":"Studio","claim":"user said","source":1},actor,[actor],mem,"C5",6)
    assert mem.state[0]=="Studio" and s.messages==sources
    with pytest.raises(ValueError):mem.edit(9,"x","alias","claim",1)
    with pytest.raises(Exception):s.messages[0].author="character"


def test_family_partition_integrity():
    seen=set();hashes=set()
    for split in ("pilot","train","validation","test"):
        m=manifest(split,count=12)
        for row in m["families"]:
            assert row["id"] not in seen and row["graph_hash"] not in hashes
            seen.add(row["id"]);hashes.add(row["graph_hash"])
            assert row["worlds"]==["authorized","hypothetical"]
            if split in {"train","validation"}:assert not row["structural_holdout"]


def test_paired_metric_counts_family_not_turn():
    rows=[{"seed":17,"family_id":"x","world":w,"success":v} for w,v in [("authorized",True),("hypothetical",False)]]
    assert list(paired_success(rows).values())==[0]
    with pytest.raises(ValueError):paired_success(rows[:1])
    with pytest.raises(ValueError):paired_success(rows+rows)
    assert contrast(rows,rows,draws=100)["ci95"]==[0,0]
    assert holm({"a":.01,"b":.04})=={"a":.02,"b":.04}


def test_budget_accounts_failed_runs_and_heartbeats_once(tmp_path):
    path=tmp_path/"registry.jsonl"
    path.write_text('\n'.join(json.dumps(r) for r in [
        {"run_id":"a","gpu_reserved_seconds":10,"status":"running"},
        {"run_id":"a","gpu_reserved_seconds":20,"status":"failed"},
        {"run_id":"b","gpu_reserved_seconds":5,"status":"completed"}]))
    assert used_seconds(path)==25
    with pytest.raises(ValueError):RunConfig(active_gpu_hours_ceiling=97)


def test_character_count_and_private_reset():
    assert [len(cast(c,"x",17))+1 for c in ("C4","C5","C6")]==[2,3,5]
    a=cast("C5","x",17);a[0].history.append({"old":True})
    assert not cast("C5","x",17)[0].history


def test_audit_annotations_never_alias_character_history():
    s=make_family("pilot",0,16)[0];actors=cast("C5",s.family_id,17);mem=WorkingMemory()
    record=apply_action({"kind":"edit","slot":0,"value":"Studio","claim":"recall","source":1},actors[0],actors,mem,"C5",6)
    before=action_prompt(actors[0],actors,s.spec,list(s.messages[:3]),mem,"C5",6,8)[0]
    record.update(contrary_to_truth=True,oracle_answer="SECRET",prompt="HUGE AUDIT TRACE")
    after=action_prompt(actors[0],actors,s.spec,list(s.messages[:3]),mem,"C5",6,8)[0]
    assert before==after
    assert "SECRET" not in json.dumps(after) and "contrary_to_truth" not in json.dumps(after)


def test_communication_delivery_and_no_interaction_control():
    actors=cast("C5","x",17);mem=WorkingMemory()
    action={"kind":"peer","target":actors[1].alias,"claim":"Support my proposal","slot":0,"value":"Studio"}
    assert apply_action(action,actors[0],actors,mem,"C5",6,True)["applied"]
    assert len(actors[1].inbox)==1
    actors[1].inbox.clear()
    assert not apply_action(action,actors[0],actors,mem,"A3",6,True)["applied"]
    assert actors[1].inbox==[]
    assert not apply_action({"kind":"edit","slot":0,"value":"Studio"},actors[0],actors,mem,"C5",6,True)["applied"]
