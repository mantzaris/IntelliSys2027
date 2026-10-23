# Persistent Character Conflict: resumable state

Started: 2026-10-23. Author-directed research; no submission or publication authorized.
Repository scope: this directory only; branch `main`; commits local, user pushes.

## Current phase

Phase B active. Source audit, state-machine implementation, CPU invariant tests,
real GPU inference, BF16/NF4 profiles, Qwen learning pilots and Phi compatibility
training have executed. No confirmatory test results exist. No scientific
advantage has been established. Confirmatory test access remains locked until
the pilot gates and a hashed analysis plan are complete.

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
- `mechanism-v3-001`: requested next, schema-controlled audit across all 32 pilot
  families. Inspect remote status before restarting any job.
- Official LongMemEval cleaned release pinned and downloaded; 50 IDs selected
  by hash before generation. Official IntelliSys LaTeX template downloaded and
  an anonymized, explicitly incomplete review scaffold compiled locally.
- `reports/PILOT_RESULTS.md` and figures regenerate from saved evidence.

No `configs/freeze.json` exists. `study_draft.json` is NOT authorization to unlock
tests. Main/ablation/replication table cells remain explicitly pending.

## Next actions

1. Finish schema-controlled mechanism audit and verify inference with trained
   LoRA adapters in both model families.
2. Complete fixed-fault recovery and secondary validation orchestration.
3. Audit distinctness, interference, solvability, headroom and realistic throughput.
4. Allocate remaining budget and freeze only after pilot evidence supports a
   functioning experiment. Never alter design using confirmatory outcomes.

## Recovery after interruption

Read this file, `DECISIONS.md`, `configs/`, and `artifacts/run_registry.jsonl`.
Inspect existing pod jobs before restarting. Resume existing completed artifacts;
never overwrite a run ID or start a concurrent GPU model. Reconcile remote and
local artifacts using `scripts/sync.sh`. Do not call a partial package submission-ready.
