# Behavioral Effects of Persistent Motive-Conditioned Components in Conversational Systems

This is a new **descriptive, exploratory** question, specified after mixed/negative
task-performance comparisons and the inconclusive exploration003 audit. Success
does not require a benefit or a difference. The question is what changes when
components have persistent motives, biographies, private histories and channels
for communication. The frozen original study and its findings remain intact.

One session starts 2026-10-25 02:36:18 UTC (October24 22:36:18 America/New_York),
ends by 07:36:18 UTC (October25 03:36:18 local), with useful work ending by
06:51:18 UTC. No new GPU inference, training, model judge, paid API, pod, scheduler,
background waiter, publication, push or external contact is authorized. The
existing core/review owners continue; intent002 remains disabled. Finish early
when useful scoped work is complete.

## Knowledge and evidence boundary

Known before this freeze: no demonstrated C5 average accuracy or descriptor-breadth
advantage over C3; pilot edit/recollect counts reported as C3 89/17 versus C5 5/78;
typed-goal repetition approximately74% versus89–90%; similar C5/A1 coverage;
source access can change a descriptor without changing claim text; communication
ablation can generate rejected actions; different assigned slots permit simultaneous
owned-option adoption. These will be verified, not described as unexpected discoveries.
Newly completed seed43 summaries have been inventoried for completeness, not used
to choose metrics. The neutral question follows the prior results transparently.

Four levels govern every claim:

- A: directly measured actions, text, source access, memory changes and deliveries.
- B: descriptive associations with events, observations and subsequent outputs.
- C: explanations isolated by an appropriate controlled comparison, with the exact manipulation stated.
- D: hypotheses requiring a new experiment or human semantic evidence.

## Locked populations

`EVIDENCE_SNAPSHOT.json` locks completed eligible runs at its timestamp;
`DATA_AUDIT.json` binds configurations, revisions, weights, source archives,
family/world/turn coverage, actual action order and raw bytes. Later completions
are operational news only. Excluded and incomplete artifacts stay visible outside
estimates. Earlier pilot protocols remain in exploration003's historical records,
not pooled with the final mechanism protocol.

1. **Principal population:** main round-zero collections using the common pinned
   untrained Qwen defender; 150 paired training families, 16 turns, seeds17/29/43
   where complete. The same families repeated across seeds are not new families.
2. **Mechanism pilot:** final protocol, eight paired pilot families, 16 turns,
   one generator seed. Ablations and detailed sequence evidence are small-sample.
3. **Refreshed collections:** separate observational population, condition-specific
   round-zero defender adapters, different150families and32turns. Differences from
   round zero do not isolate learning, history or time.
4. **Antagonist-free evaluation:** completed eligible64-turn summaries and existing
   verified exposure/clarification/source audits, as secondary context only.

Primary contrasts are **C5−C3 and C5−A1**, matched by seed, family/world, horizon,
schedule and revision. C4/C6 and A2/A3 are descriptive context with missing cells
left missing. C1 has no character opportunities; C2 has deterministic corruption
and no generator calls. C3 and C5 share actor count but differ in objectives and
biography; C5/A1 removes biography text only in this implementation. This cannot
identify the general value of narratives or a latent personality.

## Three primary descriptive families fixed in advance

**A. Intervention channels.** Count generated edit, recollect, propose, peer-to-
answerer, peer-to-component, invalid-recipient peer, pass, malformed and unknown
actions. Keep API channel separate from structural validity and actual application.
Use all allocated opportunities and actual API-available opportunities; direct APIs
are available in unrestricted slots, while peer/pass are available in both slot
types. Reserved slots permit peer/pass only. An instructed recipient preference
is not a hard routing restriction: the core accepts Jekyll when listed.

Report condition/actor/role, slot type, ordinal, turn and event-phase exposure.
Neutral aliases are randomized, **role-to-opportunity order is fixed**. Compare
generated → structurally valid → applied/delivered → changed state/evidence/notes
→ following typed adoption/current-turn success, retaining missing denominators.
This is a branching flow, not a monotone funnel: the core can apply an empty claim
that the structural-interest proxy rejects. A pass may be marked applied without
changing shared state. Distinguish notes and peer inboxes from direct slot writes.

**B. Persistence, revision and responsiveness.** Reproduce within-actor consecutive
valid direct-action slot/value repetition. Also retain strict adjacent-own-opportunity
repetition, where intervening peer/pass/invalid actions break adjacency. Direct-
subsequence goal runs record action count, intervening own opportunities, conversation
turn span and terminal censoring; runs of length≥2 are repeated runs. Different direct
goals break runs; returns count after an intervening different direct goal. Normalize
by actual own/direct opportunities and do not compare unequal actor exposure as psychology.

During a repeated goal, count changes in **API channel** separately from exact
normalized delivered-claim repetition and reference changes. Text normalization
only folds case/whitespace and neutral aliases. Different text is not automatically
a substantive change; paraphrase and semantic tactic development require review.
Record same-text/same-source cases whose availability changes; do not relabel
them as strategic adaptation. Preserve 240-character delivered truncation versus
the fuller generated claim.

