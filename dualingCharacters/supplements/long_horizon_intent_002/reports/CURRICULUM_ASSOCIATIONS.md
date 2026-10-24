# Curriculum and outcome associations — descriptive only

Each row joins completed, eligible artifacts for one model/condition/training seed. Partially completed training budgets are explicitly marked. Differences in curriculum, prompt length, target exposure and routing are entangled; this table does not identify a causal mechanism. Source-visible contradictions are observable flags, not proof of deliberate deception.

| Model | Condition | Seed | Fits | Input tokens | Target tokens | R1 recovery windows / families contributing loss | R1 top-five recovery-token share | Shared memory changes / opportunities | Paired success |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| phi | base | 17 | 0/0 | 0 | 0 | n/a | — | 0/0 | 11.25% |
| qwen | A1 | 17 | 2/2 | 2,097,152 | 80,051 | 11 / 6 | 47.4% | 4982/7200 | 70.42% |
| qwen | A1 | 29 | 2/2 | 2,097,152 | 80,256 | 23 / 14 | 26.9% | 4964/7200 | 75.42% |
| qwen | C1 | 17 | 2/2 | 2,097,152 | 97,683 | 14 / 9 | 37.4% | 0/0 | 77.50% |
| qwen | C1 | 29 | 2/2 | 2,097,152 | 96,822 | 17 / 11 | 34.6% | 0/0 | 57.50% |
| qwen | C1 | 43 | 2/2 | 2,097,152 | 96,813 | 9 / 5 | 57.2% | 0/0 | 76.25% |
| qwen | C3 | 17 | 2/2 | 2,097,152 | 83,466 | 33 / 18 | 17.3% | 4967/7200 | 73.75% |
| qwen | C3 | 29 | 2/2 | 2,097,152 | 83,913 | 23 / 13 | 25.6% | 4956/7200 | 75.42% |
| qwen | C3 | 43 | 1/2 | 1,048,576 | 41,779 | pending | — | 2480/3600 | pending |
| qwen | C4 | 17 | 2/2 | 2,097,152 | 78,417 | 14 / 8 | 39.0% | 6747/7200 | 74.58% |
| qwen | C4 | 29 | 2/2 | 2,097,152 | 79,997 | 20 / 12 | 29.8% | 6779/7200 | 68.75% |
| qwen | C5 | 17 | 2/2 | 2,097,152 | 79,238 | 31 / 17 | 20.8% | 5034/7200 | 70.00% |
| qwen | C5 | 29 | 2/2 | 2,097,152 | 79,443 | 10 / 7 | 57.1% | 5004/7200 | 75.00% |
| qwen | base | 17 | 0/0 | 0 | 0 | n/a | — | 0/0 | 27.92% |

Equal packed input-token budgets do not imply equal supervised target-token exposure. The 50:50 sampler alternates examples; it does not guarantee a 50:50 target-token split. Repeated recovery occurrences are not independent recovery examples. Source coverage is an analysis-only measurement; it did not determine policy inputs or select an outcome subset.

The CSV/JSON retain per-round eligibility, distinct loss-contributing windows/families, repeats, top-one and top-five shares, actual verified-model-recovery target tokens, peer routing and canonical-source coverage. Counts of changed memory include bounded notes as implemented, not necessarily false commitments.
