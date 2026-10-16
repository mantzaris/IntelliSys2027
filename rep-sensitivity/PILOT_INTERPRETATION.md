# Pilot interpretation: absolute outcomes and observable failure locations

Exploratory reanalysis of immutable `pilot-v7` outputs; no new model calls. The original protocol and audit remain intact.

The complete pilot contains 24 independent base pairs (12 scheduling and 12 secondary workflow), 1152 trajectories and 2304 calls. All results below are Qwen3-14B BF16, non-thinking, with the original fixed settings.

Each scheduling hierarchical condition has 96 trajectories: 12 bases × two worlds × two policies × two stochastic repetitions. The 13.54-point result compares exact copies with single presentation, averaging matched cells within a base, then giving each base equal weight. It pools ordinary synthesis and checklist, both worlds, and both repetitions. The selected report was frozen before evaluation, correct in both worlds, and unchanged across the pair. It was not chosen to favor the correct answer.

| Population / organization / condition | Single accuracy % | Repeated accuracy % | Difference pp [95% cluster interval] | Bases | Trajectories, both arms | Improve / regress / unchanged |
|---|---:|---:|---|---:|---:|---|
| schedule / flat / exact | 100.00 | 100.00 | 0.00 [0.00, 0.00] | 12 | 192 | 0 / 0 / 96 |
| schedule / flat / paraphrase | 100.00 | 100.00 | 0.00 [0.00, 0.00] | 12 | 192 | 0 / 0 / 96 |
| schedule / hierarchical / exact | 81.25 | 94.79 | 13.54 [4.17, 22.92] | 12 | 192 | 14 / 1 / 81 |
| schedule / hierarchical / paraphrase | 81.25 | 91.67 | 10.42 [1.04, 19.79] | 12 | 192 | 12 / 2 / 82 |
| workflow / flat / exact | 87.50 | 85.42 | -2.08 [-4.17, 0.00] | 12 | 192 | 0 / 2 / 94 |
| workflow / flat / paraphrase | 87.50 | 89.58 | 2.08 [0.00, 4.17] | 12 | 192 | 4 / 2 / 90 |
| workflow / hierarchical / exact | 81.25 | 83.33 | 2.08 [-3.12, 7.29] | 12 | 192 | 5 / 3 / 88 |
| workflow / hierarchical / paraphrase | 81.25 | 85.42 | 4.17 [-2.08, 10.42] | 12 | 192 | 5 / 1 / 90 |

Policy and task strata (hierarchical scheduling):

| Stratum | Repeat | Single % | Repeated % | Difference pp [95% interval] | Bases | Improved / regressed / unchanged |
|---|---|---:|---:|---|---:|---|
| checklist | exact | 81.25 | 93.75 | 12.50 [2.08, 22.92] | 12 | 6 / 0 / 42 |
| checklist | paraphrase | 81.25 | 87.50 | 6.25 [-4.17, 16.67] | 12 | 4 / 1 / 43 |
| ordinary | exact | 81.25 | 95.83 | 14.58 [2.08, 27.08] | 12 | 8 / 1 / 39 |
| ordinary | paraphrase | 81.25 | 95.83 | 14.58 [2.08, 27.08] | 12 | 8 / 1 / 39 |
| dependency | exact | 87.50 | 96.88 | 9.38 [6.25, 12.50] | 4 | 3 / 0 / 29 |
| dependency | paraphrase | 87.50 | 96.88 | 9.38 [6.25, 12.50] | 4 | 3 / 0 / 29 |
| identity | exact | 90.62 | 87.50 | -3.12 [-6.25, 0.00] | 4 | 0 / 1 / 31 |
| identity | paraphrase | 90.62 | 90.62 | 0.00 [0.00, 0.00] | 4 | 0 / 0 / 32 |
| numeric | exact | 65.62 | 100.00 | 34.38 [6.25, 62.50] | 4 | 11 / 0 / 21 |
| numeric | paraphrase | 65.62 | 87.50 | 21.88 [-6.25, 50.00] | 4 | 9 / 2 / 21 |
| deadline_downtime | exact | 87.50 | 95.83 | 8.33 unavailable (small strata) | 3 | 2 / 0 / 22 |
| deadline_downtime | paraphrase | 87.50 | 91.67 | 4.17 unavailable (small strata) | 3 | 2 / 1 / 21 |
| objective | exact | 66.67 | 100.00 | 33.33 unavailable (small strata) | 3 | 8 / 0 / 16 |
| objective | paraphrase | 66.67 | 100.00 | 33.33 unavailable (small strata) | 3 | 8 / 0 / 16 |
| precedence_release | exact | 75.00 | 83.33 | 8.33 unavailable (small strata) | 3 | 3 / 1 / 20 |
| precedence_release | paraphrase | 75.00 | 79.17 | 4.17 unavailable (small strata) | 3 | 1 / 0 / 23 |
| resource | exact | 95.83 | 100.00 | 4.17 unavailable (small strata) | 3 | 1 / 0 / 23 |
| resource | paraphrase | 95.83 | 95.83 | 0.00 unavailable (small strata) | 3 | 1 / 1 / 22 |