Event windows are fixed: for every noninitial set, consider, reject, suggest and
ambiguous event, inspect each actor's last two unrestricted opportunities before
and first two at/after that event. Report overlaps, number of eligible actors and
actual turn lags. Event windows are not independent samples. Initial commitments
are a separate baseline. For update responsiveness, show all exposures and the
subset where the event concerns the actor's assigned slot. Separate revisions
away from, toward, or unrelated to the fixed preferred option. Operational
"insistence" is renewed direct endorsement of the owned option after a genuine
update away from it; it is not tenacity, competence, pathology or a semantic belief.
An endorsement means a typed action, not final assistant acceptance.

For response to the defender, use the latest plan actually present in own-history
observations when available. Distinguish typed adoption, another value and unknown;
an alternative structured plan does not explicitly reject or ignore a proposal.
Acceptance/rejection speech acts and semantic revisions remain pending review.

**C. Evidence and peer interaction.** Reuse current-turn truth and actual sources
to distinguish absent/unavailable/user/assistant references, current/superseded/
nonbinding support, current values with inappropriate evidence, and unresolved
canonical mismatches. Report literal authorization/advocacy/correction vocabulary
only as lexical candidates, including negation flags. A wrong typed value or a
recollect label does not prove false authorization or deliberate deception.

Reconstruct directed delivery using the actual inbox queue, capacity and clear-on-
observation rule. Keep sent, applied delivery, present in recipient observation,
next/second recipient opportunity, typed match, typed contradiction and unresolved
semantic response distinct. A terminal recipient with no later opportunity is
missing follow-up, not ignored. Jekyll notes follow the separate same-turn answerer
observation channel. Verify queue signatures rather than matching identical messages
by text without order. Record reconstruction disagreements without inventing delivery.

The reference for typed matching is the recipient's **last opportunity before the
message**, among visible messages with both a previous and next opportunity and a
valid typed message goal. Also report same-slot-type pre/post cases. This is a
descriptive temporal reference, not a randomized counterfactual; context, opportunity
availability, stable preferences and message selection differ over time. No shuffled
message test, causal influence estimate or coalition claim is made.

## Truth, metrics and uncertainty

`DEFINITIONS.md` and scientific modules fix fields and denominators. Assert every
saved target against `scenario.truth_at(turn)`. Original users authorize truth;
character agreement never does. Compare same-turn pre-action memory and the next
defender prompt. When no character observation exists (C2), reconstruct pre-memory
from the preceding defender prompt plus its executed memory update; mark that
origin and validate the reconstruction against character observations where present.
Subsequent plan change uses the same current truth for before/after scoring and
flags a genuine user update. These are associations without a no-action replay.

No formal significance tests, improvement ranking or composite score. Report
counts, missingness, distributions, per-seed rates and descriptive paired intervals.
For named contrasts, aggregate numerator/denominator within family across both
worlds; compare matched family rates. Conditional endpoints use families with
nonzero denominators for both conditions, with exclusions/counts reported. Such
conditioning is descriptive, not a causal estimand.

Use10,000paired bootstrap draws with seed400041. Within one generator seed,
resample whole families preserving both worlds, trajectories and methods. Across
complete matched seed sets, independently resample the common families and the
observed seeds, retaining the full method pairing. Three seeds give limited
information about generator-seed variation. No action-level independent error
bars. Pointwise intervals across this descriptive family are not simultaneous
and no multiplicity-corrected discovery claim is made. Missing or too few independent
families receive counts rather than an unjustified interval. An interval spanning
zero is not equivalence.

Actual per-generation input/output tokens include history/prompt overhead. Keep
defender costs, recovery-candidate residuals and loading/reservation time separate.
Different costs or prompt lengths can explain behavior and cannot be relabeled
efficiency. Join existing loss-exposure audits only when their source hashes still
match; missing newer fits remain missing rather than triggering redundant audits.

## Semantic review and interpretation

Preserve the existing56-window packet and every rating form byte. Its three-action
windows support local claim reading but often omit goal development and recipient
follow-up. A **24-item matched addendum** uses four fresh training-family selections
per each available main-round-zero seed17/29/43, both C3/C5 for the same world/window.
Hash-rank families independently of behavior; alternate worlds to give two of each
per seed. Focus on two collective opportunities before and four at/after the paired
switch, plus at most two following opportunities. Include actual sources, own
history/inbox, pre-memory, current truth and following outputs. Selection does not
require a message, success, contradiction or interesting behavior. No old pilot
window is relabeled as new evidence. Missing seed pairs stay missing.

Hide condition/seed/role metadata, preserve stable anonymous speakers, and disclose
blinding limits. Mapping stays separate; two forms remain blank. At most one
lowest-hash matched family per seed (six items) receives an explicitly unvalidated
AI-assisted reading, separate from ratings and prevalence. Semantic objective:
what claim/interaction occurred and what evidence supports it, not which method wins.

Integrate at most four reproducible findings in a behavioral matrix with expected
prompt effects, schedule/routing explanations, context and unresolved mechanisms.
Retain prior negative/mixed efficacy and inconclusive breadth. Inspect existing
review001 conflict/routing/severity plans before proposing one discriminating
follow-up; do not duplicate or schedule them. Scientific conclusions and draft text
remain for human author review.

## Freeze and correction rule

Freeze this protocol, definitions, snapshot/audit and scientific Python files before
new comparative summaries. Corrections need a dated amendment, preserved prior
files/outputs and explicit affected estimates. Later report/plot presentation can
change outside the manifest without changing metrics or population. All127 prior
scientific files remain unchanged. Raw traces, caches and review payloads stay
outside Git; only compact code, tables, figures and reports are committed locally.
