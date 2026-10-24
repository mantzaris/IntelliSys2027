# Persistent Character Conflict: resumable state

Started: 2026-10-23. Author-directed research; no submission or publication authorized.
Repository scope: this directory only; branch `main`; commits local, user pushes.

## Overnight supervision — active

Window: **2026-10-24 02:36:22–12:36:22 UTC** (October 23, 22:36 through
October 24, 08:36 America/New_York). See
`reports/overnight_20261024T023622Z/WORK_LOG.md`, `LATEST_STATE.json`, and the
incremental analysis README at `analysis/overnight/README.md`.
The existing core PID **787315** and review coordinator PID **1291869** retain
ownership. No additional controller or GPU worker was started. Qwen seed17 paired
successes are base 67/240, C1 186/240, C3 177/240, C4 179/240 and C5 168/240.
C5−C3 is −3.75 percentage points (exploratory family interval −8.33 to +0.83);
C5−C1 is −7.50 points (−11.25 to −4.17). These intervals do not estimate
training-seed uncertainty. The first C5 comparison is negative relative to both
trained controls; the full planned inference remains pending. A1 seed17 is now complete at 169/240; C5−A1 is −0.42 points
(family interval −5.42 to +4.58), without evidence of equivalence or a narrative
advantage. The original queue advanced to C1 seed29 collection. Ten collections
and ten fits have exact incremental audits; 27 completed stages have verified
remote/local evidence. Both
scientific freezes remain unchanged. The overnight session will leave healthy
original work running under its existing resource controls at handoff.

## Review follow-up starting snapshot (superseded by live overnight state above)

The original 241-stage core controller remains active (session **14639**, host PID
**787315**). Its live state is `artifacts/campaign_state.json`; do not launch a
second core queue. At this review, corrected Qwen C1 seed17 and C3 seed17 tests
are complete: 186/240 and 177/240 paired successes, respectively; untrained Qwen
is 67/240. C4 seed17 antagonist-free evaluation is active after both fits completed. The primary C5−C3 multi-seed
comparison remains pending. Every one of the 58 frozen files remains unchanged.
Current core freeze SHA256:
`135e78e2423d0bc42e340098021a912df269a39949d50cb6fbf91d4edb93f2f3`.

The author requested post-review diagnostics in `supplements/review_001/`.
All ten snapshot findings were reproduced from completed eligible artifacts.
See its `REVIEW_RESPONSE.md`, protocol, separate tables and provenance manifest.
The CPU exposure audit counts actual loss-contributing tokens/windows, including
orphaned suffix masking, rather than buffer-loaded windows alone. C1 round-one
recovery uses 14 windows from nine families repeatedly. Human review of the
60-item historical action packet remains pending, with two blank rating forms.

Only the old CPU-only unseen-profile and final-report waiters were stopped to
implement the author's new scheduling priority. Their prior states/commands are
preserved in `artifacts/review_001/superseded_cpu_waiters.json`. No core controller
or active GPU operation was interrupted. A single replacement review coordinator is active (session **53621**, host PID
**1291869**), CPU-only waiting for the entire core queue, then profile and freeze a timing-based scope
before reading diagnostic outcomes. It caps new review work at two reserved
GPU-hours within 96 and preserves 30 minutes contingency plus a final-batch margin.
Review A precedes B; optional routing/severity/balanced work and then the earlier
unseen-profile supplement run only if their gates pass. Do not restart the older
waiters. Read `artifacts/review_001/controller_state.json` for coordinator status.

Source, compact tables and reports are committed on main; bulky prompts, raw
outputs, tokenizers and packets remain ignored. No push, publication or submission.
Scientific interpretations and human validation remain pending author review.

## Hardware and storage

- Existing RunPod: NVIDIA RTX 6000 Ada, 49,140 MiB reported VRAM; no GPU jobs at inspection.
- Python environment initially PyTorch 2.8.0+cu128, CUDA runtime 12.8; driver 595.91.07.
- `/workspace` currently resolves to container overlay, NOT a verified persistent volume.
- Remote workspace: `/workspace/dualingCharacters`.
- Local durable mirror: `artifacts/` (Git ignored). Local free space initially 37 GiB.
- Store source, small manifests/configs, compact results and reports in Git. Keep
  full outputs, generated examples, dependency caches and adapters outside Git.
- No rental, paid API, instance termination, or unrelated-job changes authorized.

## Budget

Ceiling: 96 active GPU-hours, including profiling, failures and all model families.
Initial profiling/pilot allocation: approximately 2 GPU-hours maximum before
re-estimation. Track process GPU reservation time conservatively (not utilization
weighted), separate elapsed pod wall time, tokens, VRAM and known price. Actual
pod hourly rate unknown; dollar cost must remain unknown.

