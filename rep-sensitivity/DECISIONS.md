# Decisions and deviations

## 2026-10-16: initial environment and model choices

Reused the provided pod. Verified RTX 6000 Ada Generation (49,140 MiB), driver
595.91.07, existing PyTorch 2.8.0+cu128, and no unrelated GPU processes. Installed
vLLM 0.10.2 in a project-local environment. Its unbounded dependency resolver first
selected Transformers 5.20.0; pinned compatible Transformers 4.55.4 and Hub 0.34.4
before any model calls. Public weight downloads needed the inherited hf-transfer
flag disabled. No new infrastructure or paid APIs were used.

## 2026-10-16: stop development pilot v1 for interface failure

The first inspected complete cluster had Markdown-fenced replies rejected by the
strict JSON contract. The run was stopped for interface validation, not for a
favorable research effect. Local immutable records contain 192 complete trajectories
plus accepted calls from an incomplete next cluster. The initial interface also
elicited wrong assertion types and repeated-output truncation. A diagnostic that
only removes a surrounding JSON code fence does not establish adequate task
competence. Do not interpret these operational failures as evidence of duplication
harm, summary amplification, or robustness. Original failures remain primary v1
failures; they are never silently replaced or re-sampled.

## 2026-10-16: interface v2 competence check

Before any held-out evaluation, replace triple-array output instructions with
named assertion fields, an explicit type example, and a common schema-constrained
JSON decoder for every policy. The schema contains no answers, claim values, scope
truth or permitted correct candidates. The output cap increases to 2,048 for this
development check. This constrains formatting in the baseline and must be disclosed.
Only flat, single-presentation, ordinary synthesis is evaluated initially: 24 pairs,
two worlds and two repetitions (96 calls). Scope instructions are not selected on
held-out outcomes. A larger public model is a possible competence fallback, not an
attempt to maximize repetition failures. The original 85% competence gate remains.

Qwen2.5-14B-Instruct's official card was inspected as a possible fallback; its
Apache-2.0 license and native Qwen chat template are suitable for sequential BF16
inference on the allocated GPU. Mistral downloads initially returned expired
download-credential errors; unauthenticated public-model access will be retried
without requesting or exposing private tokens.

## 2026-10-16: explicit objective semantics and assertion-first output (v3)

Development errors include selecting a feasible candidate with a worse objective,
not just accepting invalid schedules. The v2 header specified minimum makespan but
did not explicitly map the reports' generic `objective` label to makespan/cost.
Clarify this mapping, state that priority applies only after numerical minimization,
and place explicit supporting assertions before the choice in the common schema.
This is a baseline-fairness and interface development change, applied to every
policy. It is not a held-out intervention or evidence for H1-H4. Preserve all v1/v2
outputs and evaluate a separate v3 competence manifest on the development split.

## 2026-10-16: descriptive scope identifiers (v4)

Several development traces reproduce every assertion correctly but select an
infeasible candidate. Before attributing any behavior to duplication, test whether
opaque identifiers add avoidable binding difficulty. Replace hashed scope keys
with candidate/predicate/entity/version identifiers and a condition hash. Every
policy gets the same identifiers; they reveal scope, never truth or the answer.
Archived claims retain their original identifier convention. This development
revision does not establish a causal explanation of earlier errors. Qwen3-14B is
tested in its officially supported non-thinking mode, with that setting recorded.

Mistral's official v3 SentencePiece file is provided under the filename expected
by the pinned Transformers loader through a derived tokenizer directory. The bytes
and vocabulary are unchanged; the alias and file checksums are recorded. This
resolves a tokenizer initialization error, not an accepted inference failure.

## 2026-10-16: candidate assessment fields (v5) and matched capacity controls

Descriptive identifiers alone did not meet the competence criterion in the
development check. Add a short public assessment per candidate (conjunctive
feasibility and objective) before the final choice. These are model outputs,
not evaluator-computed answers or private reasoning. Every policy has this same
contract; it gives ordinary synthesis a stronger scaffold and narrows its
difference from the checklist policy. Evaluate this change on development only.
The threshold and all unsuccessful measurements are preserved. New competence
runs retain benchmark v1 for interface comparison.

Benchmark v2, separately versioned for subsequent experiments, changes harmless
numeric cases to the same capacity 1↔2 edit as consequential cases, with sequential
resource demand that never exceeds one. Historical v1 worlds are unchanged. Both
versions are checked independently against the reference verifier. No held-out
model outcome informed this correction.

## 2026-10-16: role-specific schema enforcement (v6)

