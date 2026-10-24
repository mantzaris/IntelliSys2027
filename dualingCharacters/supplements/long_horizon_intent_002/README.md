# Long-horizon intent robustness: exploratory follow-up 002

This continuation is separate from the original core experiment and review_001.
The single session runs **2026-10-24 13:06:05–21:06:05 UTC** (09:06:05–17:06:05
America/New_York), with the last30 minutes reserved for verification/handoff.
It does not authorize a new worker after that deadline. Core/review work may
continue under its existing authorization, ownership, freezes, and96-hour ceiling.

Read [PROTOCOL.md](PROTOCOL.md), [DATASET_CARD.md](DATASET_CARD.md),
[RUBRIC.md](RUBRIC.md), [progress](reports/PROGRESS_REPORT.md), and
[claim boundaries](reports/CLAIM_TO_EVIDENCE.md). Fresh qualitative performance
is pending unless `reports/INTENT_SCORES.json` explicitly contains a complete,
actually rated grid. CPU fake-backend tests and tokenizer audits are not model results.

## Existing owners and safe monitoring

The original core controller owns `artifacts/campaign.lock` and advances its
unchanged queue. The existing review coordinator waits for the entire required core,
not one condition or seed. No intent waiter is installed. Its optional priority guard
holds older unseen-profile work behind this extension without scheduling intent calls.
See [OPERATIONAL_INTEGRATION.md](OPERATIONAL_INTEGRATION.md).

From the `dualingCharacters` directory:

```bash
PYTHONPATH=src .venv/bin/python -m supplements.long_horizon_intent_002.operations monitor
PYTHONPATH=src .venv/bin/python -m supplements.long_horizon_intent_002.operations update
PYTHONPATH=src .venv/bin/python -m supplements.long_horizon_intent_002.operations mirror
```

Monitoring/mirror checks use the already configured authorized SSH connection;
no credentials are printed. `update` is local CPU work and validates only completed,
eligible immutable stages. Cache reuse avoids replaying unchanged exposure audits.
Never retry a stage solely because of its score. Classify infrastructure faults,
prove the old worker exited, and use the original audited resume mechanism; preserve
partial outputs, costs, and lineage. This extension has **no automatic GPU retries**.

## Rebuild the new CPU package

Use the existing local analysis environment, with pinned additions in
`requirements-cpu.txt`. No local model weights or CUDA are required for these commands.
The dataset contains authored facts and private evaluator ledgers; generated bulk
files stay in ignored local artifacts and are reproduced from committed sources.

```bash
PYTHONPATH=src .venv/bin/python -m supplements.long_horizon_intent_002.benchmark
PYTHONPATH=src .venv/bin/python -m supplements.long_horizon_intent_002.overlap
PYTHONPATH=src .venv/bin/python -m supplements.long_horizon_intent_002.token_audit
PYTHONPATH=src .venv/bin/python -m supplements.long_horizon_intent_002.regenerate
PYTHONPATH=src .venv/bin/python -m unittest supplements.long_horizon_intent_002.test_intent -q
PYTHONPATH=src .venv/bin/python -m supplements.review_001.freeze verify
PYTHONPATH=src .venv/bin/python -m supplements.long_horizon_intent_002.freeze verify
```

The last command applies after `FREEZE.json` has been created. Rebuilding must
reproduce its exact dataset/science hashes; do not edit a frozen file to suppress
a mismatch. The generated reports and figures can update with new completed runs.
A scientifically necessary correction requires an explicit documented amendment.

Tables and all PDF/SVG/PNG figures regenerate with the single `regenerate` command.
It uses cached verified raw artifacts and reports missing inputs as pending.
The separate paper section is [MANUSCRIPT_SECTION.md](MANUSCRIPT_SECTION.md);
`draft.py` builds its anonymous template-based PDF if the existing LaTeX toolchain
is available. It is a review draft, not a finished or policy-compliant submission.

## GPU dispatch: disabled until every gate passes

The new two-hour cumulative subcap is inside the original96hours, with at least
30minutes overall contingency. Engineering, loads, profiling, failed attempts,
cleanup, and inference all count. Human-only scoring is allocated; no model judge
or new training is authorized here. Required core → review_001 → intent_002 →
older optional unseen profiles. The extension deadline is independent of GPU budget.

Check without launching:

```bash
PYTHONPATH=src .venv/bin/python -m supplements.long_horizon_intent_002.budget
PYTHONPATH=src .venv/bin/python -m supplements.long_horizon_intent_002.freeze checkpoint_readiness
```

The only execution entry point is the foreground coordinator:

```bash
PYTHONPATH=src .venv/bin/python -m supplements.long_horizon_intent_002.controller run
```

It immediately returns pending if disabled or prerequisites are missing; it creates
no background waiter. An explicit `artifacts/long_horizon_intent_002/activation.json`
with boolean `enabled: true` and this exact session ID is additionally required.
Do not enable it after the recorded session deadline. A subsequent user-authorized
continuation must document a new operational session and any required protocol
amendment; elapsed time does not grant permission or reset either GPU subcap.

When admitted, the coordinator holds the existing campaign lock, checks the entire
core and review completion gates again, binds the named final adapters, uploads only
new supplementary sources/public scripts, and runs fixed engineering and profiling.
Timing alone selects a complete balanced tier before scientific outputs. The remote
worker uses the existing GPU lock and resource ledger. A separate deadline supervisor
owns only its newly launched process group; it cannot target the core controller,
review coordinator, unrelated jobs, or pod. Per-batch and absolute deadline guards
retain partial artifacts as incomplete. No failed or partial grid is reported complete.

Current fixed scientific inputs: Qwen revision
`cdbee75f17c01a7cc42f958dc650907174af0554`; C1/C3/C5 final adapters at seeds17/29/43.
The fixed C1 seed17 corrected-run alias is resolved by the original campaign map.
Missing final checkpoints are pending, never replaced with another seed/checkpoint.
The CPU suite tests boundaries and accounting; GPU execution/interface validation
remains untested until admitted engineering calls actually run.

## Human review and provenance

`human_review.py` prepares a **new**, separately blinded packet only from complete
actual intent trajectories with matching adapters, allocation, and scientific hashes.
It preserves existing item IDs and any supplied annotations. The balanced sample
has144 outputs per admitted seed; it is not the complete primary scoring grid.
For16 families, full scoring requires1,728 outputs per seed, each rated by two humans;
smaller tiers reduce that workload proportionally. All forms start blank. Do not
substitute model judgments or another condition's outputs for missing ratings.

The original60-action packet and the planned120-prose packet remain distinct.
`legacy_packets.py` audits their identities without editing or contacting anyone.
No human annotations have been invented. Scientific interpretations and any eventual
conference submission require the human author's review and authorship responsibility.

Compact reports/manifests/code/figures are committed locally on main. Raw model
traces, dataset expansions, adapters and CPU caches remain under ignored `artifacts/`;
original GPU outputs continue to mirror locally. Nothing is pushed, published or
submitted. See `reports/PROVENANCE.json` and the per-analysis manifests for exact
source hashes, selected runs, parameters, and deterministic reproduction steps.
