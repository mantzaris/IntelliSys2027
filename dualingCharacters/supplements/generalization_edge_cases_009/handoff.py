"""Final current-state record, separate from the locked009 population."""
import os,shlex,subprocess,shutil
from zoneinfo import ZoneInfo
from .common import *
def main():
 from .resources import main as resources
 from supplements.review_001.controller import connection
 resources();r=read(HERE/'reports/RESOURCES.json');session=read(HERE/'SESSION.json');resume=read(HERE/'reports/CORE_RESUMPTION.json');state=read(ROOT/'artifacts/campaign_state.json');run=state['active_job']['id']
 alive=subprocess.check_output(['ps','-p',str(resume['native_owner_pid']),'-o','pid=,etime=,comm='],text=True).strip();assert alive
 os.environ.update(read(ART/'original_owner_private.json')['environment']);ssh,target,remote=connection()
 script="import pathlib,json,subprocess,shutil; p=pathlib.Path('artifacts/runs')/"+repr(run)+"/'status.json'; s=json.loads(p.read_text()) if p.exists() else {}; print(json.dumps({'status':{k:s.get(k) for k in ['run_id','status','model_calls','gpu_reserved_seconds']},'gpu':subprocess.check_output(['nvidia-smi','--query-gpu=name,memory.used,utilization.gpu','--format=csv,noheader'],text=True).strip(),'compute_processes':subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip(),'free_bytes':shutil.disk_usage('.').free}))"
 remote_state=json.loads(subprocess.check_output(ssh+[target,'cd '+shlex.quote(remote)+' && python3 -c '+shlex.quote(script)],text=True,timeout=40))
 ops={'utc':now(),'native_owner':alive,'current_core_job':run,'remote':remote_state,'local_free_bytes':shutil.disk_usage(ROOT).free,'review_owner_unchanged':read(ROOT/'artifacts/review_001/controller_state.json'),'no_stage009_waiter':True,'boundary_hold_absent':not (ROOT/'artifacts/campaign_boundary_hold.json').exists()};write(HERE/'reports/FINAL_OPERATIONAL_STATE.json',ops)
 start=datetime.fromisoformat(session['start_utc']);end=datetime.now(timezone.utc);zone=ZoneInfo('America/New_York');elapsed=(end-start).total_seconds();assert end<datetime.fromisoformat(session['deadline_utc']);assert r['stage_ledger_seconds']<=5400
 closure={'utc':end.isoformat(),'inference_finished':True,'native_owner_restored':resume['native_owner_pid'],'no_scheduled_stage009_inference':True,'no_new_waiter':True,'additional_inference_not_authorized_by_this_closed_stage':True};write(HERE/'EXECUTION_CLOSED.json',closure)
 final={'start_utc':start.isoformat(),'handoff_report_utc':end.isoformat(),'start_America_New_York':start.astimezone(zone).isoformat(),'handoff_America_New_York':end.astimezone(zone).isoformat(),'elapsed_seconds_at_report':elapsed,'hard_deadline_utc':session['deadline_utc'],'inference_finished_utc':resume['utc'],'input_commit':session['input_commit'],'branch':subprocess.check_output(['git','branch','--show-current'],text=True).strip(),'commit_note':'Final scoped commit follows this report; obtain with git log -1 -- supplements/generalization_edge_cases_009. Nothing pushed.','resources':r};write(HERE/'reports/FINAL_SESSION.json',final)
 text=f'''# Stage009 session handoff

Started **{start.isoformat()} UTC** ({start.astimezone(zone).strftime('%Y-%m-%d %H:%M:%S %Z')}, America/New_York). Handoff prepared **{end.isoformat()} UTC** ({end.astimezone(zone).strftime('%Y-%m-%d %H:%M:%S %Z')}). Elapsed at report: **{elapsed/60:.2f} minutes**. Hard deadline: **{session['deadline_utc']}**; all inference and native-owner restoration finished at **{resume['utc']}**. Final verification and the local commit occur inside the same three-hour ceiling. The session finishes early because the admitted empirical grid, optional replay and reproducible package are complete; it does not wait for the independent core campaign.

Input HEAD: `{session['input_commit']}` on main, with a clean starting tree. Reference commits were not restored. Only this supplement is committed. The final commit ID is supplied in the chat handoff and `git log -1 -- supplements/generalization_edge_cases_009`; no push, publication, submission or external contact occurred.

## What ran

The timing-only rule admitted the reduced tier: **192/192 research conversations**,16 unique families, two paired worlds, C3/C5/A1, Qwen and Phi, rollout seed17. Each conversation has32 user turns,32 generated structured answers and12 actor calls. Main research: **8,448 calls**. Development profiles:16 conversations and704 calls, excluded from all research denominators. Optional delivery replay:16 exact reconstructed recipient states, two variants and two seeds,64 calls. **Total new calls: {r['stage_model_calls']:,}**; no missing main cells, no failed GPU run, no retry, no training, no model judge and no human rating.

Both pinned base checkpoints were already cached: Qwen `cdbee75f17c01a7cc42f958dc650907174af0554` (Apache-2.0), Phi `cfbefacb99257ffa30c83adab238a50856ac3083` (MIT). Native chat-template hashes and inference versions are in each archived status. The actual RTX6000Ada was used sequentially; HF offline mode prohibited downloads. No LoRA adapter was loaded. Changing backbone changes the entire simulated system.

Research allocation and code freeze: `ALLOCATION.json` and `SCIENTIFIC_FREEZE.json`, created before research calls. Historical evidence was inspected at startup around22:46UTC; later core completions are operational updates only. No old descriptive population or stage008 manuscript was rewritten. Fresh scripts use the existing six-field ontology and tools; the scope is context and conversational composition, not external validation or transfer of trained adapters.

## Measured interpretation

- Qwen reproduces the lower-edit/higher-recollection C5 profile; Phi uses zero edits in all conditions and reverses the C5−C3 recollection contrast. A backbone-general recollection claim is therefore unsupported.
- A1 retains high typed persistence:189/192 Qwen and117/121 Phi eligible direct transitions. Biographies are not necessary for that behavior here; semantic coherence is not measured by this proxy.
- C5 paired decisive success is14/16 versus C3's13/16 on Qwen (+6.25pp,95% family interval[−12.5,31.25]) and10/16 versus12/16 on Phi (−12.5pp,[−31.25,0]). C5 whole-plan success is16/32 on both. Earlier negative training results and failed semantic screens remain unchanged.
- Every Phi condition prematurely commits during24/24 unresolved observations from four ambiguity conversations, despite correct final paired outcomes. This is a concrete limitation of terminal scoring, not24 independent failures.
- Replay changes one typed goal and seven API labels across32 paired state/seed comparisons, with zero adoption of the message goal in either arm. Its fixed tie rule yields15 A1 states and one C5 state; it cannot compare conditions or establish no influence.

Only4/16 focal fields coincide with an actor's owned field; only one family revises away from an owned option. The unfavorable actual-revision example and the distinction between recommendation and authorization are illustrated in `COUNTEREXAMPLES.md`. Such readings are AI-assisted and not semantic prevalence estimates.

## Resource reconciliation

Five model/supervisor reservations consumed **{r['model_run_reserved_seconds']/3600:.6f} hours** ({r['model_run_reserved_seconds']/60:.2f} minutes). The complete exclusive handoff interval consumed **{r['exclusive_handoff_seconds']/3600:.6f} hours** ({r['exclusive_handoff_seconds']/60:.2f} minutes), below90minutes. Its **{r['accounting_overhead_seconds']:.3f} seconds** of previously uncharged gaps are recorded exactly once as the zero-call `edge009-exclusive-overhead-v1` shared-ledger entry. Total stage009 charged time is consequently the full exclusive interval; it is not added again to model-run time.

Actual stage input/output tokens: **{r['stage_input_tokens']:,} / {r['stage_output_tokens']:,}**. Peak recorded allocation: **{r['peak_vram_bytes']/1024**3:.3f} GiB**, including backend KV reservations. Sampled GPU-busy time: **{r['stage_sampled_busy_seconds']/60:.2f} minutes**; this is distinct from reserved time. No dollar rate or billed pod uptime is known.

At {r['utc']}, the shared registry records **{r['project_recorded_seconds']/3600:.6f}/96 hours**, including continuing core work. Adding the preserved earlier stage008 handoff margin, conservative remaining core obligations, remaining two-hour review reserve and30-minute contingency gives **{r['project_total_with_obligations_hours']:.3f}/96 hours**. Stage009 overhead is already in that ledger and is not double counted. The forecast is a conservative timing scenario, not a guarantee about future run duration.

## Current ownership and recovery

Startup found the old native controller absent after its final rsync failed. Remote `extra-qwen-base-17-horizon32` was already complete and the GPU idle. Its completed evidence was mirrored without rerunning it. The authorized boundary hold was created while CPU preparation proceeded. After study execution, only that hold was archived and the exact original command/environment restored.

Original campaign controller: **PID{resume['native_owner_pid']}**, alive as `{alive}`. Current native job: **`{run}`**, remote status `{remote_state['status'].get('status')}`, calls `{remote_state['status'].get('model_calls')}`. Core completion count at the local operational cutoff: **{r['core_completed']}/241**. GPU snapshot: `{remote_state['gpu']}`. Remote free storage: **{remote_state['free_bytes']/1024**3:.2f} GiB**; local **{ops['local_free_bytes']/1024**3:.2f} GiB**. Review coordinator ownership is unchanged; intent002 remains disabled. No stage009 inference or new waiter remains scheduled. Healthy core work continues independently under its original budget.

Read-only state: `artifacts/campaign_state.json`, `artifacts/run_registry.jsonl`, `artifacts/campaign_configs/<run_id>.log`; this handoff's native log is `artifacts/generalization_edge_cases_009/core_resume.log`. The original private command/environment is preserved mode0600 in `artifacts/generalization_edge_cases_009/original_owner_private.json`, outside Git. If infrastructure later fails, first prove that both owner and GPU worker are absent; preserve partial outputs and use the existing audited `campaign_resume.json` mechanism. With the established connection environment, the native command remains `PYTHONPATH=src .venv/bin/python -m pcc.campaign`. Do not rerun the closed stage009 owner or start beside a healthy native owner.

## Verification and portable evidence

Eight focused unit tests and23 existing invariant/protocol regression tests passed. Known-answer and mutation checks cover quoted approval, supersession, conditional nonauthorization, scoped updates and ambiguity resolution. Core58, review21, intent34, and all subsequent historical scientific manifests/protected forms remain unchanged. The stage008 delivery manifest also passes. Two early utility-test failures (argument order and manifest-entry representation) were corrected before scientific execution; no benchmark or frozen historical file was changed.

Artifact integration verifies192 complete conversations,8,448 research calls, unique turn coverage, pinned revisions, configurations, time-indexed targets, token totals and33 exact selected/counterexample claim quotations. All recorded main prompts were below the4096-token input cap (maximum1785); supplied source lists were not additionally token-truncated. Twenty-four full-context links passed offline relocation checks. The baseline replay prompts reconstructed exactly; every paired replay differs only by the selected inbox payload. The eight main groups and four figures were visually inspected; the overview PDF is one page with filename-based companion references rather than machine-specific links.

A clean temporary export contains only baseline tracked files and intended009 files, with no original `artifacts/` directory. It verifies the committed archive hashes and regenerates nine numerical tables identically; complete dialogue rendering and quote checks pass there. Model weights, private access records and old bulk runs are absent. `evidence/edge009_records.tar.gz` contains all new JSON/JSONL evidence; the full chronological HTML is supplied compressed separately to avoid committing a redundant39MB copy. Extraction commands are in `REPRODUCE.md`. Code/quote checks establish reproducibility, not semantic or broad external validity.

## Start here and remaining decisions

[One-page overview](OVERVIEW.pdf) · [Offline index](INDEX.html) · [Detailed results](RESULTS.md) · [Eight matched dialogue groups](DIALOGUES.html) · [Counterexamples](COUNTEREXAMPLES.md) · [Evidence index](EVIDENCE_INDEX.md) · [Reproduction](REPRODUCE.md) · [Manuscript addendum](MANUSCRIPT_ADDENDUM.md).

The bounded empirical task is complete. The original full241-stage campaign and its required review diagnostics remain ongoing/pending, separately owned. No human ratings are requested or made a completion condition. The author should review the narrowed backbone-dependent claim, decide how much of this shared-schema extension belongs in the main paper versus an appendix, and retain the limitations on semantic interpretation and causal interaction. No stronger submission-readiness or acceptance claim is made.
'''
 (HERE/'SESSION_REPORT.md').write_text(text);print({'elapsed_minutes':elapsed/60,'native_job':run,'core_completed':r['core_completed'],'model_calls':r['stage_model_calls'],'closed':True})
if __name__=='__main__':main()
