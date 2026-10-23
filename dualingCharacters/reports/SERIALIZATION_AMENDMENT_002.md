# Amendment 002: training completion serialization

Recorded hold: 2026-10-23 19:59:26 UTC. Status: repair and pilot validation in progress.

The first trained C1 evaluation was running when a CPU-only format audit found
that JSONL persistence alphabetizes completion fields. The fit loader preserved
that order (`clarify,evidence,plan,state`), while the installed XGrammar 0.1.23
inference grammar enforces `state,plan,evidence,clarify`. Zero of 804 first-round
and 764 second-round labels were accepted in their saved order. All 1,568 were
accepted after reordering exactly the same values. The compact audit, supervision
hashes and grammar root are in `tables/serialization_compatibility_audit.json`.
No model calls or test success metrics were used for this diagnosis.

This is a change to the implementation of the intended learning procedure after
the original freeze, not a pre-test freeze from scratch. Baseline outcomes and
pilot results were already known. The hold and exclusions were decided before
any completed trained locked-test metric was inspected. A first raw evaluation
record was parsed solely to inspect field order. Original freezes, source snapshots,
raw outputs, checkpoints and all costs remain available.

The repair serializes supervision using the public schema's field order and
rejects missing or extra fields. It changes no target values, teacher privileges,
prompts, inference schema, models, seeds, families, token budgets, checkpoint rule,
endpoint, comparison set or statistical estimators. `configs/run_exclusions.json`
explicitly lists affected first C1 fits, its dependent refreshed collection and
evaluation, and historical separate collect/fit v4 pilots. Untrained baselines
and the first C1 collection are unaffected. Earlier in-process engineering
profiles consumed in-memory schema-order teacher targets; they are still only
engineering evidence. Frozen character audits remain behavior observations.

The original C1 round-zero supervision is reused verbatim. Both fits, the
updated-policy round-one collection, and evaluation will receive new run IDs.
Original completed run IDs cannot be replaced without a frozen restart mapping,
an explicit exclusion, and an amendment reference. Resource accounting includes
both original and replacement attempts. Exclusions affect scientific tables,
not integrity audits, historical records or total spending.

Before release: regression tests, CPU grammar checks on saved examples, and
corrected GPU learning pilots for Qwen C3/C5 and Phi C5 using the original pilot
collections and fixed held-out pilot families. Pilot success requires interface
compatibility and actual parameter updates, not better task scores. The core
queue remains held until those checks and the amended source freeze are recorded.
The original scientific sample and hypotheses remain fixed. Human scientific
review and human ratings remain pending.

The corrected first Qwen C3 pilot produced one token-capped whitespace loop in
1,024 turns. It is retained as an ordinary scored failure with the unchanged
256-token cap; no retry, example removal or decoder change is made. A draft gate
requiring zero incomplete outputs was too strict for a bounded-generation policy:
the actual interface check accepts complete schema objects or records capped
incomplete failures, while all supervision must be accepted by the full grammar.
This engineering gate clarification does not alter any scientific endpoint.

Fresh untrained pilot references will use the same current source and held-out
pilot families: the older v4 baseline's environment/evaluation source differs,
so it cannot supply a matched before/after comparison for this repaired pilot.
No additional training samples or hyperparameter trials are introduced.

The original statistical plan prohibited replacing completed runs through the
resume mechanism. This amendment makes a narrow, explicit exception for the
four identified scientifically invalid C1 stages using a separately frozen
restart mapping; ordinary completed-run retries remain prohibited. This is a
reviewable change to implementation and eligibility handling, while the numerical
estimators and scientific design remain unchanged. It must not be described as
an entirely unchanged analysis protocol.

The original precision simulation used discordance 0.3125 from the historical
pilot now excluded for serialization mismatch. Retain that simulation as an
assumption-based sensitivity analysis, not a validated estimate of the repaired
method's discordance or power. The already frozen sample size and seeds stay
fixed; repaired pilot scores do not select the study size or checkpoints.

Reproducibility means pinned code, weights, data, seeds and deterministic scoring;
GPU kernels are not forced into bitwise deterministic operation. Checkpoint and
trace hashes identify the actual execution, and small numerical differences may
remain on another hardware/software stack.
