# Protocol and execution record

Initial scope fixed on 2026-10-16 UTC, before pilot outcomes were inspected.
This is an executable research protocol, not a completed study or a claim of novelty.
The user supplied the research questions and intended design. Scientific review by
the human author is pending.

## Questions and boundaries

The primary task selects the minimum-makespan feasible **supplied candidate**.
It does not solve globally optimal scheduling. Feasibility is a conjunction;
ties follow a public randomized priority ordering, and NONE means every candidate
is infeasible. Half-open integer intervals are non-preemptive. An independent
time-slot checker cross-checks the event-sweep implementation.

The main candidate contribution is preservation of complementary mandatory
constraints and consequential scope distinctions through summary-only interfaces.
Evidence double counting, ancestry, paraphrase sensitivity, and hierarchies are
established topics. In particular, *Copies or Sources?* already studies summaries
and hierarchical logs; its aggregator sees the full log, while our primary root
receives summaries and a value-free scope registry.

The primary scheduling population uses numerical, identity and dependency edits.
A **separate secondary workflow population** uses quantifier, condition and version
edits. Six-family totals must never be described as six scheduling mutations.
Development/validation/held-out targets are 24/36/192 independent pairs, balanced
within family between changing and preserving interventions. Half are scheduling.
The main 192-pair target therefore means 96 primary scheduling clusters. If reduced
to 96 total pairs before evaluation, only 48 primary scheduling clusters remain.
The limited structural diversity is a threat to generalization, not a claim of
representative real-world coverage. Evaluation reserves fork-join tails, different
parameter combinations, and different rendering templates. Seeds alone are not
the split rationale.

## Distinct quantities and access

Assignment overlap concerns verification scopes, not text. Textual similarity is
a surface property; claim equivalence requires matching predicate, candidate,
entity, condition, version and value. Complementary claims differ in required
scope. Contradictions differ in value within a compatible scope. Applicability
and explicit revision rules determine whether two apparent contradictions can
both be correct. New timestamps have no implicit authority.

Task dependencies, job precedence, organization, actual message access, and
evidence/report ancestry have separate representations. Replay workers are
deterministic verification operations, with zero model worker calls; copies add
neither a verification execution nor an evidence source. Live model executions
will receive distinct execution identifiers but shared world-source identifiers.
Fresh calls do not imply independent evidence or independent errors.

Models receive no mutation labels, oracle decisions, or evaluator correctness
flags. The public registry maps versioned scope keys to orchestration-known scope
fields and units, without assertion values. Both ordinary and proposed policies
receive this same registry. This structured interface assists the baseline and
limits conclusions to this interface. A deterministic consolidation reference is
not an empirical model result or a proposed-method accuracy measurement.

## Frozen replay

Reports are generated from typed assertions and static templates before inference.
Templates are code-reviewed and integrity-tested; human linguistic review remains
pending. No model-generated paraphrases are used. The three conditions are one
presentation, four exact presentations, and one original plus three templated
paraphrases. Every required report is retained. Template form does not encode the
answer. Candidate names, candidate order, report order and tie priority are seeded
independently of the answer. Within one input, similar reports describe different
resources and candidates, with distinct mandatory findings.

The repeated report is chosen by a prespecified candidate/task rotation, preferring
unchanged scope and value across worlds. Version changes can prevent that; the
corpus records the selected scope and supports auditing the exception. Branch
partitions are frozen by pair seed; copies initially stay with their original.
Flat uses one call. Hierarchical uses two partition managers and one root. The
root receives the managers' outputs and scope registry, not the original reports.

Ordinary synthesis and coverage checklist form the pilot. Scope-aware instructions
join validation and the main study. Decision semantics are identical. Every policy
emits choice, class probabilities, explicit scoped assertions and unresolved keys.
Assertions cite delivered report identifiers. These are emitted statements, not
measurements of hidden reasoning. Missing findings count against retention.
Malformed completed outputs are accepted once and scored as operational failures;
they are never sampled repeatedly until valid. A malformed intermediate response
makes its trajectory an operational failure even if the root happens to answer
correctly; root-only correctness is retained separately.

