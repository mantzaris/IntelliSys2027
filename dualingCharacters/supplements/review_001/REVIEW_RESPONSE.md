# Review response 001 — exploratory, author review pending

Generated 2026-10-24T01:54:54.203540+00:00. 16/241 original stages completed. All 58 frozen files pass their hashes. Core state: `main-qwen-c4-17-eval`. Recorded reservation time: 10.564155/96 hours (a running stage's final duration is not yet known). Rate and dollar cost remain unknown.

The diagnostics were designed after C1 and the available C3 seed-17 result were inspected. Existing-test analyses are exploratory. The original frozen tables, endpoint, seed list, checkpoint choices and exclusions remain intact. No new model call is authorized before all core stages complete and the shared lock is released.

## Findings independently recomputed

| finding | status | observed | review_snapshot |
| --- | --- | --- | --- |
| paired_success | verified | [186, 67] | [186, 67] |
| rule_strata | verified | [117, 69] | [117, 69] |
| failed_dependency_recall | verified | [90, 80, 81] | [90, 80, 81] |
| canonical_source_visibility | verified | 471 | 471 |
| distinct_owned_slots | verified | [900, 900] | [900, 900] |
| final_c5_peer_diagnostics | verified | [64, 0, 0] | [64, 0, 0] |
| ambiguity_confounded | verified | [30, True] | [30, True] |
| historical_severity | verified | [50, 243, 10, 241] | [50, 243, 10, 241] |
| c1_refresh_failed_pool | verified | 14 | 14 |
| amended_forecast_rounded | verified | 92.74 | 92.74 |

Exact raw paths and SHA256 hashes are in `results/cpu_provenance.json`. Historical mechanism/severity pilots are separate from eligible main evidence; excluded serialization/leakage runs are listed there and retain all artifacts and costs. The 92.74-hour figure is the historical amended forecast, not an updated estimate or consumed time.

## Current completed main evaluations

| run_id | paired_successes | families | failed_conversations | failed_with_dependency_error | failed_with_correct_recall | all_canonical_sources_visible |
| --- | --- | --- | --- | --- | --- | --- |
| base-qwen-eval | 67 | 240 | 285 | 245 | 239 | 444 |
| main-qwen-c1-17-eval-format2 | 186 | 240 | 90 | 80 | 81 | 471 |
| main-qwen-c3-17-eval | 177 | 240 | 99 | 78 | 94 | 468 |

| contrast | families | paired_difference | ci95_low | ci95_high |
| --- | --- | --- | --- | --- |
| C1-base | 240 | 0.49583333333333335 | 0.42916666666666664 | 0.5583333333333333 |
| C3-base | 240 | 0.4583333333333333 | 0.3875 | 0.5291666666666667 |
| C3-C1 | 240 | -0.0375 | -0.075 | 0.0 |

Differences and 95% family-bootstrap intervals above concern one fixed seed only and are exploratory; they do not estimate training-seed variability.

These are recomputations of completed runs, not supplementary model outcomes. Counts do not by themselves establish a C5 benefit or any mechanism. The main primary effect requires the frozen C5 versus C3 seeds and paired hierarchical analysis. C1's better performance than the untrained reference is a clean-training result.

## Supervision and severity

| run_id | pool | eligible_windows | loaded_unique_windows | loss_contributing_unique_windows | loss_contributing_unique_families | loss_contributing_occurrences | target_tokens | top5_token_share |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| main-qwen-c1-17-r0-fit-format2 | clean | 486 | 486 | 367 | 102 | 367 | 24390 | 0.014555145551455515 |
| main-qwen-c1-17-r0-fit-format2 | recovery | 318 | 318 | 282 | 80 | 368 | 24448 | 0.028795811518324606 |
| main-qwen-c1-17-r1-fit-format2 | clean | 758 | 487 | 372 | 145 | 372 | 24869 | 0.014274799951747155 |
| main-qwen-c1-17-r1-fit-format2 | recovery | 14 | 14 | 14 | 9 | 363 | 23976 | 0.3743326659993327 |
| main-qwen-c3-17-r0-fit | clean | 323 | 323 | 260 | 83 | 317 | 21084 | 0.03310567254790362 |
| main-qwen-c3-17-r0-fit | recovery | 494 | 435 | 311 | 114 | 311 | 20493 | 0.017322988337481093 |
| main-qwen-c3-17-r1-fit | clean | 742 | 438 | 319 | 143 | 319 | 21210 | 0.016737388024516738 |
| main-qwen-c3-17-r1-fit | recovery | 33 | 33 | 33 | 18 | 315 | 20679 | 0.17263890903815465 |
| main-qwen-c4-17-r0-fit | clean | 470 | 417 | 295 | 95 | 295 | 19642 | 0.01797169331025354 |
| main-qwen-c4-17-r0-fit | recovery | 340 | 340 | 246 | 81 | 293 | 19458 | 0.035872134854558535 |
| main-qwen-c4-17-r1-fit | clean | 755 | 419 | 298 | 137 | 298 | 19840 | 0.017893145161290324 |
| main-qwen-c4-17-r1-fit | recovery | 14 | 14 | 14 | 8 | 295 | 19477 | 0.38999845972172303 |

The CPU token stream reproduces per-step input and supervised-target counts, including orphaned suffix masking and resume-prefix replay. Loading into a buffer is not contributing loss. The C1 round-one small failed pool can create repeated exposure; this is not automatically a useful recovery-diversity increase. Per-process audits distinguish any resumed prefix from new optimization; a future resume chain must be joined to describe final-checkpoint cumulative exposure. Target-token totals need not match despite matched input-token budgets.

Historical severity: C3 flipped 50/243 reference-correct states; C5 flipped 10/241. Those are prior frozen-policy pilot observations, not main estimates. Current main before/after action-error counts in `collection_audit.json` are temporal associations; user updates can intervene. The optional new replay uses common training-only saved inputs and a fresh no-action frozen reference. Its actions were originally generated on different role histories, so it is a same-state action-effect diagnostic, not a matched attack-generation or curriculum correction.

## Goal conflict, routing, memory, and confounding

The original C5 cast owns distinct slots, making its preferred values jointly satisfiable. The final mechanism pilot's 64 delivered antagonist messages produced zero typed matching followups and zero repeated candidates. This does not establish that semantic interaction never occurred; the typed metric can miss useful disclosure and overcount empty echoes. Actual exchanges are prepared for two independent raters; ratings remain pending. Until stronger evidence exists, describe persistent antagonistic personas, without claiming coalitions or substantive rivalry.

Original C4 reserved communications can write notes to Jekyll; C5 prompts messages to another antagonist, although that request is not a hard routing restriction. The final C5 pilot actually sent 10 reserved peer notes to Jekyll and 54 reserved messages to antagonists, plus 10 antagonist messages in direct slots; these are retained, not reclassified as compliant reserved routing. `communication_routing.csv` separates reserved/direct opportunities and actual notes, deliveries, edits, passes and rejected actions. A frozen routing control does not retroactively fix the learned C5−C4 contrast.

471/480 C1 final prompts contain all canonical authorizing sources. Source availability alone does not prove trajectory or memory irrelevance. A0/A1/A2 and the optional common-input reference test different terminal channels; removed assistant evidence and retrieval limits must accompany any interpretation. Similar A0/A2 performance would concern terminal-memory dependence, not establish that earlier memory never mattered.

All 30 ambiguous main-test families are creative and use the held-out conditional rule. This confounds ambiguity, that domain and rule structure. The four domains retain one six-slot schema. Neither the original test nor the optional crossed validation supports broad domain transfer beyond this shared synthetic task.

## Supplementary execution status

| stage | status |
| --- | --- |
| balanced | pending |
| conflict | pending |
| memory | pending |
| routing | pending |
| severity | pending |

Separate tables: `memory_dependence.csv`, `replay_agreement.csv`, `paired_contrasts.csv`, `memory_strata.csv`, `goal_conflict.csv`, `routing_control.csv`, `severity_replay.csv`, and `balanced_validation.csv`. Empty tables explicitly have pending/not-executed status; they are not null results. The fixed allocation is made from profiling time only, before examining diagnostic outcomes. All loads, profiling and failed attempts count toward two review GPU-hours within 96; at least 30 minutes remains reserved. Review work precedes the optional unseen-profile supplement.

## Remaining scientific requirements

Core completion status and every diagnostic status are listed above. Any unfinished core stages, unexecuted diagnostics, A0 replay integrity review, genuine human ratings, and author review of scientific arguments and conclusions remain outstanding as applicable. Character-conditioned data generation with supervised adapter training and history-dependent frozen characters is the implemented method. Retrieval is fixed. No demonstrated co-evolution, autonomous exploration, optimized game equilibrium, broad robustness, or conference readiness follows from these audits.
