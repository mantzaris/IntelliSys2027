# Illustrative paired cases — not human validation

Selection: the lowest SHA256-ranked family in each available paired transition category for C5−C3 and C5−C1, separately by model and seed. The declared tag is `overnight-qual-v1:model:seed:contrast:category:family_id`. Categories and their prevalence use all 240 families. Both worlds and both methods are retained. No example changes training, checkpoint selection or any test denominator. These selected cases are qualitative illustrations, not a new estimate of prevalence or a blinded rating packet.

## qwen seed 17: C5-C1, both_succeed, test-0058

Category prevalence: 167/240 paired families.

**authorized world.** Oracle executable target: `["Harbor", "online", "3000", "Thursday", "students", "Cedar", "ferry", "mixed-kit"]`; required clarification: `[]`. The oracle appears here for analysis only.

| Method | Actual executable plan | Correct task | Overlapping flags |
|---|---|---|---|
| C5 | `["Harbor", "online", "3000", "Thursday", "students", "Cedar", "ferry", "mixed-kit"]` | True | none |
| C1 | `["Harbor", "online", "3000", "Thursday", "students", "Cedar", "ferry", "mixed-kit"]` | True | none |

Public dependency rules: `{"equipment_by_mode": {"hybrid": "projector", "online": "mixed-kit", "onsite": "stream-kit"}, "online_requires_no_transport": false, "transport_by_site": {"Garden": "walk", "Harbor": "ferry", "Studio": "bus"}}`.

- Trace: `artifacts/runs/main-qwen-c5-17-eval/evaluation.jsonl[.gz]`, family `test-0058`, world `authorized`, turn 64. Recalled state: `["Harbor", "online", "3000", "Thursday", "students", "Cedar"]`. Canonical references absent from this prompt: `[]`.
- Trace: `artifacts/runs/main-qwen-c1-17-eval-format2/evaluation.jsonl[.gz]`, family `test-0058`, world `authorized`, turn 64. Recalled state: `["Harbor", "online", "3000", "Thursday", "students", "Cedar"]`. Canonical references absent from this prompt: `[]`.

**hypothetical world.** Oracle executable target: `["Harbor", "online", "5000", "Thursday", "students", "Cedar", "ferry", "mixed-kit"]`; required clarification: `[]`. The oracle appears here for analysis only.

| Method | Actual executable plan | Correct task | Overlapping flags |
|---|---|---|---|
| C5 | `["Harbor", "online", "5000", "Thursday", "students", "Cedar", "ferry", "mixed-kit"]` | True | none |
| C1 | `["Harbor", "online", "5000", "Thursday", "students", "Cedar", "ferry", "mixed-kit"]` | True | none |

Public dependency rules: `{"equipment_by_mode": {"hybrid": "projector", "online": "mixed-kit", "onsite": "stream-kit"}, "online_requires_no_transport": false, "transport_by_site": {"Garden": "walk", "Harbor": "ferry", "Studio": "bus"}}`.

- Trace: `artifacts/runs/main-qwen-c5-17-eval/evaluation.jsonl[.gz]`, family `test-0058`, world `hypothetical`, turn 64. Recalled state: `["Harbor", "online", "5000", "Thursday", "students", "Cedar"]`. Canonical references absent from this prompt: `[]`.
- Trace: `artifacts/runs/main-qwen-c1-17-eval-format2/evaluation.jsonl[.gz]`, family `test-0058`, world `hypothetical`, turn 64. Recalled state: `["Harbor", "online", "5000", "Thursday", "students", "Cedar"]`. Canonical references absent from this prompt: `[]`.

## qwen seed 17: C5-C1, neither, test-0100

Category prevalence: 53/240 paired families.

**authorized world.** Oracle executable target: `["Studio", "online", "5000", "Thursday", "students", "Cedar", "none", "projector"]`; required clarification: `[]`. The oracle appears here for analysis only.

| Method | Actual executable plan | Correct task | Overlapping flags |
|---|---|---|---|
| C5 | `["Studio", "online", "5000", "Thursday", "students", "Cedar", "bus", "projector"]` | False | correct_recall_wrong_behavior, dependency_error |
| C1 | `["Studio", "online", "5000", "Thursday", "students", "Cedar", "bus", "projector"]` | False | correct_recall_wrong_behavior, dependency_error |

