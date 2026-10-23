# Persistent Character Conflict: resumable state

Started: 2026-10-23. Author-directed research; no submission or publication authorized.
Repository scope: this directory only; branch `main`; commits local, user pushes.

## Current phase

Phase A / B implementation. No confirmatory test results exist. No scientific
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

## Next actions

1. Pin official model revisions and isolated Python dependencies.
2. Implement paired state-machine benchmark, information-boundary tests,
   character actions, retrieval, logging and serialized GPU runner.
3. Profile BF16 LoRA and 4-bit QLoRA; run actual recovery-supervision pilot.
4. Audit distinctness, interference, solvability, headroom and throughput.
5. Allocate remaining budget and freeze only after pilot evidence supports a
   functioning experiment. Never alter design using confirmatory outcomes.

## Recovery after interruption

Read this file, `DECISIONS.md`, `configs/`, and `artifacts/run_registry.jsonl`.
Inspect existing pod jobs before restarting. Resume existing completed artifacts;
never overwrite a run ID or start a concurrent GPU model. Reconcile remote and
local artifacts using `scripts/sync.sh`. Do not call a partial package submission-ready.