## Inference and integrity

Only the existing RTX 6000 Ada allocation is authorized. Public Qwen2.5-7B-Instruct
and Mistral-7B-Instruct-v0.3 model cards were inspected; both use Apache-2.0 licenses.
These are reproducible, modest-size models, not representatives of frontier systems.
Model repository commits and tokenizer/chat-template hashes are recorded. vLLM
0.10.2 runs BF16, without quantization, using the native tokenizer template. Initial
settings: temperature 0.3, top-p 0.95, 1,536 output tokens, 12,288 context tokens,
batch size 32; no hidden reasoning channel or guided JSON decoding. All settings
are fixed within a comparison. Output and context caps are checked using actual
token lengths. No truncation of model input is allowed.

Offline engine errors stop execution. There is no transport retry in this adapter.
Accepted response files are immutable compressed JSON; events append with fsync.
Cache keys include model settings, request, trial, stage and stochastic repetition.
Resume reuses accepted malformed outputs. Started-but-unaccepted requests are
visible in the event log; a crash can require rerunning such unaccepted computation.
Completed base clusters are checkpointed. Raw outputs remain outside Git, with a
local mirror; compact manifests and analysis outputs are versioned in Git.

## Statistical commitments

`configs/analysis.json` defines H1-H4, signs, denominators, model averaging and
bootstrap settings. Repetition harm is repeated-error minus single-error;
hierarchy interaction is that harm under hierarchy minus that harm under flat.
Use complete base clusters and stratified cluster bootstrap, preserving both worlds,
all arms, both intended repetitions and model dependence. Report models separately;
pooled model estimates weight models equally. Workflow results remain secondary.
No confirmatory p-values are planned in the initial implementation. If introduced,
Holm correction covers the six registered tests. Wide intervals are inconclusive.

Competence gate: at least 85% exact accuracy on flat/single/ordinary development
trials, including operational failures. Validation determines whether caps, task
competence, precision, and runtime permit the main study. Sample-size reduction to
96 total pairs or removal of exploratory controls must occur before any held-out
model outcomes. No significance-based stopping. Measured batch runtime and actual
token lengths, not assumed throughput, determine GPU-hour projections.

## Pending extensions and acceptance gates

Supporting controls must preserve distinct information, report slots and ordering
where relevant, report actual token-length differences, and independently test
summary bypass, call-count-matched global reviewers, neutral padding, ancestry
withholding/corruption, instruction-only changes, and deduplication. A lineage
shuffle must change actual parent/source relationships. False favorable reports
and false objections require authoritative visible task data or an allowed
INSUFFICIENT response. An unsupported truth-recovery demand is invalid.

Live evaluation follows replay validation, on new base instances. Four essential
worker scopes remain in fixed-allowance comparisons. Added duplicates have fresh
execution IDs, not new source IDs. Actual input/output tokens and elapsed resource
use are reported; equal output caps are not equal compute. Any displaced essential
scope must be labeled coverage displacement. Shared-state action races and
destructive concurrent effects are outside scope.

The full workflow is incomplete until held-out inference, supporting controls,
live evaluation, analysis regeneration, manuscript compilation and human scientific
review are complete. No submission or claim of human review is authorized.

## Current development interface (v7)

See `DECISIONS.md` for preserved v1–v4 failures and revisions. The current common
contract uses descriptive scope identifiers, schema-guided JSON, and a short
model-generated feasibility/objective assessment before final selection. This
scaffolds ordinary synthesis too, narrowing its difference from the checklist.
Qwen3 uses its native non-thinking template. The v7 pilot gives every root the
same value-free orchestration ancestry registry; raw texts and assertion values
still cross the boundary only in managers’ summaries. Benchmark v2 fixes harmless
numeric controls to the matched capacity 1↔2 change. Run manifests, rather than
the historical initial settings above, specify the actual engine and caps.

Predicate criteria are separate from report applicability in v7. The final adapter
uses native token IDs and records a fixed template date. Historical Mistral checks
with extra BOS tokens are interface diagnostics; exact settings and corrections
are in `DECISIONS.md` and `records/models/*-tokenizer-audit.json`.
