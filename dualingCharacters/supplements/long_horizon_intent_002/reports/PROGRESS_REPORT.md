# Intent 002 progress — 2026-10-24T14:43:55.404057+00:00

This is an exploratory follow-up specified after the initial negative C5 comparison and C1 seed reversal. It preserves the original confirmatory study and review_001 freezes. Newly inspected test analyses are not original preregistration.

Session: 2026-10-24T13:06:05+00:00 to 2026-10-24T21:06:05+00:00; useful-work cutoff 2026-10-24T20:36:05+00:00. The single elapsed-time budget is eight hours. No intent worker is left waiting to launch after that deadline.

## Existing core: completed and running

Latest monitor 2026-10-24T14:43:33.173833+00:00: 49/241 stages complete; active `main-qwen-a1-29-r1-collect`. The existing controller retains ownership. Results below contain only completed, eligible, fully validated paired evaluations.

| Qwen seed | Condition | 64-turn paired success |
|---|---|---|
| 17 | C1 | 186/240 (77.50%) |
| 17 | C3 | 177/240 (73.75%) |
| 17 | C4 | 179/240 (74.58%) |
| 17 | C5 | 168/240 (70.00%) |
| 17 | A1 | 169/240 (70.42%) |
| 29 | C1 | 138/240 (57.50%) |
| 29 | C3 | 181/240 (75.42%) |
| 29 | C4 | 165/240 (68.75%) |
| 29 | C5 | 180/240 (75.00%) |
| 29 | A1 | Pending |
| 43 | C1 | Pending |
| 43 | C3 | Pending |
| 43 | C4 | Pending |
| 43 | C5 | Pending |
| 43 | A1 | Pending |

| Contrast | Seed | Difference, pp | Family 95% interval, pp | Both | Only C5 | Only control | Neither |
|---|---|---|---|---|---|---|---|
| C5-C3 | 17 | -3.75 | [-8.33, 0.83] | 157 | 11 | 20 | 52 |
| C5-C3 | 29 | -0.42 | [-2.50, 1.67] | 177 | 3 | 4 | 56 |
| C5-C1 | 17 | -7.50 | [-11.25, -4.17] | 167 | 1 | 19 | 53 |
| C5-C1 | 29 | 17.50 | [11.67, 23.33] | 129 | 51 | 9 | 51 |

One-seed intervals resample240 scenario families, preserving both worlds. They exclude training-seed uncertainty. A zero-containing interval is not equivalence. The frozen three-seed procedure and multiplicity treatment are retained for completed planned seed sets. C5–C1 remains alongside C5–C3; no favorable seed or checkpoint is selected.

## Different robustness questions

Horizon robustness: 5/15 existing model/horizon cells complete, including base and C4. The48 family identities preserve decision/event semantics across32/64/128; early events are not uniformly phase-scaled. Missing short/long cells prevent the proposed interaction estimate. A128-turn prefix is not a32-turn experiment.

Trajectory robustness: the table uses all480 conversations at every actual turn against its current oracle. These are structured decisions, not human-rated natural-language intent or helpfulness.

| Condition | Seed | All-turn correctness | Final-quarter correctness | Never correct /480 | Unresolved final /480 |
|---|---|---|---|---|---|
| C1 | 17 | 31.86% | 15.48% | 55 | 90 |
| C1 | 29 | 30.95% | 14.70% | 67 | 167 |
| C3 | 17 | 54.77% | 46.65% | 55 | 99 |
| C3 | 29 | 31.44% | 16.21% | 55 | 98 |
| C5 | 17 | 31.52% | 16.65% | 56 | 118 |
| C5 | 29 | 31.85% | 16.55% | 55 | 101 |

| Contrast | Seed | Mean all-turn difference, pp | Family 95% interval, pp |
|---|---|---|---|
| C5-C3 | 17 | -23.25 | [-26.26, -20.25] |
| C5-C1 | 17 | -0.34 | [-0.71, 0.05] |
| C5-C3 | 29 | 0.41 | [0.09, 0.76] |
| C5-C1 | 29 | 0.90 | [-0.14, 1.99] |

C5 does not exhibit a consistent trajectory advantage in these completed seeds. Endogenous error episodes cannot substitute for the frozen identical-faulty-state recovery experiment. Initially incorrect and never-correct conversations remain in unconditional denominators.

