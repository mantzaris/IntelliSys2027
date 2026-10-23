# Persistent Character Conflict: resumable state

Started: 2026-10-23. Author-directed research; no submission or publication authorized.
Repository scope: this directory only; branch `main`; commits local, user pushes.

## Current phase

Phase C: plan hash-frozen; starting the serialized confirmatory campaign. Real GPU inference and LoRA learning have executed in
both pinned families. The matched Qwen pilot is inconclusive; Phi's pilot is worse
than its base. No confirmatory test outcomes existed at freeze. `configs/freeze.json`
records 55 scientific-input hashes and all passed pilot gates, scientific source
commit `c96e8a0c986b8af008c1296a601ec9c881f419ae`, and 241 predetermined GPU stages.
Freeze SHA256: `3a35d0015e5447de1ca5eb3d6e77ab3c6e12ba3ad54bfcaf07799ad55443e525`.
Do not change endpoints, seeds, checkpoint rules or scientific inputs using results.

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
Measured conservative final forecast: 85.199 total reserved GPU-hours including
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

1. Synchronize source; run `pcc.campaign` locally with authorized SSH environment.
   It serializes jobs, mirrors every minute, preserves checkpoints, refuses changed
   hashes, compresses completed traces, and regenerates the package at completion.
2. Monitor infrastructure and the 96-hour ceiling. Keep test choices fixed; inspect
   failures without selecting by significance. Audit and document any resume alias.
3. Complete evidence/manuscript review, exact missing requirements and final report.

## Recovery after interruption

Read this file, `DECISIONS.md`, `configs/`, and `artifacts/run_registry.jsonl`.
Inspect existing pod jobs before restarting. Resume existing completed artifacts;
never overwrite a run ID or start a concurrent GPU model. Reconcile remote and
local artifacts using `scripts/sync.sh`. Do not call a partial package submission-ready.
