# Exploratory follow-up: long-horizon intent robustness

This section is an author-review draft. The direction was specified after observing a negative initial three-character comparison and a reversal in clean-training performance across seeds. It is separate from the original confirmatory protocol.

We distinguish horizon robustness (change with conversation length), trajectory robustness (correct application and recovery throughout a conversation), and training robustness (variation between independent training seeds). Lower deterioration from a poor starting point does not establish useful robustness. We operationalize intent as goals, priorities, constraints, permissions, and revisions expressed in the available conversation, without claiming access to unexpressed human intentions.

The underlying intervention is character-conditioned data generation followed by supervised adapter training. Character-generator parameters are frozen; their private histories make behavior history-dependent. Retrieval is fixed, and primary evaluation removes antagonists. The method does not implement co-evolving character policies, autonomous exploration, or an optimized game-theoretic equilibrium.

## Existing-core observations

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
| 29 | A1 | 181/240 (75.42%) |
| 43 | C1 | 183/240 (76.25%) |
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

At the current incomplete grid, the C5-versus-clean comparison changes direction between seeds17 and29. The corresponding C5-versus-generic-adversary differences are negative at both completed seeds. These single-seed family intervals neither establish equivalence nor quantify variation over training seeds. The untrained reference is shared, not replicated for each comparison.

Dynamic-oracle analysis scores each actual64-turn response against the then-active task state, keeping initial errors, authorized changes, ambiguous requests, and regressions distinct.

| Condition | Seed | All-turn correctness | Final-quarter correctness | Never correct /480 | Unresolved final /480 |
|---|---|---|---|---|---|
| C1 | 17 | 31.86% | 15.48% | 55 | 90 |
| C1 | 29 | 30.95% | 14.70% | 67 | 167 |
| C1 | 43 | 32.32% | 14.82% | 55 | 90 |
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

The complete32/64/128 horizon grid is pending. Consequently, the newly proposed method-by-horizon interaction and absolute128-turn differences have not been measured. Existing trajectory associations do not establish causal recovery from matched disrupted states.

A subsequent temporal source audit found that source coverage changes strongly with the scripted current request. The following selected-turn counts are descriptive and do not identify a causal effect of retrieval.

| Condition | Seed | Turn | All canonical sources /480 | Correct incoming memory /480 | Reverted to initial state /480 | Task correct /480 |
|---|---|---|---|---|---|---|
| C1 | 17 | 60 | 0 | 0 | 480 | 0 |
| C1 | 17 | 61 | 480 | 0 | 0 | 406 |
| C1 | 29 | 60 | 0 | 6 | 464 | 4 |
| C1 | 29 | 61 | 474 | 6 | 3 | 351 |
| C1 | 43 | 60 | 0 | 1 | 468 | 1 |
| C1 | 43 | 61 | 477 | 1 | 2 | 407 |
| C3 | 17 | 60 | 0 | 210 | 163 | 177 |
| C3 | 17 | 61 | 480 | 210 | 0 | 390 |
| C3 | 29 | 60 | 0 | 0 | 476 | 0 |
| C3 | 29 | 61 | 480 | 0 | 0 | 406 |
| C5 | 17 | 60 | 0 | 1 | 476 | 1 |
| C5 | 17 | 61 | 468 | 1 | 6 | 392 |
| C5 | 29 | 60 | 0 | 0 | 480 | 0 |
| C5 | 29 | 61 | 477 | 0 | 1 | 404 |

Several adapters repeatedly returned initial commitments during the intervening period, then recovered approved revisions when their sources reappeared. A flat incorrect trajectory is not stability, and final-turn accuracy alone is not long-horizon preservation. The policy and benchmark remain frozen.

## Fresh intent-transfer design, pending execution

We prepared16 authored scenario families across software/product work, research collaboration, editorial work, and operator assistance. Each has two authorization worlds and16-,64-,128-turn versions, preserving decisive events while adding supporting task work. Outputs are substantive proposals, research-plan paragraphs, edited passages, or operational recommendations. A private time-indexed intent ledger grounds evaluator judgments in visible user spans and allows multiple valid responses. It is never passed to the policy or used for retrieval.

All fixed final Qwen C1/C3/C5 adapters use one common natural-language response and bounded free-text-memory interface. This differs from their structured training interface and is therefore a transfer limitation to test, not hide. Feasible complete tiers are selected only from disjoint engineering timing under the separate two-hour subcap, core/review priority, project96-hour ceiling, and single session deadline. No new parameter training is performed.

The new primary endpoint normalizes0–4 adherence ratings, averages the final three observations within each world, takes the lower paired-world average within family, and then averages matched families and declared seeds. The primary contrast is the C5-versus-C3 difference in128-minus16 change; C5-versus-C1 and absolute128-turn performance are mandatory practical comparisons. Helpful task progress is rated separately. Human ratings, disagreement, and any adjudication remain distinct. No model-generated or synthetic annotation is presented as human validation.

## Limits and provisional interpretation

The original benchmark shares a six-slot schema across domain framings, and its ambiguous families are confounded with the creative domain and held-out rule. The new benchmark introduces free-text artifacts but still uses authored scripts and a common16-phase skeleton. Longer trajectories under fixed retrieval are not full-transcript attention tests. Few training seeds provide limited uncertainty about seed variation. Supervised target exposure and recovery concentration can differ despite common input-token budgets; observed associations do not identify their causal effects.

Fresh qualitative scores remain pending. A future positive interaction with lower absolute128-turn performance would support reduced degradation at these tested horizons, not superior long-horizon usefulness. No advantage would remain evidence about these fixed adapters and the specified interface. Narrative, persistence, rivalry, and peer-interaction explanations require their own controls. All scientific interpretations remain provisional for the human author.
