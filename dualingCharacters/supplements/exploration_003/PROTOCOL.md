# Exploration 003: post-outcome observable exploration audit

This direction was author-specified after negative/mixed C5 accuracy comparisons,
the C1 seed reversal, the intent002 investigation, and inspection of pilot
slot/value repetition. It is exploratory, not a new reading of the original
preregistered hypothesis. Known results include C5−C3 of −3.75 and −0.42 percentage
points at Qwen seeds17/29, and the approximate pilot repetition rates C3≈74%,
C5 Hyde/Rival≈89–90%. No result here changes training, endpoints or exclusions.

One shared work window starts **2026-10-24 21:46:15 UTC**, ends by
**2026-10-25 02:46:15 UTC**, with useful work ending by02:01:15UTC. In
America/New_York this is October24 17:46:15–22:46:15EDT. Verification and the
local main commit are inside this window. No new model calls, GPU inference,
training, model judging, paid API, pod, waiter or scheduling change is authorized.
The pre-existing core/review controllers retain ownership; intent002 stays disabled.

## Question and interpretation

Do persistent motive-conditioned characters expand coherent observable behavior
and behavior sequences relative to generic adversaries under matched budgets?
Separate (A) descriptor/state breadth, (B) sustained goals with changing tactics,
(C) complementary generation, and (D) learned defender exploration. These logs
directly address only proxies forA–C. D requires a new task in which the defender
chooses hypotheses/inquiries. Breadth, fixation, incoherent variety and no
difference are all admissible findings. No semantic strategy or hidden intention
is established by an API type, contradictory value, prompt utility or peer match.

## Immutable evidence and comparison populations

`EVIDENCE_SNAPSHOT.json` locks all locally completed collection/mechanism runs
at its exact early-session cutoff. `DATA_AUDIT.json` binds raw/status/config/source
and adapter hashes, paired coverage, action ordering, opportunities and missing
fields. Partial and previously excluded runs remain visible outside estimates.
Later completions can be reported operationally but cannot enter this population.

The primary dataset is **mechanism-final-001**, the final source/scheduler pilot:
eight families, two worlds,16turns, seed17, untrained pinned Qwen defender and
frozen Qwen character generator. C3/C5 share backbone revision, weights, public
scenarios, schedule and budgets; their endogenous states and random call offsets
are not identical. Conditions C1/C2/C4/C6/A1/A2/A3 provide descriptive context.
This is one small generator-seed pilot, not independent learned replications.

Main collections are a separate observational population stratified by seed and
round. Round0 uses a common untrained defender; round1 uses condition-specific
round0 adapters and different150families/32turns. Round0 has150families/16turns.
Do not pool those rounds as an intervention on history or compare unmatched seeds.
At cutoff, main C2/C6/A2/A3 are missing. Their pilot cells are not main results.
Earlier mechanism v2/v3 and other prior collection protocols remain inventoried,
with coarse action/repetition diagnostics; modern source/semantic categories are
not retroactively imposed on their different source/routing implementations.

Verify definitions from frozen `characters.py`, `evaluation.py`, `fast_backend.py`:
C3 has two adaptive generic contexts; C4 one antagonist; C5 Hyde/Rival; C6 four
antagonists. A1 removes biography only, A2 accumulated own history, A3 peer delivery.
Frozen character generation disables defender LoRA. C2 uses deterministic bounded
random corruption and no character model calls. Casts own distinct assigned slots;
their preferred commitments can be jointly satisfied. C4 reserved peer messages
can reach Jekyll, unlike the instructed C5 antagonist-peer routing. These differences
limit count/conflict attribution and are not repaired by this analysis.

## Descriptor freeze

`CODEBOOK.md` and `descriptors.py` fix two layers. Layer1 uses actual parsed actions,
source visibility, offline time-indexed truth and working state. Its primary tuple is
**(API kind, delivery route, value relation, reference relation)**. It excludes raw
slot identity, owned-slot identity, names, option strings, biographies and wording.
An API-valid nonempty task-slot action or addressed peer claim qualifies as a
structurally interpretable observable category; this is a proxy, not human-validated
coherence. Deliberately incorrect actions are retained. Empty/malformed/unavailable
actions and passes consume budget but contribute no categories. A3 no-delivery
peer messages remain valid proposed actions; application is analyzed separately.
The coarse kind/route sensitivity detects differences caused solely by API use.

Current truth comes from `scenario.truth_at(turn)`, checked against each saved
target. Final truth never labels an earlier action. A reference can match a
superseded explicit commitment or a nonbinding mention; source availability and
authorship are separate. Semantic sufficiency of generic/anaphoric user text is
unresolved. Missing fields remain missing, including C2's absent model observation.

State-transition descriptors compare pre-action character-observed memory with
post-action defender-observed memory at the same turn. Their slot categories are
unchanged, correct→incorrect, incorrect→correct, incorrect→other incorrect,
missing-state or untyped. Following adoption/error are associations; no causal
attack success is inferred. A genuine user revision can change correctness without
an action. No-intervention counterfactuals are unavailable in these rollouts.

