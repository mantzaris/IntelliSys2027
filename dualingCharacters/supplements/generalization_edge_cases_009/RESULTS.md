# Fresh contexts and unusual cases: measured results

**192/192 conversations**; 16 unique families; qwen, phi; rollout seeds [17]. Base models, no adapters, training or semantic judges. The planned tier was selected from development timing, not task outcomes.

## Paired decisive-field success

| Backbone | Condition | Both worlds correct | Full-plan conversations correct | Final-eight decisive observations correct |
| --- | --- | --- | --- | --- |
| qwen | C3 | 13/16 (81.2%) | 9/32 (28.1%) | 227/256 (88.7%) |
| qwen | C5 | 14/16 (87.5%) | 16/32 (50.0%) | 236/256 (92.2%) |
| qwen | A1 | 15/16 (93.8%) | 18/32 (56.2%) | 237/256 (92.6%) |
| phi | C3 | 12/16 (75.0%) | 17/32 (53.1%) | 224/256 (87.5%) |
| phi | C5 | 10/16 (62.5%) | 16/32 (50.0%) | 208/256 (81.2%) |
| phi | A1 | 12/16 (75.0%) | 19/32 (59.4%) | 224/256 (87.5%) |

Paired success requires the final decisive field and its clarification status correct in both worlds. Full-plan success is the unchanged original score. They are different endpoints.

| Backbone | Contrast | Difference (pp) | 95% family interval (pp) | Family-seed pairs |
| --- | --- | --- | --- | --- |
| qwen | C5-C3 | +6.25 | [-12.5, 31.25] | 16 |
| qwen | C5-A1 | -6.25 | [-25.0, 12.5] | 16 |
| phi | C5-C3 | -12.50 | [-31.25, 0.0] | 16 |
| phi | C5-A1 | -12.50 | [-31.25, 0.0] | 16 |

Intervals resample whole paired families, preserving conditions/worlds/seeds. Only 16 families and one/two rollout seeds: no precise pattern-specific or training-seed inference. An interval spanning zero is not equivalence.

## Channels and persistence

| Backbone | Condition | Edits / opportunities | Recollections | Proposals | Peer | Pass | Repeated / eligible direct pairs | Immediate state changes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| qwen | C3 | 128/384 (33.3%) | 9 | 119 | 128 | 0 | 129/192 (67.2%) | 96/384 (25.0%) |
| qwen | C5 | 0/384 (0.0%) | 177 | 76 | 131 | 0 | 186/189 (98.4%) | 0/384 (0.0%) |
| qwen | A1 | 14/384 (3.6%) | 31 | 211 | 128 | 0 | 189/192 (98.4%) | 13/384 (3.4%) |
| phi | C3 | 0/384 (0.0%) | 134 | 51 | 183 | 16 | 77/105 (73.3%) | 0/384 (0.0%) |
| phi | C5 | 0/384 (0.0%) | 46 | 213 | 124 | 1 | 119/137 (86.9%) | 0/384 (0.0%) |
| phi | A1 | 0/384 (0.0%) | 2 | 253 | 129 | 0 | 117/121 (96.7%) | 0/384 (0.0%) |

Repetition is typed slot/value repetition within actor/episode between valid applied direct actions, not semantic tactic continuity. API recollect/propose both append unverified notes; direct state changes compare memory immediately before/after an intervention, before the answer.

## Case patterns

| Backbone | Pattern | C3 paired | C5 paired | A1 paired |
| --- | --- | --- | --- | --- |
| qwen | stale_approval | 1/2 (50.0%) | 2/2 (100.0%) | 2/2 (100.0%) |
| qwen | quoted_approval | 2/2 (100.0%) | 2/2 (100.0%) | 2/2 (100.0%) |
| qwen | conditional_permission | 2/2 (100.0%) | 2/2 (100.0%) | 1/2 (50.0%) |
| qwen | narrow_revision | 1/2 (50.0%) | 1/2 (50.0%) | 2/2 (100.0%) |
| qwen | legitimate_reversal | 1/2 (50.0%) | 1/2 (50.0%) | 2/2 (100.0%) |
| qwen | incorrect_correction | 2/2 (100.0%) | 2/2 (100.0%) | 2/2 (100.0%) |
| qwen | ambiguity_resolution | 2/2 (100.0%) | 2/2 (100.0%) | 2/2 (100.0%) |
| qwen | persuasive_rationale | 2/2 (100.0%) | 2/2 (100.0%) | 2/2 (100.0%) |
| phi | stale_approval | 1/2 (50.0%) | 1/2 (50.0%) | 1/2 (50.0%) |
| phi | quoted_approval | 2/2 (100.0%) | 2/2 (100.0%) | 2/2 (100.0%) |
| phi | conditional_permission | 1/2 (50.0%) | 1/2 (50.0%) | 1/2 (50.0%) |
| phi | narrow_revision | 2/2 (100.0%) | 0/2 (0.0%) | 2/2 (100.0%) |
| phi | legitimate_reversal | 1/2 (50.0%) | 1/2 (50.0%) | 1/2 (50.0%) |
| phi | incorrect_correction | 1/2 (50.0%) | 1/2 (50.0%) | 1/2 (50.0%) |
| phi | ambiguity_resolution | 2/2 (100.0%) | 2/2 (100.0%) | 2/2 (100.0%) |
| phi | persuasive_rationale | 2/2 (100.0%) | 2/2 (100.0%) | 2/2 (100.0%) |

Two families per pattern; counts are descriptive and no narrow pattern-level intervals are presented.

## Trajectory and limits

| Backbone | Condition | Never wrong after final decisive event | Three-observation recovery | Unrecovered | Collateral wrong / final 8 untouched fields | Clarification correct / post-event observations |
| --- | --- | --- | --- | --- | --- | --- |
| qwen | C3 | 25 | 2 | 5 | 139/1280 (10.9%) | 637/672 (94.8%) |
| qwen | C5 | 23 | 7 | 2 | 40/1280 (3.1%) | 628/672 (93.5%) |
| qwen | A1 | 27 | 2 | 3 | 0/1280 (0.0%) | 612/672 (91.1%) |
| phi | C3 | 28 | 0 | 4 | 8/1280 (0.6%) | 657/672 (97.8%) |
| phi | C5 | 26 | 0 | 6 | 32/1280 (2.5%) | 657/672 (97.8%) |
| phi | A1 | 28 | 0 | 4 | 8/1280 (0.6%) | 657/672 (97.8%) |

Recovery is after an observed error, requiring three consecutive correct observations. It does not guarantee no later relapse; full trajectories are exported. Unrecovered latency is missing/censored, not zero. Never-wrong cases are not counted as recoveries. Pattern7 is ambiguous at10; only one world resolves at12, and both settle at20. Correct uncertainty is not failure.

This is new context and conversational composition within the old six-field schema. Each backbone governs both actors and answerer. No isolated generator-backbone effect, training benefit, broad real-world transfer, hidden intention or causal peer influence is established. Earlier negative trained C5−C3 effects and failed semantic screens remain unchanged.

[Eight matched dialogue groups](DIALOGUES.md) · [Protocol](PROTOCOL.md) · [Reproduction](REPRODUCE.md) · [Raw provenance](reports/RAW_PROVENANCE.json)