A temporal source audit was added after inspecting these curves. It characterizes saved prompts after generation; no gold annotation selected the policy inputs. The following comparison illustrates a late recovery of source access, with no claim that source access alone caused the behavioral change.

| Condition | Seed | Turn | All canonical sources /480 | Correct incoming memory /480 | Reverted to initial state /480 | Task correct /480 |
|---|---|---|---|---|---|---|
| C1 | 17 | 60 | 0 | 0 | 480 | 0 |
| C1 | 17 | 61 | 480 | 0 | 0 | 406 |
| C1 | 29 | 60 | 0 | 6 | 464 | 4 |
| C1 | 29 | 61 | 474 | 6 | 3 | 351 |
| C3 | 17 | 60 | 0 | 210 | 163 | 177 |
| C3 | 17 | 61 | 480 | 210 | 0 | 390 |
| C3 | 29 | 60 | 0 | 0 | 476 | 0 |
| C3 | 29 | 61 | 480 | 0 | 0 | 406 |
| C5 | 17 | 60 | 0 | 1 | 476 | 1 |
| C5 | 17 | 61 | 468 | 1 | 6 | 392 |
| C5 | 29 | 60 | 0 | 0 | 480 | 0 |
| C5 | 29 | 61 | 477 | 0 | 1 | 404 |

At these tested turns, later explicit requests can retrieve current authorizing messages that ordinary intervening requests omit. A strong final response therefore does not establish preservation throughout the trajectory. The fixed lowest-ID paired example and complete source-coverage curves are saved under the source-dynamics audit; no retriever or memory rule was changed.

Training robustness: `matched_seed_description.json` uses only seeds shared by C1/C3/C5. Values, range, and sample SD are descriptive; they neither establish a population robustness property nor conversational stability. Flat low performance is not useful robustness.

## Clarification and source-reference audits

| Condition | Seed | Original flag /480 | Unnecessary | Missed necessary | Wrong issue | Unnecessary + settled nulls |
|---|---|---|---|---|---|---|
| C1 | 17 | 12 | 3 | 6 | 0 | 3 |
| C1 | 29 | 104 | 101 | 4 | 2 | 99 |
| C3 | 17 | 23 | 16 | 7 | 1 | 15 |
| C3 | 29 | 8 | 1 | 7 | 1 | 1 |
| C5 | 17 | 23 | 16 | 7 | 0 | 16 |
| C5 | 29 | 9 | 1 | 8 | 1 | 0 |

Clarification flags overlap. Wrong-issue cases can be both unnecessary and missed. Settled-decision nulling is a structured behavioral proxy for abandoning executable work, not a judgment about hidden intention or prose acknowledgment of uncertainty. Duplicate/order-only flags remain separate in the machine table.

| Condition | Seed | Original source error /480 | Canonical mismatch /2880 | Assistant /2880 | Unavailable /2880 | Nonexistent/future /2880 | Wrong explicit user /2880 | Anaphoric /2880 |
|---|---|---|---|---|---|---|---|---|
| C1 | 17 | 47 | 49 | 6 | 21 | 0 | 8 | 2 |
| C1 | 29 | 27 | 28 | 0 | 0 | 0 | 27 | 0 |
| C3 | 17 | 243 | 292 | 154 | 242 | 1 | 12 | 2 |
| C3 | 29 | 178 | 190 | 25 | 80 | 0 | 15 | 17 |
| C5 | 17 | 46 | 47 | 3 | 9 | 0 | 34 | 6 |
| C5 | 29 | 29 | 29 | 2 | 3 | 0 | 20 | 5 |

Reference counts have2880 slot references, while the original source-error denominator is480 conversations. Categories overlap. Unavailable references are distinct from nonexistent references and assistant authorship. Possible anaphoric user support is not automatically rescored. Actual examples and canonical source spans appear in `semantic_source_examples.json`.

## Actual supervised exposure

19 completed fits have exact loss-mask and sampler reconstruction. Common input-token budgets do not imply equal supervised-target tokens, example diversity, or recovery exposure.

