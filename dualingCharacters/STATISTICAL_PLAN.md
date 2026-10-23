# Confirmatory specification prepared before test access

This document becomes frozen only when `configs/freeze.json` records its hash
and the completed pilot gates. This is an internal, timestamped preregistration;
no public registration or third-party certification is claimed. The author's
brief supplies H1–H5. Implementation choices below remain visible for author review.

## Estimand and hypotheses

The primary estimand is the mean C5 minus C3 difference in antagonist-free paired
task success over the common scenario families and independent training seeds.
A family succeeds only when both the authorized-change and hypothetical-change
conversation produce correct final executable decisions and required clarification.
Memory recall and source-reference accuracy do not substitute for behavioral success.

H1 tests C5 versus C3. H2 examines C5 versus A2 (private history) and A3 (peer
interaction). H3 examines legitimate-update acceptance separately from false
acceptance of hypothetical changes; the paired endpoint penalizes blanket resistance.
No formal noninferiority margin or proof of no regression is claimed from an
insignificant difference. H4 compares two, three and five at this fixed resource
budget; a single budget does not establish a general compute-scaling law. H5 uses
the C5 versus A1 motive-only contrast. Narrative, persistence and relationship
claims require the corresponding controls, not merely a positive H1 estimate.

## Fixed grid and information boundaries

Primary backbone: pinned Qwen3-4B-Instruct-2507. Qwen conditions C1–C6 and A1–A3
each use training seeds 17, 29 and 43. Independent-family replication uses pinned
Phi-4-mini-instruct with C1/C3/C5 and those same three independent training seeds.
The untrained scaffold is evaluated once per family/model under greedy decoding;
its repeated use is not counted as independent training replication.

All conditions share BF16 rank-8 all-linear LoRA, alpha 16, dropout zero, AdamW,
gradient clipping 1.0, the implemented common warmup/cosine schedule, and final
fixed-token checkpoint selection. Each of two rounds has 256 optimizer steps of
4096 nonpadding input tokens: 2,097,152 input tokens per condition/seed. Target
tokens, discarded orphaned suffix labels, unique examples and reuse are reported
separately. Block-diagonal attention isolates packed examples. AdamW and the same
schedule restart in round two; adapter weights continue from round one.

Round one collects 150 training families at 16 turns, selecting turns 6, 9 and 16.
Round two uses the other 150 families at 32 turns, selecting turns 6, 17 and 32.
Both worlds yield 1800 attempted windows per condition/seed. Each round has the
same maximum 128 stochastic recovery attempts; all eligible remaining failures
use the same deterministic teacher. Eligibility requires that every gold source
reference was actually retrieved. The 50:50 clean/recovery window stream is common;
an empty pool stops the stage. Oracle information is only training supervision or
offline scoring, never retrieval hints, working-memory refreshes or test corrections.

Character-generator weights remain frozen when the defender is refreshed.
Profiles, aliases and proposal ownership persist within an episode; private
histories reset between episodes. Twelve common opportunities include four
communication slots. More characters divide the same opportunities. Random
corruption passes in communication slots and has eight possible edits. Actual
tokens and generation time are reported; caps are not exact FLOP matching.

## Test sample and secondary settings

The locked primary set has 240 families, each with two conversations, at 64 turns.
Four domains have 60 families each. The withheld conditional dependency is crossed
with domain, 30 families in each structural cell per domain. Event/software are
training domains; research/creative have new framing but the same categorical task
schema. General domain transfer is therefore a limited claim.

One turn is one new user message followed by a generated public assistant response.
Each episode also has one immutable scripted prior assistant proposal, index zero.
Primary 64-turn episodes thus contain 129 source messages, 64 defender calls and
64 memory updates. The user script is not adaptive. The initial suggestion is not
a binding decision; only attributed user authorizations change the private oracle.

Primary retrieval is eight lexical selections plus four recent messages, deduplicated,
with a 4096 input-token cap and bounded six-field memory. No silent truncation is
allowed. All antagonists are absent in primary evaluation. Greedy answer decoding
uses a common public output schema and 256-token maximum; schema constraints encode
legal fields and options, never which decision is correct.

Forty-eight families are selected before outcomes by the lowest identifier hashes,
six in each domain × structural-pattern cell. The same families form these settings:

