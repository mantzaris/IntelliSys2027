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


def test_trace_compaction_is_lossless_and_leaves_active_runs(tmp_path):
    from pcc.storage import compact_completed
    from pcc.diagnostics import jsonlines
    for status in ("completed","running"):
        run=tmp_path/"artifacts/runs"/status;run.mkdir(parents=True)
        (run/"status.json").write_text(json.dumps({"status":status}))
        (run/"evaluation.jsonl").write_text('{"response":"measured"}\n')
    completed=tmp_path/"artifacts/runs/completed/evaluation.jsonl"
    before=sha256(completed);compact_completed(tmp_path)
    assert not completed.exists() and completed.with_suffix(".jsonl.gz").exists()
    assert jsonlines(completed)==[{"response":"measured"}]
    assert json.loads((completed.parent/"trace_archives.json").read_text())["evaluation.jsonl"]["original_sha256"]==before
    assert (tmp_path/"artifacts/runs/running/evaluation.jsonl").exists()


def test_prose_rollout_keeps_internal_actions_out_of_source_transcript(tmp_path):
    from pcc.config import RunConfig
    from pcc.environment import OPTIONS
    from pcc.evaluation import run_episodes
    class FakeBackbone:
        config=RunConfig(batch_size=1)
        def __init__(self):self.prompts=[]
        def generate(self,prompts,*args,**kwargs):
            self.prompts.extend(copy.deepcopy(prompts));results=[]
            for prompt in prompts:
                internal=prompt[0]["content"].startswith("You are the responsible planning assistant.")
                state=[options[0] for options in OPTIONS]
                parsed={"state":state,"plan":state+["ferry","projector"],"evidence":[1]*6,"clarify":[]} if internal else {}
                results.append({"raw":"INTERNAL_TRACE" if internal else "PUBLIC_PROSE","parsed":parsed,"input_tokens":1,"output_tokens":1})
            return results
    model=FakeBackbone();scenario=make_family("pilot",0,16)[0]
    summaries,_=run_episodes(model,[scenario],"base",tmp_path/"episode.jsonl",prose_responses=True)
    assert summaries[0]["message_count"]==33 and summaries[0]["internal_memory_generations"]==16
    assert len(model.prompts)==32
    assert "INTERNAL_TRACE" not in json.dumps(model.prompts)
    assert "PUBLIC_PROSE" in json.dumps(model.prompts)


def test_completed_archive_survives_stale_live_mirror_prefix(tmp_path):
    from pcc.storage import compact_completed
    from pcc.diagnostics import jsonlines
    run=tmp_path/"artifacts/runs/complete";run.mkdir(parents=True)
    (run/"status.json").write_text(json.dumps({"status":"completed"}))
    source=run/"evaluation.jsonl"
    first='{"turn":1}\n';complete=first+'{"turn":2}\n'
    source.write_text(complete);compact_completed(tmp_path)
    archive=source.with_suffix(".jsonl.gz");before=sha256(archive)
    manifest=(run/"trace_archives.json").read_bytes()
    source.write_text(first)  # Old plain file left by an earlier rsync pull.
    result=compact_completed(tmp_path)
    assert result["stale_or_duplicate_prefixes_removed"]==1
    assert sha256(archive)==before and not source.exists()
    assert (run/"trace_archives.json").read_bytes()==manifest
    assert jsonlines(source)==[{"turn":1},{"turn":2}]
    source.write_text('{"turn":"conflicting"}\n')
    with pytest.raises(ValueError,match="conflicts"):
        compact_completed(tmp_path)
    assert source.exists() and sha256(archive)==before


def test_completed_trace_missing_turns_is_not_archived(tmp_path):
    from pcc.storage import compact_completed
    run=tmp_path/"artifacts/runs/incomplete";run.mkdir(parents=True)
    (run/"status.json").write_text(json.dumps({"status":"completed"}))
    (run/"evaluation_summary.json").write_text(json.dumps([{"horizon":2}]))
    source=run/"evaluation.jsonl";source.write_text('{"turn":1}\n')
    with pytest.raises(ValueError,match="row count"):
        compact_completed(tmp_path)
    assert source.exists() and not source.with_suffix(".jsonl.gz").exists()