## Endpoints, budgets and uncertainty fixed before category summaries

Primary: C5−C3 difference in **distinct valid observable descriptor categories per
episode at12intervention opportunities**, averaged over both worlds within family,
then families. The cap is mechanically the smaller verified per-episode schedule
length in the primary pair. Report all1…12prefixes, including passes/rejections.
Report pooled archive coverage separately: it measures collective variety across
episodes, not typical within-episode variety or the size of all possible strategies.

Use paired family bootstrap10,000draws with seed830031, preserving worlds,
conditions and prefixes. The endpoint CI is exploratory and conditional on eight
pilot families/one generator seed. Curve intervals are pointwise, not simultaneous.
No hypothesis-testing or multiplicity-adjusted superiority claim is made. Main
contrasts are per matched seed/round with family intervals; incomplete seed sets
are not used to claim training-seed robustness or a population variance estimate.

Secondary descriptors: coarse kind/route coverage; number of distinct immediate
state-transition types; canonicalized **two-consecutive-opportunity** sequences,
including same/different anonymous actor relation. Invalid/pass actions break
sequences; never bridge episodes or tune sequence length. Consequences, structural
validity and application retain their own denominators. An applied pass is not a
substantive shared-state change.

Novelty/saturation: new episode categories in opportunities1–4,5–8,9–12. Persistence:
within-actor consecutive direct-action slot/value repetition, same-goal changes in
API/route/reference-use proxy, and return to a previously pursued slot/value after
a different direct goal. Truth reclassification alone does not count as a tactic
change. These are not validated semantic tactic counts. Count within-actor coverage,
sum of actor coverages, union, and union beyond the largest actor. Different cast
sizes mechanically alter per-actor opportunity counts; show these denominators.

Complementarity: full-prefix intersection/C5-only/C3-only categories per episode
and pooled. Also union C5's first6 and C3's first6 opportunities against each
single method's12: the mixture spends12, not24. It is an offline archive mixture,
not a newly run interacting ensemble. Show its actual character and defender-prefix
token cost, including two separate initial trajectories. Additionally aggregate
whole paired families under100fixed SHA256 orderings; alternate C5/C3 families
for balanced mixtures and compare the same number of whole episodes/opportunities.
Never shuffle actions inside an episode. Ordering envelopes describe finite archive
sensitivity, not inferential confidence or unseen-strategy richness.

Token sensitivity uses measured **input+output** character tokens including
biographies, history and system prompts. LetT be the minimum complete episode
token cost across the C3/C5 primary data. Compare strict chronological prefixes
that fit floor(T×.25),floor(T×.5),floor(T×.75),floor(T). Stop before the first
unaffordable action; never skip an expensive action to include cheaper later ones.
Report used tokens, consumed opportunities/calls and leftover allowance. Defender
rollout costs and whole-run/model-load accounting are reported separately; equal
opportunities or token counts are not exact FLOPs. Random C2 is a different cost
regime. Missing actual accounting is never converted into a measured cost estimate.

Any coverage/accuracy association is descriptive. Do not infer that coverage
causes learning: defender identity, curriculum severity, recovery diversity,
teacher targets and supervised-token concentration remain confounders. Existing
negative/mixed antagonist-free main results remain visible as context.

## Semantic review and illustrations

Layer2 defines compact semantic codes, coherence/relevance/novelty criteria and
ambiguity rules, not automatic semantic labels. A **56-window** packet takes one
window per each of eight pilot families for each C3/C4/C5/C6/A1/A2/A3 condition.
Per condition four worlds are authorized and four hypothetical, allocated by
condition/family hash independent of outcomes. End anchors4/8/12 are selected by
a second fixed hash; each window contains three consecutive intervention actions,
their actual visible sources, pre-memory, received messages, preceding and following
answers, and offline current truth. The code fixes these hashes before summaries.
No repeated windows inflate the sample, and no nonexistent cells are fabricated.

Hide conditions, seeds, roles and biographies; preserve stable anonymous speakers.
Cast size, routing and wording may still disclose condition. Reviewer-facing files
and the private key are separate. Two blank forms must never overwrite human
annotations. No raters are contacted. An AI-assisted reading of at most one
deterministically selected window per condition may be presented as unvalidated
illustration, never human scoring or a prevalence estimate. Additional repetitive
or ambiguous illustrations use declared lowest-hash proxy strata with prevalence
reported. No external/model-judge inference is authorized.

## Reproducibility and amendment rule

Freeze this protocol, codebook, evidence audit and scientific Python files in
`SCIENTIFIC_MANIFEST.json` before the first comparative category summary. Subsequent
corrections require an append-only amendment naming the defect, affected outputs,
old hashes and new version; preserve original results. Reporting/plot layout and
operational monitoring can evolve outside that scientific manifest without changing
definitions or population. Raw traces, caches and review payloads stay outside Git.
No original freeze is changed. The final report identifies what completed, what
remains pending, whether the observations favor breadth or fixation, and the single
fresh common-defender control that would most reduce uncertainty.
