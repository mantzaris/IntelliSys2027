"""Observed retrieval volume/coverage from executed structured-evaluation prompts.

Explicitly post-baseline descriptive reporting; no new hypothesis tests. Current
source visibility differs from validity of a reference remembered from earlier.
"""
from pathlib import Path
import gzip
import json
from pcc.diagnostics import trace_path
from pcc.analysis import paired_success
from pcc.resources import sha256
from pcc.eligibility import exclusions
from pcc.study_analysis import write_csv


def regenerate(root: Path):
    excluded=exclusions(root)
    rows=[];inputs={};snapshots=[]
    freeze=root/"configs/freeze.json";selected_families={f"test-{i:04d}" for i in json.loads(freeze.read_text())["plan"]["extension_family_numbers"]}
    inputs[str(freeze.relative_to(root))]=sha256(freeze)
    for status in sorted((root/"artifacts/runs").glob("*/status.json")):
        meta=json.loads(status.read_text());run=status.parent;cfg=meta["config"]
        if meta["status"]!="completed" or cfg["phase"]!="confirmatory" or run.name in excluded:continue
        summary=run/"evaluation_summary.json"
        if not summary.exists():continue
        summary_rows=json.loads(summary.read_text())
        expected_families=len(meta["family_numbers"]) if "family_numbers" in meta else meta["families"]
        if len(summary_rows)!=2*expected_families or len(paired_success(summary_rows))!=expected_families:
            raise ValueError("Incomplete fixed evaluation sample")
        horizons={r["horizon"] for r in summary_rows}
        if len(horizons)!=1:raise ValueError("Mixed horizons in an evaluation run")
        horizon=next(iter(horizons))
        path=trace_path(run/"evaluation.jsonl");reader=gzip.open if path.suffix==".gz" else open
        n=selected=assistant_sources=required=covered=references=visible_references=extra_clarifications=0
        final_required=final_covered=final_all_visible=0
        with reader(path,"rt") as stream:
            for line in stream:
                row=json.loads(line);body=json.loads(row["prompt"][-1]["content"]);sources=body["sources"]
                actual={s["index"] for s in sources}
                if actual!=set(row["visible_indices"]):raise ValueError("Logged visibility differs from the executed prompt")
                canonical={index for index in row["target"]["evidence"] if index is not None}
                refs=[index for index in row["generation"]["parsed"].get("evidence",[]) if index is not None]
                n+=1;selected+=len(sources);assistant_sources+=sum(s["author"]=="assistant" for s in sources)
                required+=len(canonical);covered+=len(canonical & actual)
                references+=len(refs);visible_references+=sum(index in actual for index in refs)
                extra_clarifications+=len(set(row["generation"]["parsed"].get("clarify",[]))-set(row["target"]["clarify"]))
                if row["turn"]==horizon:
                    final_required+=len(canonical);final_covered+=len(canonical & actual)
                    final_all_visible+=canonical<=actual
                if run.name=="base-qwen-eval" and row["family_id"] in selected_families and row["turn"]==32:
                    snapshots.append({"source_run":run.name,"family_id":row["family_id"],"world":row["world"],
                        "snapshot_turn":32,"selected_source_messages":len(sources),
                        "canonical_site_source_visible":row["target"]["evidence"][0] in actual,
                        "all_canonical_sources_visible":canonical<=actual,
                        "canonical_source_count":len(canonical),"canonical_sources_visible":len(canonical & actual)})
        if n!=2*expected_families*horizon:raise ValueError("Completed evaluation trace has missing turns")
        rows.append({"run_id":run.name,"model":cfg["model"],"condition":cfg["condition"],"seed":cfg["seed"],
            "setting":meta.get("extension","antagonist-free"),"horizon":horizon,"families":expected_families,
            "executed_turns":n,"defender_source_selection_calls":n,"source_message_occurrences":selected,
            "selected_source_messages_per_turn":selected/n,"assistant_source_occurrence_fraction":assistant_sources/selected,
            "canonical_authorizing_source_occurrences":required,"canonical_authorizing_sources_visible":covered,
            "canonical_authorizing_source_coverage":covered/required,
            "final_canonical_authorizing_source_coverage":final_covered/final_required,
            "final_conversations_with_all_canonical_sources_visible":final_all_visible,
            "final_all_canonical_sources_visible_rate":final_all_visible/(2*expected_families),
            "emitted_reference_occurrences":references,"emitted_references_currently_visible":visible_references,
            "emitted_reference_current_visibility":visible_references/references if references else None,
            "extra_clarification_fields_across_turns":extra_clarifications,
            "extra_clarification_fields_per_turn":extra_clarifications/n})
        for p in (status,summary,path):inputs[str(p.relative_to(root))]=sha256(p)
    result={"classification":"Post-baseline descriptive analysis of actual executed prompts; no changes to frozen endpoints or inferential tests",
        "coverage_definition":"Micro-average of canonical authorizing source indices present among the actual selected sources; repeated fields sharing one source count once per turn.",
        "visibility_definition":"Current visibility of emitted reference occurrences, not whether an earlier-seen reference is valid. The original exact-reference score is reported separately.",
        "cost_scope":"Defender source selection occurs at every turn in the fixed scaffold. Selected-message volume is measured; identifying unnecessary retrieval requires a separate necessity analysis, since rejection/hypothetical/ambiguity evidence can also matter. Character-source requests are outside these defender counts. Settings use their original fixed samples; the main 240-family sample and 48-family extensions are not interchangeable.",
        "clarification_scope":"Count of emitted field names absent from the evaluator's pending-field set, including extra fields when another clarification is legitimate.",
        "dependence":"Turn-level counts are descriptive totals, not independent experimental subjects.",
        "results":rows,"analysis_source_sha256":sha256(Path(__file__).resolve()),"inputs":inputs}
    out=root/"reports/tables";(out/"exploratory_retrieval.json").write_text(json.dumps(result,indent=2)+"\n")
    write_csv(out/"exploratory_retrieval.csv",rows)
    if snapshots and len(snapshots)!=96:raise ValueError("Incomplete fixed recovery snapshot coverage audit")
    snapshot_report={"classification":"Descriptive source-availability audit of the original fixed recovery snapshots; no cases selected or removed",
        "scope":"At turn 32, before the fixed site-memory erasure. That erasure leaves retrieved sources unchanged. Canonical-source absence is not a proof of impossibility; other legitimate evidence may help. All cases remain in recovery curves.",
        "cases":len(snapshots),"canonical_site_source_visible_cases":sum(r["canonical_site_source_visible"] for r in snapshots),
        "all_canonical_sources_visible_cases":sum(r["all_canonical_sources_visible"] for r in snapshots),
        "rows":snapshots,"analysis_source_sha256":sha256(Path(__file__).resolve()),
        "inputs":{k:v for k,v in inputs.items() if k=="configs/freeze.json" or k.startswith("artifacts/runs/base-qwen-eval/")}}
    (out/"exploratory_recovery_source_coverage.json").write_text(json.dumps(snapshot_report,indent=2)+"\n")
    write_csv(out/"exploratory_recovery_source_coverage.csv",snapshots)
    base={r["model"]:r for r in rows if r["condition"]=="base" and r["setting"]=="antagonist-free" and r["horizon"]==64}
    tex=[]
    if set(base)>={"qwen","phi"}:
        q,p=base["qwen"],base["phi"]
        tex.append("\\paragraph{Descriptive evidence-access audit.} A post-baseline audit of executed prompts found final-turn canonical-authorizing-source coverage of "
            f"{100*q['final_canonical_authorizing_source_coverage']:.1f}\\% for Qwen and {100*p['final_canonical_authorizing_source_coverage']:.1f}\\% for Phi. "
            f"All canonical sources were present in {q['final_conversations_with_all_canonical_sources_visible']}/480 and {p['final_conversations_with_all_canonical_sources_visible']}/480 final observations respectively. "
            "These figures concern the untrained scaffolds and measure source availability separately from citation validity or behavioral adherence.")
    if snapshots:
        tex.append(f"Within the 96 fixed Qwen recovery snapshots, the canonical authorizing source for the site field was visible in {snapshot_report['canonical_site_source_visible_cases']}, and all canonical authorizing sources were visible in {snapshot_report['all_canonical_sources_visible_cases']}. "
            "The recovery analysis retains all 96 cases. These descriptive availability counts do not prove that an individual case is solvable or impossible.")
    (root/"paper/generated_retrieval_diagnostics.tex").write_text("\n".join(tex)+"\n")
    print(json.dumps({"completed_runs_with_executed_retrieval_audits":len(rows)}))


if __name__=="__main__":regenerate(Path(__file__).resolve().parents[1])