def test_persisted_supervision_matches_public_decoding_order(tmp_path):
    from itertools import permutations
    from pcc.training import serialize_completion
    from pcc.resources import append_json
    from pcc.schemas import defender_schema
    # Exercise the actual persistence boundary which alphabetizes JSON keys.
    target={"state":[None]*6,"plan":[None]*8,"evidence":[None]*6,"clarify":[]}
    path=tmp_path/"supervision.jsonl"
    append_json(path,{"completion":target})
    loaded=json.loads(path.read_text())["completion"]
    assert list(loaded)!=list(defender_schema()["properties"])
    expected=serialize_completion(target)
    for order in permutations(target):
        actual=serialize_completion({key:loaded[key] for key in order})
        assert actual==expected
        assert json.loads(actual)==target
        assert list(json.loads(actual))==list(defender_schema()["properties"])
    with pytest.raises(ValueError):serialize_completion({**target,"oracle_score":1})
    with pytest.raises(ValueError):serialize_completion({k:v for k,v in target.items() if k!="evidence"})


def test_completed_restart_requires_exclusion_and_preserves_design(tmp_path):
    from pcc.campaign import load_overrides,resolve_job
    configs=tmp_path/"configs";configs.mkdir()
    run=tmp_path/"artifacts/runs/original";run.mkdir(parents=True)
    (run/"status.json").write_text(json.dumps({"status":"completed"}))
    entry={"run_id":"original-format2","reason":"audited interface defect","amendment":"amendment.md"}
    (configs/"serialization_restarts.json").write_text(json.dumps({"original":entry}))
    (tmp_path/"amendment.md").write_text("Preserved prior attempt; no outcome-based change.")
    with pytest.raises(ValueError,match="explicit exclusion"):load_overrides(tmp_path)
    (configs/"run_exclusions.json").write_text(json.dumps({"original":"interface defect"}))
    overrides=load_overrides(tmp_path)
    job={"id":"next","model":"qwen","seed":17,"families":240,"horizon":64,"adapter":"artifacts/runs/original/training/final"}
    result=resolve_job(job,overrides)
    assert result=={**job,"adapter":"artifacts/runs/original-format2/training/final"}
    assert resolve_job({**job,"id":"original"},overrides)["id"]=="original-format2"
    (configs/"serialization_restarts.json").unlink()
    (tmp_path/"artifacts/campaign_resume.json").write_text(json.dumps({"original":{"run_id":"replacement","reason":"routine retry"}}))
    with pytest.raises(ValueError,match="completed run"):load_overrides(tmp_path)


def test_excluded_result_does_not_enter_primary_but_cost_is_counted(tmp_path):
    from pcc.study_analysis import analyze
    (tmp_path/"configs").mkdir()
    run=tmp_path/"artifacts/runs/main-qwen-c1-17-eval";run.mkdir(parents=True)
    (tmp_path/"configs/run_exclusions.json").write_text(json.dumps({run.name:"interface defect"}))
    (run/"status.json").write_text(json.dumps({"run_id":run.name,"status":"completed","config":{"model":"qwen","condition":"C1"},"gpu_reserved_seconds":123,"train_tokens":4096}))
    # Deliberately invalid metric data must never be read into analysis.
    (run/"evaluation_summary.json").write_text('not eligible metric data')
    rows,contrasts=analyze(tmp_path)
    row=next(x for x in rows if x["model"]=="qwen" and x["condition"]=="C1")
    assert row["paired_success"] is None and row["executed_seeds"]==0
    assert row["gpu_reserved_seconds"]==123 and row["train_tokens"]==4096
    assert not contrasts
