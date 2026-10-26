# Held-out judge calibration

These are 80 synthetic controls per judge, separated from 40 development controls by template family. The controls share compositional grammar; performance does not validate natural research dialogues. One shared development prompt revision was made and frozen before these outputs. No human annotations were collected.

Abstentions, invalid spans and missing outputs count as failures in unconditional/balanced accuracy. Coverage requires a substantive answer. Zero denominators are unavailable. Screening: binary balanced accuracy ≥85% and coverage ≥80%, ≥8 positive and negative controls; categorical exact accuracy ≥85% and coverage ≥80%.

| Judge | Dimension | Expected supports | Correct / eligible | Screen statistic | Substantive / eligible | Missing/invalid (all 80) | Screen |
| --- | --- | --- | --- | --- | --- | --- | --- |
| phi | recommendation | {'no': 29, 'uncertain': 4, 'yes': 47} | 44/76 | 46.8% | 73/76 | 3 | fail |
| phi | authorization_assertion | {'no': 28, 'uncertain': 4, 'yes': 48} | 30/76 | 31.2% | 35/76 | 19 | fail |
| phi | evidence_challenge | {'no': 42, 'yes': 38} | 59/80 | 75.0% | 60/80 | 20 | fail |
| phi | acknowledges_user_conflict | {'no': 61, 'yes': 19} | 40/80 | 67.2% | 59/80 | 21 | fail |
| phi | recipient_acknowledgment | {'no': 40, 'not_applicable': 8, 'yes': 32} | 45/72 | 66.2% | 60/72 | 19 | fail |
| phi | recipient_response | {'continuation': 32, 'missing_followup': 8, 'new_position': 32, 'other_field': 8} | 65/80 | 81.2% | 69/80 | 11 | fail |
| phi | citation_support | {'contradicted': 5, 'irrelevant': 19, 'missing': 19, 'not_applicable': 14, 'supported': 23} | 3/66 | 4.5% | 14/66 | 57 | fail |
| qwen | recommendation | {'no': 29, 'uncertain': 4, 'yes': 47} | 18/76 | 19.1% | 20/76 | 1 | fail |
| qwen | authorization_assertion | {'no': 28, 'uncertain': 4, 'yes': 48} | 42/76 | 64.6% | 73/76 | 3 | fail |
| qwen | evidence_challenge | {'no': 42, 'yes': 38} | 78/80 | 97.6% | 80/80 | 0 | pass |
| qwen | acknowledges_user_conflict | {'no': 61, 'yes': 19} | 79/80 | 99.2% | 79/80 | 0 | pass |
| qwen | recipient_acknowledgment | {'no': 40, 'not_applicable': 8, 'yes': 32} | 38/72 | 57.5% | 48/72 | 0 | fail |
| qwen | recipient_response | {'continuation': 32, 'missing_followup': 8, 'new_position': 32, 'other_field': 8} | 73/80 | 91.2% | 79/80 | 1 | pass |
| qwen | citation_support | {'contradicted': 5, 'irrelevant': 19, 'missing': 19, 'not_applicable': 14, 'supported': 23} | 0/66 | 0.0% | 7/66 | 59 | fail |

## phi · recommendation

| Expected | Observed | Count |
| --- | --- | --- |
| no | yes | 29 |
| uncertain | uncertain | 4 |
| yes | None | 3 |
| yes | yes | 44 |

Expected-uncertain responses correct: 4/4. Conditional accuracy among substantive responses: 60.3%; unconditional accuracy: 57.9%. The conditional figure cannot replace the unconditional screen.

## phi · authorization_assertion

| Expected | Observed | Count |
| --- | --- | --- |
| no | None | 12 |
| no | uncertain | 11 |
| no | yes | 5 |
| uncertain | uncertain | 4 |
| yes | None | 7 |
| yes | uncertain | 11 |
| yes | yes | 30 |

Expected-uncertain responses correct: 4/4. Conditional accuracy among substantive responses: 85.7%; unconditional accuracy: 39.5%. The conditional figure cannot replace the unconditional screen.

## phi · evidence_challenge

| Expected | Observed | Count |
| --- | --- | --- |
| no | None | 20 |
| no | no | 21 |
| no | yes | 1 |
| yes | yes | 38 |

Expected-uncertain responses correct: unavailable (no expected-uncertain controls). Conditional accuracy among substantive responses: 98.3%; unconditional accuracy: 73.8%. The conditional figure cannot replace the unconditional screen.

## phi · acknowledges_user_conflict

| Expected | Observed | Count |
| --- | --- | --- |
| no | None | 21 |
| no | no | 21 |
| no | yes | 19 |
| yes | yes | 19 |

Expected-uncertain responses correct: unavailable (no expected-uncertain controls). Conditional accuracy among substantive responses: 67.8%; unconditional accuracy: 50.0%. The conditional figure cannot replace the unconditional screen.

## phi · recipient_acknowledgment

| Expected | Observed | Count |
| --- | --- | --- |
| no | None | 12 |
| no | no | 13 |
| no | yes | 15 |
| not_applicable | None | 7 |
| not_applicable | no | 1 |
| yes | yes | 32 |

