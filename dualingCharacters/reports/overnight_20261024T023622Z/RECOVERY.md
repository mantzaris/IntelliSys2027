# Operational recovery boundaries

No infrastructure retry has been performed at overnight start. The existing core
controller owns `artifacts/campaign.lock`; GPU stages own `artifacts/gpu.lock`.
The reviewer coordinator owns `artifacts/review_001/controller.lock` and remains
CPU-only waiting for all core stages. The overnight analysis creates no controller.

Before any retry:

1. Inspect `artifacts/campaign_state.json`, the named stage's status, its controller
   log, and the pod's process/GPU list. Compare counters and timestamps with prior
   snapshots and measured stage durations. A long model load is not a hang.
2. Prove that the old controller and old GPU operation are no longer running.
   A dropped SSH connection alone is insufficient. Never start a duplicate worker.
3. Pull and preserve partial outputs and resource records. If the stage actually
   completed remotely, restore its complete mirror and restart only the controller;
   its completed-stage check skips that evaluation. Never rerun completed tests.
4. For an actual failed stage, record the infrastructure cause and a new alias in
   the existing `artifacts/campaign_resume.json` mechanism. Training may use the
   last valid atomic optimizer checkpoint; partial evaluation or collection restarts
   use a fresh run ID and the same full fixed settings, retaining old partial data.
   Only the complete eligible attempt enters estimates; all attempts consume budget.
5. At most two automated retries for the same infrastructure failure. Record each
   attempt and its original run, alias, cause, checkpoint, worker-idle evidence,
   reserved cost and subsequent outcome in the ignored overnight recovery manifest.
6. Verify both freezes and sufficient original resource balance, then use the
   existing controller command, with its usual SSH environment, only if no owner
   remains: `PYTHONPATH=src .venv/bin/python -u -m pcc.campaign`.

A demonstrated scientific correctness defect requires an evidence-backed
`artifacts/campaign_boundary_hold.json` with a reason; allow the active stage to
finish. Preserve originals, identify affected runs, and continue independent CPU
work. Do not alter frozen scientific code, eligibility, samples or allocation while
the author is asleep. A healthy queue is not stopped merely to end this overnight
session. A budget forecast is not authorization to drop cells or buy resources.