## Executed and running evidence (2026-10-23)

- `profile-bf16-001`, `profile-nf4-001`: four actual LoRA optimizer steps each;
  changed adapter checksums. BF16 selected on measured speed and adequate VRAM.
- `pilot-c3-001`: INVALID; audit/history aliasing could expose evaluator annotations.
  Fixed with allowlisted deep copies and regression test. Preserve its costs/logs.
- `pilot-c3-002`, `pilot-c5-001`: 32 LoRA steps each, 131,072 training input tokens;
  four distinct held-out pilot families, antagonists removed. Paired success C3
  1/4, C5 2/4. These are exploratory and use the earlier optional-peer protocol.
- `profile-phi-001`: four actual Phi LoRA steps, exact pinned revision; passed.
- `mechanism-v2-001`: all eight mechanism conditions executed. Peer channels
  function, but invalid action formatting motivates a shared decoding schema.
- `vllm-profile-001`: accelerated inference compatible; 64 unique pilot prompts
  completed in 4.54 seconds after engine initialization.
- `mechanism-v3-001`: all eight conditions complete, 32 paired pilot families,
  shared schema, no malformed defender objects. C1 12/32, C3 4/32, C4 10/32,
  C5 15/32, C6 8/32, A1 11/32, A2 13/32, A3 15/32 paired successes. Frozen
  policies only, not a learned comparison. C5 delivered 230 antagonist messages;
  no repeated directed-coordination candidates passed the typed criterion.
- `pilot-v4-*`: matched 32-step, 131,072-input-token balanced training pilots,
  evaluated without antagonists on 16 separate 32-turn pilot families. Qwen base
  6/16, C3 5/16, C5 6/16; C5−C3 +0.0625, family interval [−0.1875,+0.3125].
  Phi base 4/16, C5 2/16. One training seed; these do not establish H1 or replication.
  **The trained v4 entries are excluded from intended-method efficacy under
  amendment 002 for incompatible target serialization.** The numbers remain
  historical records, with all artifacts and costs retained.
  The v4 source archive is `artifacts/source_snapshots/pilot-v4-source.tar.gz`.
- `pilot-severity-001`: identical frozen reference observations; direct C3 actions
  flipped 50/243 initially correct states, C5 10/241. Severity differs despite
  matched opportunity caps. This is a pilot diagnostic, not a training effect.
- `profile-bf16-isolated-001`, `profile-phi-isolated-001`: final block-diagonal
  training attention works; four real steps each, changed adapters, respectively
  3.04 and 2.17 seconds per step in the small profile.
- `pilot-alias-refresh-001`: updated defender plus frozen characters; 96/96 actions
  applied, 34 delivered peer messages; private role-label leak removed. Both
  clean/recovery supervision pools nonempty (18/2 eligible windows).
  This refresh used an excluded v4 adapter and is also excluded under amendment 002.
- `mechanism-final-001`: completed and mirrored locally. Nine conditions
  (including C2), eight paired pilot families, final explicit prior assistant
  proposal and shared action scheduler. All 144 conversations completed without
  malformed defender objects; clean paired success was 3/8. GPU verified idle.
- Official LongMemEval cleaned release pinned and downloaded; 50 IDs selected
  by hash before generation. Official IntelliSys LaTeX template downloaded and
  an anonymized, explicitly incomplete review scaffold compiled locally.
- `reports/PILOT_RESULTS.md` and figures regenerate from saved evidence.

`study_draft.json` is superseded by frozen `study_plan.json`.
Main/ablation/replication cells remain explicitly pending until actual completion.
The candidate schedule retains 36 independently trained condition/seed models,
two refresh rounds, 256 steps × 4096 input tokens per round (2,097,152 total),
240 paired test families and 64 turns. Optional 32/128-turn sweeps use seed 17;
main conditions, A1/A2/A3 and Phi C1/C3/C5 retain three seeds (17,29,43).
Original pre-test forecast, superseded by amendment 002: 85.199 total reserved GPU-hours including
completed work, leaving 10.801 hours contingency. Forecasts are not actual
consumption. Completed pilots used 1.749 reserved GPU-hours.

The user requested the human packet now and raters later. Human ratings remain
pending. Two automatic approval-review timeouts on a Git commit were resolved
after the user explicitly requested a retry; commit `5ccbfa0` succeeded. Continue
authorized commits on main without asking again. No push or publication.

Completed raw traces can be losslessly compressed with verified SHA256 and read
as `.jsonl.gz`; active files and supervision remain plain. Identical completed
checkpoints are hard-linked without removing named artifacts. All remain Git ignored.