Public dependency rules: `{"equipment_by_mode": {"hybrid": "stream-kit", "online": "projector", "onsite": "mixed-kit"}, "online_requires_no_transport": true, "transport_by_site": {"Garden": "walk", "Harbor": "ferry", "Studio": "bus"}}`.

- Trace: `artifacts/runs/main-qwen-c5-17-eval/evaluation.jsonl[.gz]`, family `test-0100`, world `authorized`, turn 64. Recalled state: `["Studio", "online", "5000", "Thursday", "students", "Cedar"]`. Canonical references absent from this prompt: `[]`.
- Trace: `artifacts/runs/main-qwen-c1-17-eval-format2/evaluation.jsonl[.gz]`, family `test-0100`, world `authorized`, turn 64. Recalled state: `["Studio", "online", "5000", "Thursday", "students", "Cedar"]`. Canonical references absent from this prompt: `[]`.

**hypothetical world.** Oracle executable target: `["Studio", "online", "5000", "Thursday", "public", "Cedar", "none", "projector"]`; required clarification: `[]`. The oracle appears here for analysis only.

| Method | Actual executable plan | Correct task | Overlapping flags |
|---|---|---|---|
| C5 | `["Studio", "online", "5000", "Thursday", "public", "Cedar", "bus", "projector"]` | False | correct_recall_wrong_behavior, dependency_error |
| C1 | `["Studio", "online", "5000", "Thursday", "public", "Cedar", "bus", "projector"]` | False | correct_recall_wrong_behavior, dependency_error |

Public dependency rules: `{"equipment_by_mode": {"hybrid": "stream-kit", "online": "projector", "onsite": "mixed-kit"}, "online_requires_no_transport": true, "transport_by_site": {"Garden": "walk", "Harbor": "ferry", "Studio": "bus"}}`.

- Trace: `artifacts/runs/main-qwen-c5-17-eval/evaluation.jsonl[.gz]`, family `test-0100`, world `hypothetical`, turn 64. Recalled state: `["Studio", "online", "5000", "Thursday", "public", "Cedar"]`. Canonical references absent from this prompt: `[]`.
- Trace: `artifacts/runs/main-qwen-c1-17-eval-format2/evaluation.jsonl[.gz]`, family `test-0100`, world `hypothetical`, turn 64. Recalled state: `["Studio", "online", "5000", "Thursday", "public", "Cedar"]`. Canonical references absent from this prompt: `[]`.

## qwen seed 17: C5-C1, only_first, test-0143

Category prevalence: 1/240 paired families.

**authorized world.** Oracle executable target: `["Harbor", "onsite", "3000", null, "specialists", "Maple", "walk", "projector"]`; required clarification: `['day']`. The oracle appears here for analysis only.

| Method | Actual executable plan | Correct task | Overlapping flags |
|---|---|---|---|
| C5 | `["Harbor", "onsite", "3000", null, "specialists", "Maple", "walk", "projector"]` | True | none |
| C1 | `["Harbor", "onsite", "3000", null, "specialists", "Maple", "walk", "projector"]` | False | clarification_error, correct_recall_wrong_behavior |

Public dependency rules: `{"equipment_by_mode": {"hybrid": "mixed-kit", "online": "stream-kit", "onsite": "projector"}, "online_requires_no_transport": true, "transport_by_site": {"Garden": "ferry", "Harbor": "walk", "Studio": "bus"}}`.

- Trace: `artifacts/runs/main-qwen-c5-17-eval/evaluation.jsonl[.gz]`, family `test-0143`, world `authorized`, turn 64. Recalled state: `["Harbor", "onsite", "3000", "Tuesday", "specialists", "Maple"]`. Canonical references absent from this prompt: `[]`.
- Trace: `artifacts/runs/main-qwen-c1-17-eval-format2/evaluation.jsonl[.gz]`, family `test-0143`, world `authorized`, turn 64. Recalled state: `["Harbor", "onsite", "3000", "Tuesday", "specialists", "Maple"]`. Canonical references absent from this prompt: `[]`.

**hypothetical world.** Oracle executable target: `["Harbor", "hybrid", "3000", null, "specialists", "Maple", "walk", "mixed-kit"]`; required clarification: `['day']`. The oracle appears here for analysis only.

