# Mechanism amendment v1 — 16 October 2026

The revised question is: **When does repetition protect information from loss in
hierarchical agent systems, and when does it cause those systems to overlook
contradictions, scope differences, exceptions, or updates?** The proposed tension
between shared-information retention and sensitivity to meaningful differences
remains a hypothesis. Benefits, harms, negligible effects and mixtures are all
admissible outcomes.

The immutable introduction record is `records/amendments/mechanism-v1.json`, dated
15:00:47 UTC. Original main-v7 was frozen at 12:58:49 UTC and had started inference.
Its hypotheses, configuration, implementation snapshots and accepted outputs stay
unchanged. Its model outcomes were not inspected to select these new contrasts.
New mechanism analyses of the old pilot, validation or main are exploratory. New
confirmatory claims require fresh held-out identifiers and their own freeze.

## Development experiment

Use the same 24 development base pairs, Qwen3-14B, both worlds, one stochastic
repetition. This is a targeted design, not a Cartesian product. The initial plan
contains 514 trajectories and 1,446 logical decision-graph calls. Identical manager
requests explicitly shared within base/world/stage/repetition reduce this to
1,116 physical calls. Shared raw outputs are referenced by hash. Separate
stochastic repetitions and roots do not collapse into one cache entry.

The target classes are selected from executable truth before model evaluation;
these labels and oracle values never enter the model prompt:

| Class | Definition | Presentations |
|---|---|---|
| A | Correct mandatory Boolean finding whose isolated flip changes the complete-information choice; prefer a failed constraint | 4 |
| B | Correct Boolean finding whose isolated flip does not change that choice | 4 |
| C | True lowest objective for an infeasible candidate, else a true mandatory result for an infeasible candidate | 4 |
| D | False Boolean finding with original true report and authoritative task data visible; correct-data and single-false controls | 1 or 4 false |
| E | Every required report equally | 4 each |
| F | Complete original report set | 1 each |

The common-finding target is C when available, otherwise B. It is not labeled
irrelevant: the claim can matter locally without entailing whole-candidate
feasibility. Eligibility and omissions are recorded independently of model output.
The development plan has 34 ineligible C world-cells; it never removes a required
report to create an intervention. Target relevance is evaluated per world, so a
pair can have different selected scopes. Paired correctness is still measured on
both worlds; it does not isolate an unchanged repeated scope in every pair.

Six prespecified development indices, `[0,7,2,9,4,11]`, span the six mutation
families and both change statuses. They support flat, summary-only hierarchy,
summary plus raw-report bypass, lossless transport, and two global reviewers plus
root. Bypass reuses exactly the same summaries as hierarchy. Lossless transport
groups only supplied equal values at equal scopes, retaining false assertions and
conflicts; it never corrects them from evaluator truth. It is a diagnostic ceiling
for transport, with a different call count, not an unqualified fair-performance
claim. Global reviewers provide the three-call architectural control.

Within-input controls include a shared claim with a decisive or harmless unique
clause, numerical contradictions differing by one unit, scoped entity/condition
differences, and explicit version-2 authority with version-1 reports still visible.
Changed-world tests regenerate correct reports; corrupted-report tests keep the
world fixed and expose evidence resolving the error. High/low overlap controls
retain distinct claims, report identifiers, slots, order and evidence. Character
overlap and native-token residuals are recorded in `records/preflight/`.
Workflow conditions are explicit rule predicates, not arbitrary natural-language
exceptions. Numerical false reports are not paraphrases. Version authority is
explicitly specified, not inferred from recency.

The same subset tests 1, 2, 4, 8 and 16 total presentations with worker execution
count fixed at zero model workers. Neutral administrative material matches added
slots and report text tokens; whole manager prompts differ by up to 15 tokens in
the initial check. Scope and ancestry metadata remain present in the neutral arm.
Adjacent/end placement and same/different copy-branch controls are separate.
The dose range will not expand in response to the observed direction.

Ordinary, checklist and scope-aware instructions share task data and output
contracts. Exact-string removal and a fixed 0.9 character-similarity threshold
are evaluated on the decisive overlapping presentation. Preprocessing loss is
scored, including accidental removal of unique clauses. This heuristic is not
representative of every semantic deduplication system. The scope policy receives
no additional oracle facts. Existing frozen supporting-v7 controls retain their
ancestry, instruction-only, distinct-scope branch and other original comparisons.

## Observable outcomes and inference

Exact final correctness remains the operational outcome; completed malformed or
truncated outputs remain failures. Every base's planned trajectories must complete
before that base enters analysis. Only declared engine failures can be resumed;
an accepted malformed response is never resampled.

Boolean-critical retention uses the single-truth-flip definition above. Necessary
retention instead removes one scoped assertion and checks whether the remaining
information uniquely determines the correct candidate; it includes objectives.
Each retention proportion's denominator is the number of eligible unique scopes
in that trajectory, including lost claims in failed summaries. Unrepeated necessary
retention excludes the emphasized scope. A retained value must be explicitly
correct at its scope without a contradictory value or unresolved flag.

