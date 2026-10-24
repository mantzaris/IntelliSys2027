# A small decisive follow-up — proposed, not scheduled

The largest missing control is a competent generic generator explicitly asked to
explore coherent, nonredundant strategies. The existing generic opponent optimizes
disruption, while the present character approach has neither an explicit diversity
objective nor mutually incompatible owned-slot goals. A positive descriptor count
alone cannot distinguish useful exploration from superficial variation.

This document proposes new work for author review. It authorizes no model calls,
training, resource reservation or queue change. It is not part of the original
study or this supplement's frozen analysis.

## One fixed-defender experiment

Use four conditions, each with two generator contexts and the same frozen Qwen
base defender and generator revision `cdbee75f17c01a7cc42f958dc650907174af0554`:

| Condition | Generator instruction | Essential inference |
|---|---|---|
| G | Existing strong generic disruption objective | Anchor against the implemented comparator |
| G-diverse | G plus explicit coherent, task-relevant, nonredundant exploration; use history to avoid repeating substantively equivalent tactics | Does character conditioning add anything beyond an explicit exploration objective? |
| M | Concise persistent motives/utilities, without narrative biographies | Is a biography needed beyond explicit motives? |
| P | Persistent biographies, identical motives/utilities to M, private histories and peer delivery | Character-centered candidate |

The decisive contrast is **P versus G-diverse**, with P versus G and P versus M
reported beside it. Keep the same observations, history capacity, peer tools and
scheduler in all four conditions. A generic condition must receive the same
opportunity to communicate and adapt. No condition receives the oracle, semantic
ratings, a privileged strategy list, or diversity feedback that another lacks.
G-diverse's instruction is the declared manipulation, not hidden extra search.

Proposed scale: 16 fresh paired families, 16 user/answer turns, generator seeds
17/29/43, four conditions: 384 episodes. Each has 12 total intervention calls,
divided into eight direct and four separate peer opportunities; passes and invalid
outputs still consume them. Use common family/world inputs and independently
keyed per-episode random streams. Randomize neutral aliases and ownership under
fixed seeds. Reset private histories between episodes; keep generator weights
frozen. This is a generator experiment, with **no parameter training**.

Keep the existing 4,096-token input ceiling, 256 answer-token ceiling, 128 character-
token ceiling, eight retrieved messages, four recent messages and six own-history
actions. Retrieval is fixed and cannot consult truth labels. Use identical
truncation rules. Equal ceilings and opportunity counts do not imply equal realized
tokens or FLOPs: report all prompt/history overhead, outputs, loads and failed
attempts, and the already defined strict chronological token-prefix sensitivity.
Do not pad a method with dummy tokens and call that equal useful compute.

Freeze fresh family IDs, script/event hashes, prompts, stream keys, ordering,
checkpoints, endpoint, sample size and exclusion rules before model execution.
Do not reuse the current eight pilot families. A fixed 16-family study remains
small; its intervals should be reported rather than advertised as adequate power
for an arbitrary effect. A later increase requires a new design, not inspection
of whether this one is significant.

## What would make the test informative

Retain observable descriptor coverage at 12 opportunities for comparability.
For the new exploration claim, also require **human-supported semantic strategy
coverage** from the fixed codebook, distinguishing coherent task-relevant false
claims from noise. Two independent raters should label the complete sampled
episodes, with disagreements and adjudication retained. Review all 12 actions and
their evidence before claiming episode-wide semantic coverage. A few attractive
windows cannot validate that endpoint.

The proposed rating workload is 384 episodes × two raters = 768 episode reviews.
At an assumed 3–5 minutes each, that is approximately 38–64 total person-hours;
this is a planning assumption, not measured human throughput. Obtain a realistic
rating plan before execution. If only a small packet is feasible, restrict claims
to a validated subset and leave whole-dataset semantic breadth unresolved. Do not
silently replace humans with an unvalidated model judge.

Report per-episode and archive coverage, within-goal semantic tactic changes,
repetition, chronological novelty, and actual costs. Preserve both worlds within
family and condition in resampling; with three generator seeds, preserve seeds too
and state the limited estimate of seed variation. Use the fixed sequence length
two and the same equal-budget prefix/archive mixtures. Match the defender weights;
report that realized defender states still diverge after different interventions.

Evidence favoring P would require a useful semantic breadth or development gain
over G-diverse at comparable costs, not just a larger tuple count. If P exceeds G
but not G-diverse, explicit exploration instructions are a sufficient competing
explanation. If M matches P, withhold a biography-specific benefit. Null or negative
findings remain informative about this implementation.

## Optional factors, only when the claim needs them

The existing A2/A3 pilot supplies context, but its small sample and rejected-action
differences do not isolate history or interaction. A later targeted P-without-history
or P-without-peer-delivery arm would test the corresponding claim while retaining
the same reserved communication slots. A diverse cooperative-perspectives arm is
optional if the question becomes whether antagonism contributes beyond heterogeneous
perspectives. Do not add every factor to a large factorial training grid.

The current distinct-slot ownership permits simultaneous preferred-option adoption.
If **conflict** is claimed as the mechanism, add a separate controlled comparison:
both actors target the same slot in both arms; in the compatible arm they prefer
the same option, and in the incompatible arm they prefer different options that
cannot both occupy that slot. Counterbalance whether either preference initially
agrees with the user and include ordinary authorized updates that change alignment.
Hold biographies, histories, budgets and delivery fixed. Do not script betrayal,
deception, collaboration or successful interference. This manipulation is a future
mechanism test, not a retrospective repair of the frozen core.

## Resource estimate, not a reservation

The proposal contains 6,144 defender calls and 4,608 character calls, 10,752 total.
The completed `mechanism-final-001` pilot recorded 3,648 calls in 532.5565 reserved
seconds, including 38.8208 loading seconds. A call-scaled planning calculation,
with 1.5× execution margin and three model loads, gives **2,299.29 seconds
(38.32 minutes)**. The reproducible calculation is in
`reports/future_resource_estimate.json`; it is an estimate, not newly consumed time.

Prompt lengths, batching, changed instructions and failures can invalidate that
scaling. Before any authorization, reserve roughly twice that planning estimate
(about 77 minutes) or revise it from a separately authorized engineering profile.
Admission must use the then-current remaining study budget and existing lock, and
must preserve core/review/intent priority and contingency. This proposal has no
dispatcher, background waiter, activation file or scheduled start. No dollar cost
is supplied because the actual pod rate is unknown.

## Future application: diagnosing an unexpected research null

To test learned exploration by the defender, give it a research result compatible
with several causes: ineffective treatment, weak implementation, measurement
failure, insufficient sensitivity, a population mismatch, or a false premise.
Let it choose a bounded sequence of evidence requests from a fixed costed menu,
including checks that can disconfirm its favored explanation. The hidden causal
case determines available evidence; an independent evaluator scores it. This is
a proposal for a new task, not a benchmark implemented in this session.

Measure plausible distinct hypothesis coverage without rewarding irrelevant lists;
the discriminating value and cost of chosen inquiries; revision after contradictory
evidence; calibration and correctness of the final diagnosis; and a useful next
research action. Include ambiguous cases where a qualified diagnosis or targeted
request is correct. A frozen rubric can rate explanatory coherence; a known
generative case can score information gain and diagnostic accuracy separately.

Evaluate fixed trained defenders with antagonists removed, common interfaces and
matched seeds/budgets. Compare C5 with both C3 and C1. This would test transfer of
exploration behavior directly. More varied training traces, preserved memory, or
final-answer accuracy in the current six-slot task do not demonstrate that transfer.