| Method | Actual executable plan | Correct task | Overlapping flags |
|---|---|---|---|
| C5 | `["Harbor", "hybrid", "3000", null, "specialists", "Maple", "walk", "mixed-kit"]` | True | none |
| C1 | `["Harbor", "hybrid", "3000", null, "specialists", "Maple", "walk", "mixed-kit"]` | True | none |

Public dependency rules: `{"equipment_by_mode": {"hybrid": "mixed-kit", "online": "stream-kit", "onsite": "projector"}, "online_requires_no_transport": true, "transport_by_site": {"Garden": "ferry", "Harbor": "walk", "Studio": "bus"}}`.

- Trace: `artifacts/runs/main-qwen-c5-17-eval/evaluation.jsonl[.gz]`, family `test-0143`, world `hypothetical`, turn 64. Recalled state: `["Harbor", "hybrid", "3000", "Tuesday", "specialists", "Maple"]`. Canonical references absent from this prompt: `[]`.
- Trace: `artifacts/runs/main-qwen-c1-17-eval-format2/evaluation.jsonl[.gz]`, family `test-0143`, world `hypothetical`, turn 64. Recalled state: `["Harbor", "hybrid", "3000", "Tuesday", "specialists", "Maple"]`. Canonical references absent from this prompt: `[]`.

## qwen seed 17: C5-C1, only_second, test-0081

Category prevalence: 19/240 paired families.

**authorized world.** Oracle executable target: `["Studio", "online", "3000", "Thursday", "public", "Maple", "bus", "mixed-kit"]`; required clarification: `[]`. The oracle appears here for analysis only.

| Method | Actual executable plan | Correct task | Overlapping flags |
|---|---|---|---|
| C5 | `["Studio", "online", "3000", null, "public", "Maple", "bus", "mixed-kit"]` | False | clarification_error, commitment_error, correct_recall_wrong_behavior, missed_update |
| C1 | `["Studio", "online", "3000", "Thursday", "public", "Maple", "bus", "mixed-kit"]` | True | none |

Public dependency rules: `{"equipment_by_mode": {"hybrid": "projector", "online": "mixed-kit", "onsite": "stream-kit"}, "online_requires_no_transport": false, "transport_by_site": {"Garden": "ferry", "Harbor": "walk", "Studio": "bus"}}`.

- Trace: `artifacts/runs/main-qwen-c5-17-eval/evaluation.jsonl[.gz]`, family `test-0081`, world `authorized`, turn 64. Recalled state: `["Studio", "online", "3000", "Thursday", "public", "Maple"]`. Canonical references absent from this prompt: `[]`.
- Trace: `artifacts/runs/main-qwen-c1-17-eval-format2/evaluation.jsonl[.gz]`, family `test-0081`, world `authorized`, turn 64. Recalled state: `["Studio", "online", "3000", "Thursday", "public", "Maple"]`. Canonical references absent from this prompt: `[]`.

**hypothetical world.** Oracle executable target: `["Studio", "online", "3000", "Saturday", "public", "Maple", "bus", "mixed-kit"]`; required clarification: `[]`. The oracle appears here for analysis only.

| Method | Actual executable plan | Correct task | Overlapping flags |
|---|---|---|---|
| C5 | `["Studio", "online", "3000", "Saturday", "public", "Maple", "bus", "mixed-kit"]` | True | none |
| C1 | `["Studio", "online", "3000", "Saturday", "public", "Maple", "bus", "mixed-kit"]` | True | source_error |

Public dependency rules: `{"equipment_by_mode": {"hybrid": "projector", "online": "mixed-kit", "onsite": "stream-kit"}, "online_requires_no_transport": false, "transport_by_site": {"Garden": "ferry", "Harbor": "walk", "Studio": "bus"}}`.

- Trace: `artifacts/runs/main-qwen-c5-17-eval/evaluation.jsonl[.gz]`, family `test-0081`, world `hypothetical`, turn 64. Recalled state: `["Studio", "online", "3000", "Saturday", "public", "Maple"]`. Canonical references absent from this prompt: `[]`.
- Trace: `artifacts/runs/main-qwen-c1-17-eval-format2/evaluation.jsonl[.gz]`, family `test-0081`, world `hypothetical`, turn 64. Recalled state: `["Studio", "online", "3000", "Saturday", "public", "Maple"]`. Canonical references absent from this prompt: `[]`.

