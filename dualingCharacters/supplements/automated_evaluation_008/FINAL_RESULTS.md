# Final measured results — author-review package

The fixed core cutoff is 2026-10-26T18:25:24.957430+00:00: **181/241 stages**, **37 completed 64-turn main evaluation cells**. The new stage completes the frozen automated sample and all **64 compatibility conversations**. Human semantic annotation was unavailable by author decision and was not collected; it is not a completion prerequisite. Historical forms remain unchanged. This is a bounded characterization, not completion of the original horizon/recovery/external grid.

## Actual execution

5,303 new local generation calls; 1.859042 reserved GPU-hours including loads, failed attempts and format repairs. Compatibility rollout: 2,816 calls, 0.103824 hours. No new training, paid model API, pod, human ratings, push, publication or submission was added by this stage. Model-time reservations, sampled utilization and pod uptime are distinct; the pod rate and billed uptime are unknown.

Final automated measurement consists of 80 held-out controls, 72 fixed archive events, 540 balanced broader archive opportunities and 32 controlled events **per model**, plus 36 fixed events under three probes per model. This is 1,664 final judgment tasks, excluding development and repairs. The 612 archive sample records represent 609 underlying opportunities, with three sampled in both separately reported populations. The broader sample has 15 unique families; the non-overlap sensitivity has 13. Generator seeds are not independently learned actors.

## Strongest measured findings

1. **Action channels change.** Across 150 unique paired families and three generator seeds, C3/C5/A1 each receive 10,800 opportunities (900 episodes). Direct edits are 5,408/477/938; recollections 828/4,618/1,397; proposals 969/1,930/4,830. C5−C3 edit rate is −45.66 percentage points, 95% family/seed interval [−48.20, −43.06]; recollection +35.09 [31.64, 38.67]. C5−A1 recollection is +29.82 [27.08, 32.66]. These are API frequencies, not deception or false-memory rates.

2. **Typed preferences persist, especially with fixed motives.** Repeated eligible direct slot/value transitions: C3 3,623/5,400; C5 4,831/5,224; A1 5,093/5,364. Matched family-mean C5−C3 is +25.39 points [22.22, 28.58]; C5−A1 is −2.48 [−4.30, −0.69]. Persistence is explicitly encouraged by the prompts; it does not establish flexible tactics or useful intent tracking. Immediate working-state changes are 3,830/286/562 per 10,800 opportunities; note changes are a separate mechanism.

3. **Compatible goals make matching easier; most matching was already present.** The complete controlled grid has 16 paired families and 128 reserved communication opportunities per arm. Compatible preferences produce 107 typed same-goal next actions versus zero under incompatibility; incompatible preferences produce 111 different-value/same-slot actions versus six. Matching difference (incompatible minus compatible): −83.59 points [−95.31, −69.53]. Of the 107 compatible matches, 77 already matched before delivery, 29 lack a prior recipient position and one had an untyped/other prior position. Neither arm shows a different-to-matching typed transition. This does not establish persuasion or a delivery effect.

Secondary controlled paired success is **5/16 versus 7/16**, a +12.5-point incompatible-minus-compatible difference [−12.5, 37.5]. Decisive-field correctness is 25/32 in each arm; preferred-option adoption is 196/384 versus 189/384. Equal counts do not establish equivalence. Fixed arm order, one stochastic rollout and different call-index random draws limit interpretation.

4. **Character training does not demonstrate superiority over generic training.** All completed C5 seeds exceed their untrained reference, but this does not identify a character-specific benefit. Original seed/family dependence and negative cells remain in the consolidated table.

| Model | Contrast | Difference (pp) | 95% interval (pp) | Seeds |
| --- | --- | --- | --- | --- |
| qwen | C5-C1 | +1.81 | [-8.47, +16.25] | [17, 29, 43] |
| qwen | C5-C3 | -3.89 | [-8.33, +0.14] | [17, 29, 43] |
| qwen | C5-A1 | +2.64 | [-2.50, +9.44] | [17, 29, 43] |
| phi | C5-C1 | +8.47 | [-2.08, +17.92] | [17, 29, 43] |
| phi | C5-C3 | -4.17 | [-9.72, +1.81] | [17, 29, 43] |

## Automated semantics: screening and uncertainty

Each assessor is reported separately. Phi is the primary different-family assessor and is not replaced when it fails. Passing a synthetic engineering threshold would not establish accuracy on compound research dialogue. Failed dimensions are retained as raw diagnostic classifications, not promoted to calibrated semantic prevalence.

**Phi** passed 0/7: none. Failed: recommendation, authorization_assertion, evidence_challenge, acknowledges_user_conflict, recipient_acknowledgment, recipient_response, citation_support.