The first full v5 pilot cluster exposed managers filling final assessment/choice
fields despite instructions to leave them empty. All initial hierarchical
trajectories were therefore operational failures under the declared strict parser.
Stop this development run and retain the failures. Constrain intermediate choice
to null and intermediate assessments/probabilities to empty collections in the
common decoder; clarify the manager role before giving the root decision rule.
This enforces an already-declared interface and gives no policy privileged values.
Root prompts and schemas are unchanged from the successful v5 competence check.
The v6 pilot uses a new immutable run; v5 results are not repaired or replaced.

Mistral-Nemo-12B (official Apache-2.0 model card, pinned revision and verified
weights) is the larger second-family fallback. Its initial benchmark-v1 scheduling
check missed the unchanged gate. A separately labeled check will use the final
benchmark v2 and execution settings, as Qwen3's pilot does. These development
checks reuse base structures and are not independent confirmations. No held-out
outcomes have been evaluated.

## 2026-10-16: separate checked criterion from applicability (v7)

A schema audit found that resource limits and workflow expressions had been put
in `applicability_condition`. That could imply a failed check is inapplicable,
although its result remains mandatory. Store these expressions separately in
`predicate_parameters`; a report's applicability remains `always` unless the task
defines a true applicability restriction. Render the checked criterion explicitly.
This is a semantic correction, not a claim that it caused earlier model errors.
Preserve old scope keys and old corpora for historical analysis. Cancel the queued
v6 full pilot before it starts; completed development checks remain unsuccessful
or successful under their original interfaces. Validate v7 competence and summary
contracts on development before allocating the full pilot. No held-out outcomes
have been inspected, and the 85% criterion is unchanged.

## 2026-10-16: larger second-family fallback