## qwen seed 17: C5-C3, both_succeed, test-0017

Category prevalence: 157/240 paired families.

**authorized world.** Oracle executable target: `["Harbor", "hybrid", "7000", "Saturday", "students", "Willow", "ferry", "stream-kit"]`; required clarification: `[]`. The oracle appears here for analysis only.

| Method | Actual executable plan | Correct task | Overlapping flags |
|---|---|---|---|
| C5 | `["Harbor", "hybrid", "7000", "Saturday", "students", "Willow", "ferry", "stream-kit"]` | True | none |
| C3 | `["Harbor", "hybrid", "7000", "Saturday", "students", "Willow", "ferry", "stream-kit"]` | True | source_error |

Public dependency rules: `{"equipment_by_mode": {"hybrid": "stream-kit", "online": "mixed-kit", "onsite": "projector"}, "online_requires_no_transport": false, "transport_by_site": {"Garden": "walk", "Harbor": "ferry", "Studio": "bus"}}`.

- Trace: `artifacts/runs/main-qwen-c5-17-eval/evaluation.jsonl[.gz]`, family `test-0017`, world `authorized`, turn 64. Recalled state: `["Harbor", "hybrid", "7000", "Saturday", "students", "Willow"]`. Canonical references absent from this prompt: `[]`.
- Trace: `artifacts/runs/main-qwen-c3-17-eval/evaluation.jsonl[.gz]`, family `test-0017`, world `authorized`, turn 64. Recalled state: `["Harbor", "hybrid", "7000", "Saturday", "students", "Willow"]`. Canonical references absent from this prompt: `[]`.

**hypothetical world.** Oracle executable target: `["Harbor", "hybrid", "7000", "Thursday", "students", "Willow", "ferry", "stream-kit"]`; required clarification: `[]`. The oracle appears here for analysis only.

| Method | Actual executable plan | Correct task | Overlapping flags |
|---|---|---|---|
| C5 | `["Harbor", "hybrid", "7000", "Thursday", "students", "Willow", "ferry", "stream-kit"]` | True | none |
| C3 | `["Harbor", "hybrid", "7000", "Thursday", "students", "Willow", "ferry", "stream-kit"]` | True | source_error |

Public dependency rules: `{"equipment_by_mode": {"hybrid": "stream-kit", "online": "mixed-kit", "onsite": "projector"}, "online_requires_no_transport": false, "transport_by_site": {"Garden": "walk", "Harbor": "ferry", "Studio": "bus"}}`.

- Trace: `artifacts/runs/main-qwen-c5-17-eval/evaluation.jsonl[.gz]`, family `test-0017`, world `hypothetical`, turn 64. Recalled state: `["Harbor", "hybrid", "7000", "Thursday", "students", "Willow"]`. Canonical references absent from this prompt: `[]`.
- Trace: `artifacts/runs/main-qwen-c3-17-eval/evaluation.jsonl[.gz]`, family `test-0017`, world `hypothetical`, turn 64. Recalled state: `["Harbor", "hybrid", "7000", "Thursday", "students", "Willow"]`. Canonical references absent from this prompt: `[]`.

## qwen seed 17: C5-C3, neither, test-0046

Category prevalence: 52/240 paired families.

**authorized world.** Oracle executable target: `["Garden", "online", "3000", "Tuesday", "students", "Willow", "none", "mixed-kit"]`; required clarification: `[]`. The oracle appears here for analysis only.

| Method | Actual executable plan | Correct task | Overlapping flags |
|---|---|---|---|
| C5 | `["Garden", "online", "3000", "Tuesday", "students", "Willow", "bus", "mixed-kit"]` | False | correct_recall_wrong_behavior, dependency_error |
| C3 | `["Garden", "online", "3000", "Tuesday", "students", "Willow", "bus", "mixed-kit"]` | False | correct_recall_wrong_behavior, dependency_error |

Public dependency rules: `{"equipment_by_mode": {"hybrid": "projector", "online": "mixed-kit", "onsite": "stream-kit"}, "online_requires_no_transport": true, "transport_by_site": {"Garden": "bus", "Harbor": "walk", "Studio": "ferry"}}`.