**Qwen** passed 3/7: evidence_challenge, acknowledges_user_conflict, recipient_response. Failed: recommendation, authorization_assertion, recipient_acknowledgment, citation_support.

Full confusion matrices, supports, abstentions and invalid spans are in [JUDGE_CALIBRATION.md](JUDGE_CALIBRATION.md). The ancillary citation category permits blank quoted spans under the frozen validator; those cases are audited and the dimension is not treated as evidence-supported natural-dialogue measurement.

| Judge | Condition | Stratum | Authorization yes / all | No | Uncertain | Missing |
| --- | --- | --- | --- | --- | --- | --- |
| phi | A1 | communication | 14/90 | 0 | 54 | 22 |
| phi | A1 | direct | 19/90 | 1 | 43 | 27 |
| phi | C3 | communication | 24/90 | 4 | 46 | 16 |
| phi | C3 | direct | 27/90 | 0 | 34 | 29 |
| phi | C5 | communication | 19/90 | 0 | 48 | 23 |
| phi | C5 | direct | 42/90 | 0 | 22 | 26 |
| qwen | A1 | communication | 13/90 | 76 | 0 | 1 |
| qwen | A1 | direct | 7/90 | 82 | 0 | 1 |
| qwen | C3 | communication | 16/90 | 71 | 0 | 3 |
| qwen | C3 | direct | 10/90 | 80 | 0 | 0 |
| qwen | C5 | communication | 17/90 | 69 | 0 | 4 |
| qwen | C5 | direct | 14/90 | 72 | 0 | 4 |

These are classification rates, not verified authorization or false-authorization frequencies. A yes label can refer to a true assertion. Direct and communication strata have different sampling fractions and are not pooled. In each broader condition/stratum, 90 opportunities arise from 15 families × two worlds × three generator seeds.

| Condition | Stratum | Exact agreement / joint | Joint yes/no | Positive agreement | Negative agreement | Conservative annotation range |
| --- | --- | --- | --- | --- | --- | --- |
| A1 | communication | 10/67 | 14 | 83.3% | 0.0% | 11.1%–100.0% |
| A1 | direct | 8/62 | 20 | 53.8% | 14.3% | 7.8%–98.9% |
| C3 | communication | 19/71 | 26 | 81.1% | 53.3% | 16.7%–95.6% |
| C3 | direct | 9/61 | 27 | 50.0% | 0.0% | 10.0%–100.0% |
| C5 | communication | 11/63 | 18 | 75.9% | 0.0% | 12.2%–100.0% |
| C5 | direct | 9/61 | 41 | 36.0% | 0.0% | 10.0%–100.0% |

The conservative range runs from both-judge positives to all cases except both-judge negatives. It describes unresolved annotation under that rule, not all possible shared model error. Uncertainty and missingness remain separate. Exact agreement includes explicit uncertain/NA categories; positive/negative agreement uses only jointly substantive yes/no labels.

| Judge | Probe | Authorization labels changed / joint | Baseline missing | Probe missing |
| --- | --- | --- | --- | --- |
| phi | alias_permutation | 2/20 | 14 | 10 |
| phi | api_exposed | 0/18 | 14 | 13 |
| phi | category_order | 0/21 | 14 | 13 |
| qwen | alias_permutation | 1/35 | 1 | 1 |
| qwen | api_exposed | 1/35 | 1 | 1 |
| qwen | category_order | 1/34 | 1 | 2 |

Category order changes only the declared list, not the schema skeleton. Actual notes can retain API words despite selected-metadata masking. Numerical GPU variation is not separated by an extra unchanged replay. Probe calls are repeated measurements, not new subjects.

## What remains unsupported

No validated population semantic-frequency claim, human-level evaluator validity, deliberate deception, incompatible rivalry in the original separate-slot cast, causal message persuasion, broad exploration benefit, AGI, or long-horizon robustness follows from these results. The prior review001 delivery/no-delivery diagnostic remains pending at the cutoff. A compatibility manipulation tests a different factor. No human recruitment requirement is reintroduced.

## Inspect and reproduce

Read [EVIDENCE_INDEX.md](EVIDENCE_INDEX.md), [REPRODUCE.md](REPRODUCE.md), [CLAIM_TO_EVIDENCE.csv](CLAIM_TO_EVIDENCE.csv), the [dialogue appendix](DIALOGUE_APPENDIX.md), and the [fresh controlled exchange](CONTROLLED_DIALOGUE.md). The [anonymous paper](paper/manuscript.pdf) and [identified project copy](paper/author_review.pdf) are complete author-review drafts. Editable source and exact raw model outputs are supplied.

The required human decisions are scientific scope and conclusions, final authorship/anonymity, disclosure/policy compliance, and whether the bounded characterization is suitable for submission while the larger original campaign continues. No acceptance is promised. Software and packaging checks do not make semantic readings scientifically validated.
