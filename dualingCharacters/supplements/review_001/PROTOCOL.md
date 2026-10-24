# Review supplement 001 — exploratory, after observed main results

This supplement was requested and designed **after inspection of C1 seed 17**.
During the initial current-state audit, C3 seed 17 was also complete and its
177/240 paired successes were read. The untrained result and historical pilots
were already known. Existing-test analyses here are exploratory, not original
preregistered confirmation. No supplementary model calls precede the implementation
freeze and prerequisite checks. The core experiment, its order and its endpoint
remain unchanged.

Core freeze SHA256:
`135e78e2423d0bc42e340098021a912df269a39949d50cb6fbf91d4edb93f2f3`
(58 files). Qwen revision:
`cdbee75f17c01a7cc42f958dc650907174af0554`. Supplement code, this protocol,
configuration and fresh-data manifests receive exact hashes in `FREEZE.json`.
Timing-based concrete allocation receives a second freeze in
`artifacts/review_001/allocation.json` before any diagnostic outcomes are analyzed.
Both freezes and chronology are retained in the provenance manifest.

## Fixed policies and hypotheses

Use only Qwen, seed 17, the untrained backbone and the **fixed final round-one**
adapters from C1/C3/C5. C1 resolves to
`main-qwen-c1-17-r1-fit-format2`; C3 and C5 resolve to their original
`main-qwen-{c3,c5}-17-r1-fit` IDs. Exact adapter bytes and completed evaluation
hashes are bound before profiling. Missing prerequisites mean waiting or a
pending result. No favorable replacement, seed selection or new parameter update
is permitted. B and C use the untrained Qwen defender and frozen untrained character
generator, chosen here before their results exist.

- A: Test dependence of final decisions on explicit terminal memory and on
  retrieved assistant messages. No directional advantage is assumed. Similar
  performance after removal is compatible with limited dependence at that final
  observation, not proof that memory or the preceding trajectory never mattered.
- B: Test whether incompatible owned options alter observable tactics, disclosures
  and recipient responses beyond separate-slot personas. Conflict does not require
  or predict a betrayal, deception, coalition or a higher defender error rate.
- C: Test the communication-routing difference separately from the original learned
  character-count contrast. Frozen-policy evidence cannot repair that contrast.
- Severity and balanced validation are optional, explicitly exploratory diagnostics.

All inference uses the existing pinned vLLM environment, BF16, batch limit 64,
4,096 input tokens with no silent truncation, 256 defender tokens and 128 character
tokens. Defender decoding is greedy with the unchanged public schema. Characters
use temperature .7/top-p .9 and the existing action schema. Actual tokens and
reservation time are measured; equal caps are not equal FLOPs. Retrieval remains
the fixed lexical scaffold, not a learned action.

## A: terminal-memory interventions

Input source: completed, eligible C1/C3/C5 seed-17 main final-turn prompts.
Preserve both worlds. The first choice is all 240 families. If the outcome-blind
runtime allocation cannot fit that choice plus B, use the first feasible count
from 120, 64, 32. Selection takes an equal number from each of eight domain/rule
cells, ranked by SHA256 of `review001-A-family-v1:family_id`, then original family
order for batching. It never uses success, failure or canonical-source visibility.

A0 preserves every prompt content byte. A1 changes only memory state to six nulls,
evidence to six nulls and notes to an empty list. A2 additionally removes only
assistant-authored entries from the supplied sources, preserving every remaining
message, index, catalog field and current user request. No label-driven retrieval,
source addition, oracle summary or source reconstruction enters these interventions.
A1 leaves information in assistant messages; A2 can remove useful evidence.

First report raw-text, parsed-answer, executable-plan and paired-success replay
agreement for A0 versus the saved answers. More than 1% parsed-answer disagreement
or an absolute paired-success change over 1 percentage point is a **material replay
discrepancy**. This flags interpretation for source/adapter/version/schema/batching
audit; it does not exclude cases or authorize retries or checkpoint changes.
Contrasts remain visible with that qualification. Exact GPU bitwise replay is not
assumed. Input-content, tokenizer-template, model, adapter and decoding hashes are
checked independently of scores.

