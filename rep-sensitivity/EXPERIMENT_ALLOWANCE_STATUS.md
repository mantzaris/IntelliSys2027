# Additional experiment allowance

On 17 October 2026 UTC, the user increased the cumulative additional-experiment
allowance from 7,200 to **28,800 seconds** and authorized execution. The previous
**500.0316 seconds** remain charged. They comprise the 450.0316-second RTX 4090
compatibility attempt and a conservative 50-second cleanup margin. The remaining
allowance at the amendment is **28,299.9684 seconds (7 h 51 min 40 s)**.
These are budgeted wall-time charges, not measured GPU kernel time.

Deployment completed at **17:11 UTC**. All three future controller entrypoints
passed their startup checks on the pod. A separate check verified that their
scientific source and frozen configuration hashes still match the original
records. The original supervisor (PID 3403) and model engine (PID 3930) stayed
running. At 17:13 UTC, Qwen3 had **162/192 distinct completed main base pairs**,
**11,664 completed trajectories**, and **23,576 accepted calls**. Its measured
replacement-pod throughput projected about **2.4 hours** for the remaining main
calls alone, excluding subsequent supporting and live stages. This estimate is
sensitive to the remaining case mix.

See `records/execution/additional-gpu-budget-live-v3.json` for the operational
snapshot. It corrects the preceding snapshot's count of repeated completion
announcements after resume. Those announcements reuse accepted outputs and are
not additional problems or GPU calls. This correction changes no scientific
score, accepted response, budget charge or experiment configuration.

The authorization is preserved in
`records/amendments/additional-gpu-allowance-v2.json`. The ledger remains
`artifacts/runs/objective-confirmation-execution/budget.jsonl`. An amendment event
records the new ceiling without resetting prior attempts. Unresolved attempts
continue to consume their full reservation until an actual elapsed charge is
available. Model loading, execution and cleanup remain inside timed attempts.

The original main evaluations and separately authorized frozen mechanism stages
remain outside this additional-work ledger. Eight hours is therefore not an
estimate of the entire queue's remaining duration.

## Execution

The existing replacement-pod supervisor and Qwen3 engine continue running. The
supervisor already loaded its original command list, so changing a working-tree
configuration alone would not affect the queued controllers. A narrowly scoped
Python startup hook routes only the three future additional-budget entrypoints
to versioned derivatives. It does not intercept the active main runner or its
model requests. Original archived controllers and frozen configurations remain
unchanged.

Each derivative changes the controller's allowance lookup and adds a helper
that verifies the authorization record's checksum. Every other archived file,
including scientific code, prompts, model settings and analysis, is byte-identical
to its original. The routing manifest records original and actual entrypoints
and all derivative file hashes. A source mismatch stops execution before a model
call. Actual substitutions are recorded in
`artifacts/runs/replacement-ada-execution/budget-routes.jsonl`.

The original serial order remains in effect. Original Qwen3 and Phi-4 work and
the previously frozen mechanism stages precede objective confirmation. Objective
confirmation still uses 24 fresh pairs and both models. Numerical preservation
still uses six development pairs and 48 root calls. The final feedback and
identity explorations retain four development pairs, at most 104 calls and their
frozen budget-only fallback. Numerical preservation and adjacent explorations
each retain their individual 900-second limit. No scientific sample or treatment
is enlarged to consume the allowance.

The existing mirror copies accepted outputs locally. Completion hooks analyze
finished stages and update the manuscript. Partial held-out choices are not
inspected to alter the design. Implementation and deployment do not constitute
completion of the scientific study.

## Reproduction and status

From `rep-sensitivity`, rebuild the budget-only archives using the retained
original implementation snapshots:

```bash
.venv/bin/python scripts/freeze_budget_continuation.py
PYTHONPATH=src .venv/bin/python scripts/status.py
```

After copying the resulting archives, adapter and records to the same remote
project, install from that project's virtual environment:

```bash
PYTHONPATH=src .venv/bin/python scripts/install_budget_continuation.py
```

Installation verifies all three queued entrypoints with `--help`, makes no GPU
calls, and does not restart active processes. Its receipt is
`records/execution/additional-gpu-budget-installed-v2.json`. The routing manifest
is `records/execution/additional-gpu-budget-routing-v2.json`. Do not start another
experiment controller alongside the current queue.

All **98 integrity tests passed** after this change. New checks cover preserved
charges across the allowance increase, rejected source or authorization changes,
argument preservation during routing, reinstatement of hardware provenance after
re-execution, and unique base counts after a checkpoint resume.