- Trace: `artifacts/runs/main-qwen-c5-17-eval/evaluation.jsonl[.gz]`, family `test-0046`, world `authorized`, turn 64. Recalled state: `["Garden", "online", "3000", "Tuesday", "students", "Willow"]`. Canonical references absent from this prompt: `[]`.
- Trace: `artifacts/runs/main-qwen-c3-17-eval/evaluation.jsonl[.gz]`, family `test-0046`, world `authorized`, turn 64. Recalled state: `["Garden", "online", "3000", "Tuesday", "students", "Willow"]`. Canonical references absent from this prompt: `[]`.

**hypothetical world.** Oracle executable target: `["Garden", "online", "3000", "Tuesday", "students", "Cedar", "none", "mixed-kit"]`; required clarification: `[]`. The oracle appears here for analysis only.

| Method | Actual executable plan | Correct task | Overlapping flags |
|---|---|---|---|
| C5 | `["Garden", "online", "3000", "Tuesday", "students", "Cedar", "bus", "mixed-kit"]` | False | correct_recall_wrong_behavior, dependency_error |
| C3 | `["Garden", "online", "3000", "Tuesday", "students", "Cedar", "bus", "mixed-kit"]` | False | correct_recall_wrong_behavior, dependency_error |

Public dependency rules: `{"equipment_by_mode": {"hybrid": "projector", "online": "mixed-kit", "onsite": "stream-kit"}, "online_requires_no_transport": true, "transport_by_site": {"Garden": "bus", "Harbor": "walk", "Studio": "ferry"}}`.

- Trace: `artifacts/runs/main-qwen-c5-17-eval/evaluation.jsonl[.gz]`, family `test-0046`, world `hypothetical`, turn 64. Recalled state: `["Garden", "online", "3000", "Tuesday", "students", "Cedar"]`. Canonical references absent from this prompt: `[]`.
- Trace: `artifacts/runs/main-qwen-c3-17-eval/evaluation.jsonl[.gz]`, family `test-0046`, world `hypothetical`, turn 64. Recalled state: `["Garden", "online", "3000", "Tuesday", "students", "Cedar"]`. Canonical references absent from this prompt: `[]`.

## qwen seed 17: C5-C3, only_first, test-0068

Category prevalence: 11/240 paired families.

**authorized world.** Oracle executable target: `["Garden", "hybrid", "7000", "Thursday", "specialists", "Willow", "walk", "mixed-kit"]`; required clarification: `[]`. The oracle appears here for analysis only.

| Method | Actual executable plan | Correct task | Overlapping flags |
|---|---|---|---|
| C5 | `["Garden", "hybrid", "7000", "Thursday", "specialists", "Willow", "walk", "mixed-kit"]` | True | none |
| C3 | `["Garden", "hybrid", "7000", null, "specialists", "Willow", "walk", "mixed-kit"]` | False | clarification_error, commitment_error, correct_recall_wrong_behavior, source_error |

Public dependency rules: `{"equipment_by_mode": {"hybrid": "mixed-kit", "online": "projector", "onsite": "stream-kit"}, "online_requires_no_transport": true, "transport_by_site": {"Garden": "walk", "Harbor": "bus", "Studio": "ferry"}}`.

- Trace: `artifacts/runs/main-qwen-c5-17-eval/evaluation.jsonl[.gz]`, family `test-0068`, world `authorized`, turn 64. Recalled state: `["Garden", "hybrid", "7000", "Thursday", "specialists", "Willow"]`. Canonical references absent from this prompt: `[]`.
- Trace: `artifacts/runs/main-qwen-c3-17-eval/evaluation.jsonl[.gz]`, family `test-0068`, world `authorized`, turn 64. Recalled state: `["Garden", "hybrid", "7000", "Thursday", "specialists", "Willow"]`. Canonical references absent from this prompt: `[]`.

**hypothetical world.** Oracle executable target: `["Studio", "hybrid", "7000", "Thursday", "specialists", "Willow", "ferry", "mixed-kit"]`; required clarification: `[]`. The oracle appears here for analysis only.

| Method | Actual executable plan | Correct task | Overlapping flags |
|---|---|---|---|
| C5 | `["Studio", "hybrid", "7000", "Thursday", "specialists", "Willow", "ferry", "mixed-kit"]` | True | none |
| C3 | `["Studio", "hybrid", "7000", null, "specialists", "Willow", "ferry", "mixed-kit"]` | False | clarification_error, commitment_error, correct_recall_wrong_behavior, source_error |