## Next actions

1. Monitor the existing `pcc.campaign` controller; do not launch a second copy.
   It serializes jobs, mirrors every minute, preserves checkpoints, refuses changed
   hashes, compresses completed traces, and regenerates the package at completion.
2. Monitor infrastructure and the 96-hour ceiling. Keep test choices fixed; inspect
   failures without selecting by significance. Audit and document any resume alias.
3. Run `bash analysis/regenerate_all.sh` after synchronized completed stages for
   the full integrity audit, frozen analysis, explicitly post-baseline descriptive
   tables and manuscript. Complete scientific author review and the final report.
4. The supplemental controller is already in a CPU-only wait in execution
   session `68875`; do not launch another copy. Its state/log are
   `artifacts/unseen_profiles_controller_state.json` and
   `artifacts/unseen_profiles_controller.log`. It acquires the shared queue lock
   after all 241 core stages (including four explicit rerun aliases) complete, checks the fixed 3.5-hour remaining-budget
   gate, then runs the ten declared exploratory profile tests if permitted.
   Otherwise it records the unmet gate. No supplemental GPU job has started.
   See `analysis/UNSEEN_PROFILES.md`; do not alter the primary freeze or queue.

## Recovery after interruption

The original controller was launched on 2026-10-23 at approximately 16:40 UTC through
session `38552`, then replaced after the documented boundary hold by session
`67629` at approximately 18:16 UTC. Its log is `artifacts/campaign_controller.log`,
current stage is in `artifacts/campaign_state.json`, and stage logs/configurations
are in `artifacts/campaign_configs/`. Do not launch a duplicate controller. At the
first live resource check, Qwen's base evaluation was on track for about 43 minutes
against its frozen 44.3-minute forecast; this is progress accounting, not an outcome.

Read this file, `DECISIONS.md`, `configs/`, and `artifacts/run_registry.jsonl`.
Inspect existing pod jobs before restarting. Resume existing completed artifacts;
never overwrite a run ID or start a concurrent GPU model. Reconcile remote and
local artifacts using `scripts/sync.sh`. Do not call a partial package submission-ready.

## Automatic execution update

2026-10-23T18:10:07Z: Campaign stopped incomplete: [Errno 21] Is a directory: '/home/resort/Documents/repos/IntelliSys2027/dualingCharacters/artifacts/campaign_configs/main-qwen-c1-17-r0-collect.json'. See the run registry and regenerated AUTHOR_REVIEW report. Human ratings and scientific author review remain pending. Nothing was pushed or submitted.

This was the deliberately installed infrastructure boundary hold, not a GPU run
failure. Both baselines were preserved. Full archive verification and hold release
completed at 2026-10-23T18:13:48Z, with 3.217735 reserved GPU-hours consumed.

## Serialization repair hold — 2026-10-23 19:59 UTC

The original queue is held by `artifacts/campaign_boundary_hold.json` after the current C1 evaluation. CPU grammar checks accept 0/1,568 saved training completions in their current order and 1,568/1,568 after schema-order serialization, with identical values. Affected completed training/evaluation and dependent refresh runs are excluded explicitly in `configs/run_exclusions.json`; all artifacts and costs remain. No completed trained-test metric informed this decision. Baselines and the original C1 round-zero collection remain valid. See `reports/SERIALIZATION_AMENDMENT_002.md`. Do not remove the hold until corrected GPU pilot gates, restart aliases and the amended freeze are audited. The supplemental controller remains CPU-only pending the original queue; its cached freeze must be refreshed before execution.

## Automatic execution update

2026-10-23T20:07:41Z: Campaign stopped incomplete: Infrastructure hold before another GPU stage: Audit confirmed training supervision serializes clarify/evidence/plan/state, while the installed inference grammar starts with state. Hold after the current C1 evaluation for a documented serialization repair; no completed trained-test outcome was inspected to decide this hold.. See the run registry and regenerated AUTHOR_REVIEW report. Human ratings and scientific author review remain pending. Nothing was pushed or submitted.

The old main controller exited cleanly at the planned boundary (execution session
67629). Its first C1 evaluation is retained as excluded; it consumed 46.83 minutes.
Repair source commit `67f8e55` executed three 32-step LoRA pilots in session 36013;
all three fits and evaluations completed. A subsequent serialized controller in
session 21162 runs matched current-source Qwen/Phi references and a short updated
C5 refresh check. Main hold remains installed. The optional supplemental controller
(session 73013) was stopped while CPU-only waiting so it cannot retain a stale
freeze; restart it only after amendment 002 is finalized. No supplementary GPU
job has run. Do not launch a second main or pilot controller.

## Current execution — amendment 002 released