Nemo did not meet the primary scheduling competence threshold under the corrected
interface. Select Mistral-Small-24B-Instruct-2501 in Red Hat AI's published W8A8
checkpoint as a larger fallback that fits the existing GPU. Inspect both the
[official base card](https://huggingface.co/mistralai/Mistral-Small-24B-Instruct-2501)
and the [quantizer's card](https://huggingface.co/RedHatAI/Mistral-Small-24B-Instruct-2501-quantized.w8a8).
The actual pinned config identifies MistralForCausalLM and INT8 linear weights
(per-channel) and dynamic per-token INT8 activations. The quantizer's card has
inconsistent architecture/evaluation boilerplate; do not rely on its benchmark
claims. Record the downloaded quantized revision, rather than inventing a revision
for its unrecorded pre-quantization source. No calibration uses our benchmark.
The official base card recommends low temperature: fix 0.15 for this model before
its first outcome, with 0.3 retained for Qwen3. Report model-specific settings and
results. Completed smaller-model caches are reproducible and evicted to free space;
all outputs, manifests and checksums remain locally mirrored.

## 2026-10-16: native token-ID adapter and frozen template date

Before Mistral-Small inference, compare Hugging Face and official Mistral-common
encodings with identical system/user messages: token IDs agree. Its native template
also inserts a default system message and current date; freeze that date at
2026-10-16 and record the complete template/default system text. Sending the
formatted string through a second tokenizer can add another BOS token. The audit
of all 96 archived Nemo-v7 calls confirms one extra token; do not interpret those
checks as clean comparisons of model competence. They remain original outcomes.
All 96 Qwen3-v7 token counts match native encoding, so its running pilot is retained.
The updated adapter submits explicit native token IDs, verifies the engine did not
change them, and records their hash plus the formatted-prompt hash. Earlier Mistral
checks belong in the development/interface record, not the final model ranking.

New queued work runs from immutable source snapshots so local edits cannot change
the implementation between stages of a long-lived process. The existing Qwen run's
remote source has remained unchanged since its v7 launch.

## 2026-10-16: analysis audit and supporting-control completeness

The branch-placement contrast now distinguishes placement of two similar reports
with different scopes from placement of exact copies. Both preserve the full
report set; the distinct-scope contrast records changes in branch load. Scope
selection uses identifiers and task fields, never the correct decision. The
supporting harness remains unexecuted on held-out data.

Claim scoring version 2 treats an integer and the equal integral float as the same
numeric finding, while Boolean truth remains distinct from 0/1. It adds a visible
incompatible-scope citation metric: an assertion cites at least two known reports,
their scopes differ, and at least one citation does not bind the asserted scope.
This measures emitted attribution, not a hidden merge operation. Offline analysis
recomputes claim scores from immutable responses, recording the scorer hash;
original scores and final-choice outcomes are preserved. Precision projections now
use separate stratum variances and target group sizes, especially for H2's two
change classes. A collapsed empirical interval is never presented as proof of
robustness or adequate prospective precision.

The deterministic development-corpus audit shows balanced repeated task families
in scheduling and both feasible and infeasible fastest candidates. The 24-pair
development prefix includes ties but no NONE worlds; NONE is present in the
36-pair validation prefix. Do not generalize the development competence gate to
that untested stratum. Preserve the frozen pilot and evaluate that limitation in
validation. All corpus-audit counts are in `records/benchmark/development-v2.json`.

Supporting corruption contrasts include all three policies under the same visible
authoritative world, so H4's false-objection guardrail can actually be evaluated.
The provisional practical error-increase margin is five percentage points; it is
an interpretation threshold requiring scientific review, not a sample-size or
significance target. A wide or degenerate small-sample interval cannot establish
acceptable loss. Main harmless-pair and supporting false-objection comparisons
are reported even if scope-aware prompting improves another metric.

## 2026-10-16: prospective resource allocation and unattended execution

Before any validation or held-out model outcome, fix `configs/allocation-rule-v1.json`.
Keep the requested 192-pair target unless measured validation extrapolates to more
than 48 inference hours for the main replay on this GPU; use 96 if it does. This
two-day planning heuristic is an implementation choice, not a user billing cap,
and does not stop a frozen run early. Export precision estimates at both sizes and
report any precision limitation. The primary scheduling population is half of
these totals. Main execution requires completed validation and adequate ordinary
primary-task performance for both families. Secondary workflow performance is
reported separately, including limitations.

The targeted held-out subset has 12 prespecified pairs: one consequential and one
preserving case per family, with regular, tied and NONE preserving structures.
Use one stochastic repetition for these exploratory controls, retaining both
worlds. Bootstrap these small supporting populations by change class, pooling
families within each task population; family-specific inference is unsupported.
The main bootstrap remains stratified by family and change class. Live evaluation
retains two repetitions and twelve new scheduling bases. Omit optional dose response.

The sequential controller uses immutable code/configuration snapshots, checks
qualification before validation, and freezes main, supporting and live protocols
before the first held-out call. Model calls use only this pod. Completed calls and
failures are never resampled for a better answer. Offline engine errors stop the
controller with an explicit failure record. A failing gate is not silently relaxed.

Live fixed-budget accounting now includes the root. Workers retain the baseline
worker allowance; after their outputs are available, the root's output allowance
is bounded by the remaining corresponding baseline trajectory allowance, including
its input. A root that cannot fit is recorded as resource displacement without a
fabricated model call or shortened input. Exact end-to-end accuracy and input-supported
root success are separate: a lucky truth match on unresolved worker claims is not
evidence of successful root integration. Worker access excludes jobs irrelevant to
a single-resource assignment. Report ancestry comes from logged orchestration
access; unsupported worker source citations are separately counted.

Checkpoint publication is atomic and fsynced. Request hashes include per-call
output allowances. Coarse GPU telemetry is integrated only over accepted batch
windows, with sampling coverage reported; it is not a kernel-time measurement.

## 2026-10-16: completed pilot and second-family qualification failure

The complete Qwen3 v7 pilot is analyzed in `results/pilot-v7/analysis.json` and
audited in `records/audits/pilot-v7.json`. Its scheduling repetition estimates are
beneficial, with ceiling flat accuracy; workflow effects are mixed. These are
development results, not held-out confirmation. Preserve and report them without
selecting a model or modifying held-out cases to reverse their direction.

Mistral Small 24B INT8 failed the unchanged development competence gate with native
chat-template token IDs (`records/gates/competence-mistral24-v7.json`). The queued
controller stopped before validation; failure records remain in the mirrored raw
artifact package. No held-out inference has occurred.

Select Microsoft Phi-4 as the next competence candidate before seeing its outcomes,
because it is a distinct family with a reasoning-oriented text model, a supported
Phi3ForCausalLM architecture, a native chat template, MIT license, and BF16 weights
that fit this GPU. Directly inspected the official card and pinned configuration:
https://huggingface.co/microsoft/phi-4/tree/2db69c1c3e91a05d2c64a3185acfbaf36f744e25 .
Use the existing common temperature 0.3, top-p 0.95 and output/context limits.
Do not alter task data, prompt interface, correctness rules, or the 85% gate.
Evict only the reproducible failed Mistral24 cache after retaining its checksums,
metadata and results. Phi-4 qualification uses immutable implementation snapshot
`cff4b3a0b1a2b0f42a8a0ff63afa7d9eebbf6deb65c6b8b18ff5851713349c7e`.

Phi-4 passed both development populations and the summary contract check, as recorded
in `records/gates/`. Validation was frozen at the timestamp in
`records/freezes/validation-v7.json` for Qwen3 and Phi-4. The sequential controller
now uses immutable snapshot `77e005c5428fb32bb54df2166d0d2341076ca56422f1b5fad7e3a84957ec3122`.
No held-out outcomes were used in this model substitution. Additional exploratory
analysis reports the high-minus-low overlap effect for decisive clauses minus the
same effect for harmless clauses, pairing all four cells within base/world/repetition.
The original primary contrasts are unchanged. Supporting optional metrics retain
explicit observed-cell denominators; unavailable metrics are not imputed.