Summary sufficiency asks whether emitted values alone determine the correct choice.
An incorrect root decision despite sufficient summaries is an observable
integration error. This does not prove a causal reasoning path or faithful
mediation. Unique-clause retention, wrong-scope citations, incompatible cited-scope
merges, unmerged equivalent emissions, injected-value emission/adoption and
superseded-scope emission have separate fields. Emitting an obsolete scope is not
automatically proof of relying on it internally. Rates of false adoption use only
parseable outputs and explicitly report their available denominator; overall
correctness includes operational failures.

Effects pair matching world/repetition cells, average within independent base
pairs, then weight bases equally. Family-by-change-status stratified cluster
bootstrap uses 10,000 replicates and seed 20271015. Singleton strata do not support
the requested uncertainty estimate: their intervals are withheld. No confirmatory
p-values are planned. Wide or degenerate intervals are not evidence of robustness.
Both-world correctness defines successful response/stability; merely changing or
retaining an answer does not. Brier/log loss use valid probability distributions
only. Tokens per correct decision have the number of correct decisions as their
denominator; latency and allocated engine inference time are reported separately.
Actual GPU billing and monetary cost are not observed.

## Bounded fresh verification

`fresh-probe-v1` uses six existing scheduling development bases and one resource
predicate per base. Other mandatory scopes remain available as frozen reports.
One initial live report is shared across original, four exact copies, verified
template paraphrases, and three added fresh executions. Fresh workers see only
their assigned data and no prior reports; roots see the same authoritative task
data in every arm. Errors in the initial report are preserved.

Fresh added-resource and fixed-resource variants share the initial execution. The
fixed variant bounds the entire trajectory's input tokens plus allowed output by
the original worker-plus-root allowance. It logs reduced worker/root caps. If
complete input cannot fit, it records resource displacement without truncating or
dropping essential evidence. Token matching is not FLOP matching. Assigned event
and integer-slot procedures do not prove the model used different algorithms.
No verified witness or genuinely new source observation is claimed. The existing
whole-live adequacy failures preclude interpreting this narrow test as a general
worker-scaling result; optional 8/16-worker experiments are not launched.

## Fresh validation and held-out extension

Machine-readable rules are in `configs/mechanism-analysis-v1.json` and
`configs/mechanism-allocation-v1.json`. Validation uses 24 new base pairs at
validation indices 36–59, disjoint from original validation 0–35. Ordinary flat
single-presentation scheduling accuracy must reach 85%; hierarchy accuracy is not
a gate because summary failure is under investigation. No gate is relaxed to
obtain a preferred direction.

The core extension retains hierarchical F/A/common/E, bypass F/common, both worlds
and one repetition. The primary population is scheduling; workflow remains
secondary. The three primary contrasts are:

1. P1: decisive-four minus common-four, final correctness.
2. P2: common-four minus unrepeated, retention of unrepeated necessary scopes.
3. P3: the repetition effect in summary-only hierarchy minus that effect with raw
   bypass, final correctness. This is an interaction, not overall hierarchy error.

One model is used for this bounded extension; the original two-model main is
preserved. New held-out indices begin at 384 (original main uses 0–191). The
prospective rule chooses 24 or 48 pairs using validation stratum variance and
measured time, never the sign or significance of an effect. It prefers 48 unless
24 meets a 0.10 approximate interval half-width for all three contrasts with
observed variance. A six-hour measured inference planning bound can reduce this
to 24; if even 24 exceeds the bound or competence fails, no new held-out run starts.
Zero observed variance does not constitute a precision or power claim. This rule
is an allocation plan, not a RunPod billing change. The selected configuration,
analysis hash, source snapshot and decision record are frozen before inference.

## Execution and review safeguards

Before any new inference, final analysis review found that the four-presentation
arm also appeared in the broad core. `mechanism-analysis-correction1.json` records
an analysis-only fix: dose estimates restrict all levels to the same selected
world-0 cells. Trials, prompts, primary contrasts and the queued inference snapshot
are unchanged. The archived controller preserves its original analysis source;
the local refresh hook applies the corrected analyzer to completed suites and
records its hash. This implements the already specified subset, rather than
choosing a subset after seeing new outcomes.

Allow the current original Qwen3 main/support/live stage to finish. A queued
successor runs the bounded extension, then resumes the original Phi-4 stage from
its original snapshot. Even an extension failure must not discard that original
work. No process is killed, no extra infrastructure is provisioned, and no paid
API is used. Local mirroring and the finalizer preserve raw outputs outside Git
and compact records inside Git. The finalizer waits for amendment completion or
an explicit allocation-gate decision; it cannot label the revised study complete
merely because the original main finishes. All manuscript results require completed
analysis records, and human scientific review remains pending.