At 2026-10-23 20:34:47 UTC, the serialization hold was released after all gates.
The active main controller is execution session **14639**, with the same
`artifacts/campaign_controller.log` and `artifacts/campaign_state.json` paths.
It resumed at `main-qwen-c1-17-r0-fit-format2`, reusing the original valid
round-zero supervision. Four fixed `-format2` aliases preserve original invalid
files and every consumed resource. All other original jobs and scientific choices
remain fixed. Do not start a duplicate controller.

Scientific source commit: `a62f1881d23df2282b410243ad4575bb11d1d74a`.
Freeze commit: `45b79bd`; freeze SHA256:
`135e78e2423d0bc42e340098021a912df269a39949d50cb6fbf91d4edb93f2f3`.
The amendment verifies 58 source/configuration files and passed 23 CPU tests.
The completed local artifact audit verified 41 runs, 623 recorded source files,
135 checkpoint files and 36 trace archives. Prior freezes remain preserved.

The restarted supplemental controller is **session 68875**, CPU-only waiting for
the original queue and its unchanged minimum 3.5-hour remaining-budget gate.
Its protocol hash is unchanged. Earlier main/pilot controllers (67629, 36013,
21162) are finished; the earlier supplemental waiter 73013 was stopped before
any GPU work. At release, all attempts consumed **5.339829 reserved GPU-hours**;
the conservative amended core forecast is **92.742568 hours total**, including
those attempts. Actual price remains unknown. Human ratings and author review
remain pending, and the primary three-seed comparison has no eligible result yet.

At 2026-10-23 20:55 UTC, corrected C1 round zero completed 256 steps, 1,048,576 input tokens and 48,838 supervised target tokens in 1,140.637 reserved seconds. Its final adapter SHA256 is `4c7ce600b71d3fe63583b4fbaadd910e32ce7f7a883f21366e8e581afed3645c`. Round-one collection loaded exactly that hash. Initial weights and supervision bytes match the original attempt; all original costs remain.

At 2026-10-23 21:30 UTC, corrected C1 round one completed 256 steps, 1,048,576
input tokens and 48,845 supervised target tokens in 1,217.850 reserved seconds.
Its initial weights exactly match round zero's final adapter; its final SHA256 is
`24e6c8f7287f1c3133203ab34e947cfce43a22f72ee2ced7ee6d6308b2570edc`.
The second round consumed 501 distinct buffered windows and 473 repeated entries;
these counts are not additional independent trajectories. Both rounds together
used 512 steps, 2,097,152 input tokens and 97,683 supervised target tokens. The
fixed final adapter is now being evaluated on all 240 paired 64-turn test families.
Six completed eligible stage lineages verify; no eligible trained test result is
complete at this update. All attempts have consumed about 6.227 reserved hours.

The CPU-only final reporting waiter is execution session **26434**. Its state is
`artifacts/final_report_controller_state.json`. It makes no model calls and waits
for the existing core controller plus a terminal supplemental decision, including
a budget skip. It then acquires the shared controller lock, runs the complete
saved-evidence regeneration and commits compact reports on main. Do not launch a
second waiter. Its six-part factual report is `reports/EXECUTION_REPORT.md`; that
report names incomplete stages and never treats scheduled work as measured evidence.

At 2026-10-23 21:38 UTC, the active C1 evaluation had 6,336 mirrored requests out
of 30,720. The authorized GPU was fully utilized, with about 39 GiB resident VRAM.
Local free space was about 32 GiB and remote free space about 27 GiB. These are
infrastructure progress checks, not test outcomes. The updated local manuscript
compiled successfully to 14 pages. Four human-packet and three reporting-control
unit checks passed; no human annotations exist.

At 2026-10-23 22:14 UTC, `main-qwen-c1-17-eval-format2` completed all 480
64-turn conversations and 30,720 defender requests in 2,657.650 reserved seconds.
The fixed final adapter achieved 186/240 paired successes (77.5%) and 390/480
per-conversation successes (81.25%). The untrained Qwen reference is 67/240
(27.9167%) on the same paired families. These are descriptive observations for
one clean-training seed, not the primary character contrast or a seed-variation
estimate. The evaluation summary SHA256 is
`36077bb0f19535c15e3aaf051898e264b1a1c4fdda4285c065a7a13ded56dcc7`.
The full local audit verified 45 completed runs, 751 recorded source files,
153 checkpoint files and 38 archives; all seven eligible scheduled stage
lineages passed. Every excluded attempt remains recorded. The existing queue
advanced to `main-qwen-c3-17-r0-collect` with about 6.965 total reserved GPU-hours
consumed before that stage. No scientific input or selection rule changed.