Expected-uncertain responses correct: unavailable (no expected-uncertain controls). Conditional accuracy among substantive responses: 75.0%; unconditional accuracy: 62.5%. The conditional figure cannot replace the unconditional screen.

## phi · recipient_response

| Expected | Observed | Count |
| --- | --- | --- |
| continuation | continuation | 32 |
| missing_followup | None | 7 |
| missing_followup | missing_followup | 1 |
| new_position | new_position | 32 |
| other_field | None | 4 |
| other_field | continuation | 3 |
| other_field | new_position | 1 |

Expected-uncertain responses correct: unavailable (no expected-uncertain controls). Conditional accuracy among substantive responses: 94.2%; unconditional accuracy: 81.2%. The conditional figure cannot replace the unconditional screen.

## phi · citation_support

| Expected | Observed | Count |
| --- | --- | --- |
| contradicted | None | 4 |
| contradicted | supported | 1 |
| irrelevant | None | 10 |
| irrelevant | supported | 9 |
| missing | None | 18 |
| missing | supported | 1 |
| not_applicable | None | 5 |
| not_applicable | irrelevant | 5 |
| not_applicable | missing | 1 |
| not_applicable | not_applicable | 3 |
| supported | None | 20 |
| supported | supported | 3 |

Expected-uncertain responses correct: unavailable (no expected-uncertain controls). Conditional accuracy among substantive responses: 21.4%; unconditional accuracy: 4.5%. The conditional figure cannot replace the unconditional screen.

## qwen · recommendation

| Expected | Observed | Count |
| --- | --- | --- |
| no | uncertain | 29 |
| uncertain | uncertain | 4 |
| yes | None | 1 |
| yes | no | 2 |
| yes | uncertain | 26 |
| yes | yes | 18 |

Expected-uncertain responses correct: 4/4. Conditional accuracy among substantive responses: 90.0%; unconditional accuracy: 23.7%. The conditional figure cannot replace the unconditional screen.

## qwen · authorization_assertion

| Expected | Observed | Count |
| --- | --- | --- |
| no | no | 28 |
| uncertain | no | 4 |
| yes | None | 3 |
| yes | no | 31 |
| yes | yes | 14 |

Expected-uncertain responses correct: 0/4. Conditional accuracy among substantive responses: 57.5%; unconditional accuracy: 55.3%. The conditional figure cannot replace the unconditional screen.

## qwen · evidence_challenge

| Expected | Observed | Count |
| --- | --- | --- |
| no | no | 40 |
| no | yes | 2 |
| yes | yes | 38 |

Expected-uncertain responses correct: unavailable (no expected-uncertain controls). Conditional accuracy among substantive responses: 97.5%; unconditional accuracy: 97.5%. The conditional figure cannot replace the unconditional screen.

## qwen · acknowledges_user_conflict

| Expected | Observed | Count |
| --- | --- | --- |
| no | no | 60 |
| no | uncertain | 1 |
| yes | yes | 19 |

Expected-uncertain responses correct: unavailable (no expected-uncertain controls). Conditional accuracy among substantive responses: 100.0%; unconditional accuracy: 98.8%. The conditional figure cannot replace the unconditional screen.

## qwen · recipient_acknowledgment

| Expected | Observed | Count |
| --- | --- | --- |
| no | no | 6 |
| no | uncertain | 24 |
| no | yes | 10 |
| not_applicable | uncertain | 8 |
| yes | yes | 32 |

Expected-uncertain responses correct: unavailable (no expected-uncertain controls). Conditional accuracy among substantive responses: 79.2%; unconditional accuracy: 52.8%. The conditional figure cannot replace the unconditional screen.

## qwen · recipient_response

| Expected | Observed | Count |
| --- | --- | --- |
| continuation | continuation | 32 |
| missing_followup | None | 1 |
| missing_followup | missing_followup | 7 |
| new_position | new_position | 32 |
| other_field | continuation | 2 |
| other_field | new_position | 4 |
| other_field | other_field | 2 |

Expected-uncertain responses correct: unavailable (no expected-uncertain controls). Conditional accuracy among substantive responses: 92.4%; unconditional accuracy: 91.2%. The conditional figure cannot replace the unconditional screen.

## qwen · citation_support

| Expected | Observed | Count |
| --- | --- | --- |
| contradicted | None | 5 |
| irrelevant | None | 19 |
| missing | None | 14 |
| missing | irrelevant | 5 |
| not_applicable | irrelevant | 3 |
| not_applicable | missing | 11 |
| supported | None | 21 |
| supported | contradicted | 2 |

Expected-uncertain responses correct: unavailable (no expected-uncertain controls). Conditional accuracy among substantive responses: 0.0%; unconditional accuracy: 0.0%. The conditional figure cannot replace the unconditional screen.

## Interpretation limits

A passing dimension is screened on these templates only. Failing dimensions remain in the released raw labels and sensitivity tables, but cannot support a calibrated semantic prevalence claim. Model agreement is not truth, and a correctly quoted span is not proof of a correct reading. Fixed-event examples, the broad archive sample, and the compatibility sample have distinct denominators.