| Condition | Seed | Round | Nonempty recovery pool | Loss-contributing unique | Occurrences | Completion target tokens | Top-5 share |
|---|---|---|---|---|---|---|---|
| C1 | 17 | 0 | 30 | 25 | 32 | 2148 | 31.4% |
| C1 | 17 | 1 | 10 | 10 | 258 | 17131 | 51.8% |
| C1 | 29 | 0 | 30 | 27 | 33 | 2240 | 30.7% |
| C1 | 29 | 1 | 17 | 17 | 361 | 23664 | 34.6% |
| C3 | 17 | 0 | 32 | 19 | 19 | 1279 | 27.2% |
| C3 | 17 | 1 | 33 | 33 | 315 | 20679 | 17.3% |
| C3 | 29 | 0 | 29 | 22 | 23 | 1520 | 27.4% |
| C3 | 29 | 1 | 17 | 17 | 226 | 14987 | 35.0% |
| C5 | 17 | 0 | 30 | 18 | 21 | 1433 | 38.7% |
| C5 | 17 | 1 | 31 | 31 | 299 | 19729 | 20.8% |
| C5 | 29 | 0 | 30 | 22 | 32 | 2158 | 31.8% |
| C5 | 29 | 1 | 9 | 9 | 269 | 17857 | 63.0% |

These target tokens count whole supervised completions in the nonempty-clarification class, not just the clarification field. Unique loss-contributing examples, repeated occurrences, orphaned suffix masking, and resume replay are separate. Full teacher-versus-verified-recovery label totals are in `supervision_exposure.json`; loaded buffer contents are not counted as loss exposure. Curriculum/outcome associations are noncausal.

All currently loss-contributing necessary-clarification targets come from these original training domains: software. Their exact turn, event type, label source, family IDs, and largest repeated-example shares are in `clarification_training_situations.json` and `clarification_top_examples.json`. This original training confound is retained; the fresh benchmark crosses ambiguity with all four domains.

## Fresh qualitative benchmark and execution readiness

Sixteen authored families (four per practical domain), paired authorization worlds, and matched16/64/128-turn scripts are implemented with private time-indexed ledgers and exact user-source spans. Four disjoint engineering cases test the common response/free-text-memory interface. The16-phase event template is controlled but synthetic and structurally limited.

The shared public interface uses4096 input tokens,640 combined output tokens,128 memory tokens, fixed lexical retrieval8 plus4 recent messages, greedy BF16 inference and batch limit32. The policy alone writes memory; evaluator state and corrections never enter its prompts. Offline tokenizer checks are not GPU validation of this transfer interface.

Fresh score status: **pending_outputs_and_human_ratings**. Intent reserved GPU time: 0.0 seconds. Admission reasons: required_core_incomplete, review001_not_resolved, extension_disabled. No qualitative performance result, crossover, or new robustness advantage is claimed.

Human status: pending_fresh_outputs. Two independent rating forms remain blank until actual humans provide ratings. The complete grid and balanced sample are different workloads. Earlier60-action identities/forms remain preserved; the original120-prose packet awaits its required natural outputs. No one was contacted.

## Resources and next action

Latest reconciled project reservation: 23.0570/96hours. Core forecast: expected 79.89, conservative 88.24 total reserved hours. Review and intent each have separate cumulative2-hour subcaps within96; at least0.5hours contingency is retained. These forecasts are not guarantees. Pod elapsed time and sampled utilization are recorded separately in `LATEST_STATE.json`; actual dollar rate remains unknown.

Required core → review_001 → intent_002 → older unseen-profile work. This session does not expand the96-hour ceiling. New intent work requires the completed core and review gates, a fixed-final-checkpoint binding, timing-only complete-tier allocation, free shared locks, remaining allowance, and this session’s deadline. If gates stay closed, leave intent disabled for a subsequent authorized continuation.

## Reviewable package

[Figures](INTENT_FIGURES.md), [claims](CLAIM_TO_EVIDENCE.md), [illustrative core appendix](ILLUSTRATIVE_APPENDIX.md), [new protocol](../PROTOCOL.md), [dataset card](../DATASET_CARD.md), [rubric](../RUBRIC.md), [reproduction](../README.md). No manuscript is presented as a compliant finished submission; scientific arguments and conclusions require human author review.