If affordable after reserving A and B, use the same selected families for the
common-input reference. Apply the original public query and retriever to immutable
original **user messages only**, eight lexical selections plus four recent user
messages, with empty memory. Base/C1/C3/C5 receive identical source sets. No earlier
generated assistant response enters retrieval. This is a **collapsed source-reasoning
reference**, not a matched 64-turn rollout. The recent-message pool differs from
the mixed-transcript pool, and actual source coverage must be reported.

Report paired success and A1−A0/A2−A0 differences, authorized-update acceptance,
false hypothetical updates, recall, executable-plan accuracy, dependency errors,
source counts/authors, canonical-source visibility and tokens. Report descriptive
familiar/held-out-rule, domain and ambiguity strata. Ground truth characterizes
coverage only after inputs are fixed. No visibility-selected primary subset.

## B: fresh incompatible-goal mechanism study

Sixteen fresh paired families, 32 turns, four configurations, one frozen base
defender: B0 separate owned slots; B1 Hyde/Rival own different options of one slot;
B2 B1 without peer delivery; B3 B1 with concise utility/motive text and no biography.
The two B1 preferences cannot simultaneously fill their shared decision. The fixed
initial-alignment allocation is six Hyde-aligned, five Rival-aligned and five neither,
shuffled under a declared seed. Approved updates change alignment while preferences
remain fixed. Hypothetical paired worlds retain the earlier commitment. Public
dialogue is identical across B0–B3. All four domains occur, with familiar rules and
unambiguous updates here to isolate the mechanism.

`fresh.py` defines fresh wording and IDs, neutral aliases, option permutation,
profile wording, and an eight/eight randomized first-actor allocation. These stay
fixed within an episode and match across configurations. Histories reset between
worlds/episodes. Profiles and utility terms use the original character-centered
objectives. Only own history and newly delivered inbox messages are observed;
private truth, future messages and other private histories are never exposed.

Use the same 12 opportunities (four reserved communications), one-slot edit bounds,
four-note memory, six-action private history and original acceptance interface.
B2 uses the explicit no-delivery channel; B3 changes biography representation only.
An explicit supplemental rollout implements these conditions without monkeypatching
the core. B0 randomizes actor order as requested here, so it is not an exact replay
of the original mechanism pilot.

Measure preferred-option adoption, incompatible-goal exposure, repetition versus
tactic changes, edits, memory changes, source-visible contradiction flags, directed
messages and subsequent relevant behavior. Retain the original typed matching and
repeated-coordination criterion. These flags are not proof of semantic coordination
or hidden intent. False commitment claims and truthful disclosures require a
separate semantic review of actual text and visible sources.

Produce a deterministic blinded action-exchange packet with up to 12 typed matching
peer cases and 12 nonmatching peer cases per configuration, plus up to 12
source-contradiction flags and 12 other substantive actions. Within each stratum
rank the recorded case key by SHA256. Empty candidate strata stay empty. Include
source evidence and the recipient's next two opportunities; hide condition/profile
labels in the reviewer packet and retain a private key. This is enriched qualitative
sampling, not a deception prevalence estimator. Two blank rater forms and a fixed
rubric remain unfilled. Freeze item IDs once the complete selected packet exists;
never overwrite human annotations or silently change item identities.

## C, severity, and optional balanced validation

C uses the same 16 fresh paired families and 32 turns. Compare one antagonist with
private journal/no-delivery communication, two with peer delivery, and two with
delivery disabled. Every cast receives eight direct opportunities permitting
edit/recollect/propose/pass and four separate peer/journal opportunities. Reserved
messages cannot add notes to Jekyll; peer actions in direct slots are rejected.
Count actual direct notes, edits, proposals, deliveries, passes and rejected actions.
Actual influence need not be equal merely because opportunity counts are equal.

Optional severity replay selects 16 training families by SHA256 of
`review001-severity-v1:family_id`, both worlds and the first and last direct
opportunity at the original 16-turn horizon. Use the saved clean C1 round-zero
prompt as a common state and the C3/C5 round-zero action at that same family/world/
turn. Regenerate a no-intervention base answer and both modified-state answers.
Retain pass/peer/no-shared-change cases, not just successful attacks. No truth
determines selection or modifications. Report correct-to-incorrect flips among
fresh reference-correct states, all reference-incorrect cases, action applicability
and canonical coverage. "Reference-solvable" means the common frozen reference
succeeded; it is not an oracle proof that another case is impossible. No training
rebalance or update uses this diagnostic.