Exact-copy base means are positive for 6 bases, negative for 1, and zero for 5. The largest contributor is `e765f8bb5f0e2aad`: seven of the 14 improved cells. Leaving that base out gives 6.82 pp. Across all single-base omissions the estimate ranges from 6.82 to 15.91 pp. This is descriptive sensitivity, not another significance search. Per-base values and every omission are in `analysis.json`.

The bootstrap resamples whole bases within mutation-family × decision-change strata; it retains dependent worlds, policies and stochastic repetitions. The fixed stratum composition is part of the estimand. Singleton-stratum intervals are withheld. Flat scheduling is at a ceiling in this pilot; a zero-width empirical interval does not establish robustness.

Paired-world success requires both answers to be correct. Changing an answer or keeping it stable alone is insufficient.

| Scheduling hierarchy | Repeat | Both correct, single % | Both correct, repeated % | Difference pp [95% interval] | Bases | Matched world-pairs |
|---|---|---:|---:|---|---:|---:|
| Harmless | exact | 79.17 | 95.83 | 16.67 [0.00, 33.33] | 6 | 24 |
| Harmless | paraphrase | 79.17 | 91.67 | 12.50 [-8.33, 33.33] | 6 | 24 |
| Consequential | exact | 66.67 | 87.50 | 20.83 [8.33, 33.33] | 6 | 24 |
| Consequential | paraphrase | 66.67 | 79.17 | 12.50 [8.33, 16.67] | 6 | 24 |

Observable labels below have 96 trajectories per column. Labels overlap and are not causal categories. A correct choice may coexist with an omitted fact or an erroneous supporting assertion.

| Observation | Single | Exact | Paraphrase |
|---|---:|---:|---:|
| Necessary proposition absent | 3 | 6 | 6 |
| Necessary value wrong or conflicted | 16 | 2 | 5 |
| Invalid choice despite delivered failed constraint | 1 | 1 | 1 |
| Feasible but not preferred | 12 | 1 | 3 |
| Correct choice with erroneous support | 15 | 13 | 12 |
| Response-contract failure | 0 | 0 | 0 |

A key binds entity, predicate, criterion parameters, units, applicability and version in the public registry. Values must match at that key. Free-text rationale is not scored as an internal reasoning path. A wrong key with the same number does not preserve the original proposition. Citation mismatch is measured separately.

Deterministic labels refer to explicit keyed assertions and observable decisions. Attribution to attention, arithmetic, implicit scope confusion or causal mediation requires independent annotation/intervention; no such causal label is inferred here.

No pilot output was truncated or contract-invalid. Numerical objective errors and omissions are visible, but this pilot alone cannot assign the aggregate accuracy gain to transmission versus root application. A baseline root also makes a wrong decision after receiving enough correct information. Lossless and bypass interventions test this distinction directly; their completion status and results are reported separately in `records/mechanism-report-status.json` and the manuscript extension section.

The frozen development extension already covers exact/paraphrase copying, selective/uniform emphasis, false visible assertions, same-input scope differences, branch/padding/position controls, summary bypass, deterministic transport and call-matched global reviewers. A separately versioned root-only diagnostic fills the gap for numerical objectives, covering every candidate rather than selecting only favorable or correct-choice objectives. It will run after the protected original evaluations. Additional boundary investigations are not selected before the core extension finishes.

Machine-readable evidence: `results/pilot-interpretation-v2/analysis.json`, `accuracy.csv`, `paired-world.csv`, `failure-locations.csv`. Detailed trajectory annotations are locally mirrored/derived in ignored `artifacts/analyses/pilot-interpretation-v2/`. Reproduce with `scripts/interpret_pilot.py` and `scripts/build_pilot_interpretation.py`.