Public dependency rules: `{"equipment_by_mode": {"hybrid": "mixed-kit", "online": "projector", "onsite": "stream-kit"}, "online_requires_no_transport": true, "transport_by_site": {"Garden": "walk", "Harbor": "bus", "Studio": "ferry"}}`.

- Trace: `artifacts/runs/main-qwen-c5-17-eval/evaluation.jsonl[.gz]`, family `test-0068`, world `hypothetical`, turn 64. Recalled state: `["Studio", "hybrid", "7000", "Thursday", "specialists", "Willow"]`. Canonical references absent from this prompt: `[]`.
- Trace: `artifacts/runs/main-qwen-c3-17-eval/evaluation.jsonl[.gz]`, family `test-0068`, world `hypothetical`, turn 64. Recalled state: `["Studio", "hybrid", "7000", "Thursday", "specialists", "Willow"]`. Canonical references absent from this prompt: `[]`.

## qwen seed 17: C5-C3, only_second, test-0127

Category prevalence: 20/240 paired families.

**authorized world.** Oracle executable target: `["Studio", "onsite", "3000", "Tuesday", "specialists", null, "bus", "mixed-kit"]`; required clarification: `['partner']`. The oracle appears here for analysis only.

| Method | Actual executable plan | Correct task | Overlapping flags |
|---|---|---|---|
| C5 | `["Studio", "onsite", "3000", "Tuesday", "specialists", "Maple", "bus", "mixed-kit"]` | False | clarification_error, commitment_error, correct_recall_wrong_behavior |
| C3 | `["Studio", "onsite", "3000", "Tuesday", "specialists", null, "bus", "mixed-kit"]` | True | source_error |

Public dependency rules: `{"equipment_by_mode": {"hybrid": "stream-kit", "online": "projector", "onsite": "mixed-kit"}, "online_requires_no_transport": true, "transport_by_site": {"Garden": "walk", "Harbor": "ferry", "Studio": "bus"}}`.

- Trace: `artifacts/runs/main-qwen-c5-17-eval/evaluation.jsonl[.gz]`, family `test-0127`, world `authorized`, turn 64. Recalled state: `["Studio", "onsite", "3000", "Tuesday", "specialists", "Maple"]`. Canonical references absent from this prompt: `[]`.
- Trace: `artifacts/runs/main-qwen-c3-17-eval/evaluation.jsonl[.gz]`, family `test-0127`, world `authorized`, turn 64. Recalled state: `["Studio", "onsite", "3000", "Tuesday", "specialists", "Maple"]`. Canonical references absent from this prompt: `[]`.

**hypothetical world.** Oracle executable target: `["Studio", "onsite", "3000", "Saturday", "specialists", null, "bus", "mixed-kit"]`; required clarification: `['partner']`. The oracle appears here for analysis only.

| Method | Actual executable plan | Correct task | Overlapping flags |
|---|---|---|---|
| C5 | `["Harbor", "onsite", "3000", "Saturday", "specialists", "Maple", "ferry", "mixed-kit"]` | False | clarification_error, commitment_error, dependency_error, source_error |
| C3 | `["Studio", "onsite", "3000", "Saturday", "specialists", null, "bus", "mixed-kit"]` | True | source_error |

Public dependency rules: `{"equipment_by_mode": {"hybrid": "stream-kit", "online": "projector", "onsite": "mixed-kit"}, "online_requires_no_transport": true, "transport_by_site": {"Garden": "walk", "Harbor": "ferry", "Studio": "bus"}}`.

- Trace: `artifacts/runs/main-qwen-c5-17-eval/evaluation.jsonl[.gz]`, family `test-0127`, world `hypothetical`, turn 64. Recalled state: `["Harbor", "onsite", "3000", "Saturday", "specialists", "Maple"]`. Canonical references absent from this prompt: `[11]`.
- Trace: `artifacts/runs/main-qwen-c3-17-eval/evaluation.jsonl[.gz]`, family `test-0127`, world `hypothetical`, turn 64. Recalled state: `["Studio", "onsite", "3000", "Saturday", "specialists", "Maple"]`. Canonical references absent from this prompt: `[]`.