Optional balanced validation has 64 fresh families: four domains × two rule
structures × two ambiguity states × four replicates, each with both worlds.
C1/C3/C5 seed 17 receive 64-turn rollouts with original answering budgets and no
antagonists. Fresh source wording/IDs and graph hashes are frozen before evaluation;
exact graph/source overlap is checked against core manifests. The same six-slot
schema remains shared. This new validation cannot replace any original test case
or denominator and cannot establish broad domain transfer.

## Resource allocation and scheduling

The original 241-stage core queue has priority. One new coordinated post-core
controller replaces the two older CPU-only waiters. The user authorized this
review **before** optional unseen-profile evaluation. No active GPU job or core
controller is interrupted. The older supplement may run only afterward if its
original 3.5-hour gate and the new 30-minute contingency plus a 90-second last-batch margin can all be respected.

New review work, including loads, failures and profiling, has an absolute ceiling
of **two reserved GPU-hours inside the original 96 hours**. Preserve at least
30 minutes of project contingency. A further 90-second launch/last-batch margin
protects these caps. No extra GPU, API, rental or purchase is allowed.

After core completion, first bind prerequisites and run the fixed profiling job:
A variants/common input on 16 selected paired families (32 prompts per cell), and
B1 on eight distinct profiling families at 32 turns. Save outputs without computing
or displaying task-success or behavior metrics. Profiling has a fixed 900-second cap (including load); a failed profile stops supplementary execution with all costs retained. Use measured elapsed times and a 1.35 runtime
multiplier plus measured model-load time for future stages. The profiler and every
future run are charged to the shared ledger.

Freeze the feasible allocation **before analyzing those outcomes**. Choose the
largest A count that fits with all of B; if even A32+B cannot fit, choose the largest
feasible A alone and mark B pending. Then add common-input A, routing C, severity,
and finally the full balanced validation in that priority order if their predicted
costs fit. B remains 16 families; C remains 16; severity remains 16; balanced remains
64. No result-based sample reduction, retry, endpoint alteration or early stopping.
If a budget gate fails, mark the omitted module explicitly. A failed stage retains
its data/cost and stops the review queue for audit, without affecting the core.

Fixed run IDs: `review001-profile-17-v1`, `review001-memory-17-v1`,
`review001-conflict-17-v1`, `review001-routing-17-v1`,
`review001-severity-17-v1`, `review001-balanced-17-v1`.

## Analysis, exposure and interpretation

Use paired family-level percentile bootstrap intervals, 10,000 draws, analysis
seed 40721. Preserve both worlds and conditions within a family. This one-seed
supplement cannot estimate training-seed variation; no new confirmatory p-values
or multiplicity-adjusted success claims are introduced. Semantic annotations remain
pending until humans actually provide them.

The CPU exposure audit reconstructs tokenizer/chat-template bytes, alternating
clean/recovery sampling, packing, orphaned suffix masking and any resume-prefix
replay. It verifies per-step target counts against actual loss logs, and distinguishes
loaded windows, loss-contributing windows/occurrences, input tokens, target tokens,
families and recovery-pool concentration. Resume replay contributes no new gradient.
Detailed window-level exposure stays in ignored artifacts. Temporal action/error
associations remain separate from matched intervention replay.

Each result must distinguish gains over base, clean and generic adversarial training
from profile, history, peer, memory-necessity and transfer claims. Characters are
history-dependent frozen policies; learning is supervised adapter training on
character-conditioned data. There is no demonstrated co-evolution, optimized
game-theoretic equilibrium, autonomous exploration, coalition or general intelligence
merely from prompted utilities. All interpretations remain provisional for the author.

Implementation details fixed before calls: variants run in B0/B1/B2/B3 and C-single/C-peer/C-off order, with the original seed-plus-cumulative-call sampling rule. Call offsets are logged; random streams are predetermined but are not identical across conditions. The two severity actions were generated on their original collection histories and are replayed on the common clean state; this is not matched attack generation. Existing chronological outcomes known at design are enumerated in the supplement freeze. A fixed 15-minute available-budget gate is required before launching profiling.