- 32/128-turn sensitivity: Qwen base and C1/C3/C4/C5, seed 17 only; compare with
  those same families and seed at 64 turns. This scope reduction preserves three
  seeds for every main condition and essential trained ablation.
- Clean 16-turn regression and identical-state recovery: Qwen base once and
  C1/C3/C4/C5 with all three training seeds.
- Larger retrieval (16 + 8, 8192 input-token cap) and unfamiliar bounded cache
  carryover faults: Qwen base and C1/C3/C4/C5, seed 17. This is not full-history
  evaluation or an exhaustive unseen-character study.

Recovery reuses the base Qwen observation at turn 32 of each 64-turn scenario,
erasing site and its reference without reading the oracle. Every method receives
identical damaged memory and actually retrieved sources. Four attempts each have
one separate diagnosis call and one repair call; diagnosis is not fed into repair.
Report cumulative recovery and detection, all unrecovered cases, and the full
denominator. No successful-cases-only repair-time comparison is permitted.

External validation uses the preselected 50 LongMemEval cleaned-S IDs and pinned
original rubric. Retrieval and a small cross-family judge are documented adaptations;
the scores are exploratory and not official comparable benchmark results. Judge
calibration uses 40 positive/40 negative programmatically scored pilot outputs.
A balanced accuracy ≥.85 and specificity ≥.80 are required even for descriptive
acceptance, and do not establish validity for open-ended memory QA. Human agreement
is pending. No external answers enter training or the evaluated policy prompt.

Natural-language validation uses 20 unseen paired families (40 conversations) for
Qwen C1/C3/C5 seed 17. Each public assistant response is generated prose, with a
separate internal structured memory action; only prose enters the conversational
transcript. The final 120 outputs form a randomized blinded packet with a fixed
rubric and two blank rater forms. The author requested raters later. No human scores
or adjudication will be invented. This remains synthetic, scripted-user validation.

## Inference and precision

Use paired two-way bootstrap resampling of training seeds and scenario families,
preserving methods and paired worlds within a cell, with 10,000 draws and fixed
analysis seed 90210. Report absolute effects, percentile 95% intervals, every seed's
result and seed standard deviation. Three seeds cannot characterize the population
of training outcomes reliably. Turns, paraphrases and paired worlds are not extra
independent subjects. The implementation's family sign-flip test is conditional on
the observed seeds, not a test over an adequately sampled seed population.

The prespecified Qwen secondary comparison family is C5−C1, C5−C2, C5−C4, C5−C6,
C5−A1, C5−A2 and C5−A3; apply Holm correction to its conditional paired p-values.
The primary C5−C3 contrast is separate. Phi C5−C3 is the independent-family check;
Phi C5−C1 is a secondary reference. Other metric rates, horizon effects, failure
taxonomies and subgroup interpretations are descriptive/exploratory, not new
unadjusted confirmatory successes.

The 16-family pilot had paired discordance .3125. The design simulation varies
discordance, seed standard deviation and family sharing, using a practically
meaningful five-point effect without assuming it exists. Under the explicitly
assumed 70% shared-uniform mechanism and zero seed shift, 240 families detect a
five-point effect only about 30% of the time; nonzero seed variation weakens this.
The calculation is sensitivity analysis, not a guarantee. Retain 240 families to
preserve all three-seed controls and independent-model confirmation within the
resource ceiling. A null result must not be called evidence that a five-point
benefit is absent. No sample or endpoint may be changed using test significance.

## Exclusions, stopping and accounting

Malformed or capped outputs count as failures, never exclusions. All paired worlds
are required; missing conversations stop aggregation. Infrastructure failures retain
their logs, consumed compute and fresh audited resume IDs. Only condition-blind
corrupt-input decisions can exclude a family, with a recorded reason applied to
every method. Completed runs cannot be replaced through the resume mechanism.

No checkpoint, condition, seed or family is selected by test outcomes. The hard
ceiling is 96 reserved GPU-hours including all pilots and failures. The measured
allocation is in `configs/study_plan.json` and `reports/tables/workload_forecast.json`.
This is a ceiling, not a spending target. An unfinished grid at the ceiling is an
incomplete study. Actual price is unknown, so dollar cost remains unknown. Pod
observed wall time, reservation time, sampled utilization, token counts and VRAM
are distinct measurements. Checkpoints and raw outputs are mirrored locally;
lossless compression preserves exact bytes and archived hashes.
