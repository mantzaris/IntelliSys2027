# Draft analysis plan — NOT frozen and no test outcomes opened

Primary estimand: the C5 minus C3 absolute difference in antagonist-free paired task
success, averaging independent training seeds and common scenario families. A family
succeeds only if both its authorized-change and hypothetical-change worlds have the
correct final executable decisions and required clarifications. Recall is separate.

Default training seeds: 17, 29, 43. Three seeds are a weak basis for estimating the
distribution of training variability; report each seed and avoid claims of stable
tail behavior. The pretrained base is deterministic under greedy inference and
should not be counted three times as independent training runs.

The draft test manifest contains 240 families (480 conversations), balanced over
four domain labels; substantive domain transfer remains a pilot design gate.
Primary horizon: 64 user/assistant pairs. Preselect families by hash for 32/128-turn,
full-history, unfamiliar-corruption and fixed-fault recovery subsets before any
test outcomes. Manifest and generation hashes, endpoint, count, seeds, training
budget, checkpoint rule, exclusions and analysis code must be frozen together.

Use a paired two-way family/seed bootstrap, resampling both seed and family axes
and preserving all methods and both worlds within each sampled cell. Report
absolute differences and percentile 95% intervals, plus per-seed differences.
Turns and paraphrases are not independent subjects. Assess sensitivity to seed
pairing and a family-only interval conditional on these seeds. A degenerate
bootstrap in tiny engineering pilots is not a precision claim.

Prespecified secondary comparison family: C5–C1, C5–C2, C5–C4, C5–C6,
C5–A1, C5–A2, C5–A3. Report all and adjust inferential p-values with Holm's
procedure if a valid paired test is implemented. The primary contrast is separate.
Replicate the central comparison independently in Phi with C1/C3/C5 and the same
three training seeds. No weights transfer between architectures.

Secondary measurements: per-world success; authorized-update acceptance;
hypothetical-change acceptance; memory recall versus plan adherence; dependency
errors; source-reference accuracy; malformed output; clarification/refusal;
tokens, latency and retrieval volume. Error recovery uses identical prespecified
faulty memory snapshots and reports cumulative repair probability at each budget,
including all never-repaired cases. Do not compare latency only among successes.

Power/precision: simulate a five-percentage-point paired improvement under pilot-
estimated baseline/discordance and several plausible seed variances. This is a
design sensitivity analysis, not an assumed effect or a promise of power. Use
the measured throughput to allocate the <=96 GPU-hour ceiling before freezing.
Reduce optional scope first, retaining C1/C3/C4/C5, three seeds, A1 and independent
family replication. If even this is infeasible, disclose the exact shortfall.

Checkpoint selection: predeclare a validation-only rule or a common final-token
checkpoint. No significance-based extension, early stopping, endpoint changes or
checkpoint choice. Infrastructure failures retain logs and budget usage; reruns
use the same data/seed/config and fresh IDs with an explicit supersedes field.
Malformed answers are failures, not exclusions. Corrupt inputs require a
condition-blind exclusion decision and a logged reason.

Freeze mechanism: `configs/freeze.json` must contain verified file SHA256 values
and `pilot_gates_passed=true`. The CLI refuses locked-test evaluation otherwise.
This draft alone is not preregistration and no public registration is claimed.
