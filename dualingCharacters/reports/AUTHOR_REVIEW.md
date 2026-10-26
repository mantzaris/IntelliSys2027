# Author-review evidence package

This is not a submission-ready paper. Human scientific review remains required.

Measured reservation: 72.742 GPU-hours; inference 1,972,888,491 input and 124,013,239 output tokens; 78,725,120 training input tokens. Actual dollar cost is unknown.

## Historical pilots (trained entries excluded for serialization mismatch)

| Run | Paired success | Conversations |
|---|---:|---:|
| pilot-v4-qwen-base | 0.3750 (16 families) | 0.4375 |
| pilot-v4-qwen-c3-eval | 0.3125 (16 families) | 0.4062 |
| pilot-v4-qwen-c5-eval | 0.3750 (16 families) | 0.5000 |
| pilot-v4-phi-base | 0.2500 (16 families) | 0.3125 |
| pilot-v4-phi-c5-eval | 0.1250 (16 families) | 0.2188 |

Excluded-format pilot C5−C3 difference +0.0625, 95% family interval [-0.1875, +0.3125]. These trained pilots are invalid intended-method efficacy evidence due to the serialization mismatch; all measurements remain for audit.

## Main grid

| Model | Condition | Seeds | Paired success | Status |
|---|---|---:|---:|---|
| qwen | C1 | 3 | 0.7041666666666666 | complete |
| qwen | C2 | 3 | 0.7583333333333333 | complete |
| qwen | C3 | 3 | 0.7611111111111111 | complete |
| qwen | C4 | 3 | 0.7236111111111111 | complete |
| qwen | C5 | 3 | 0.7222222222222222 | complete |
| qwen | C6 | 2 | 0.73125 | partial |
| qwen | A1 | 3 | 0.6958333333333333 | complete |
| qwen | A2 | 3 | 0.4652777777777778 | complete |
| qwen | A3 | 3 | 0.7444444444444445 | complete |
| phi | C1 | 3 | 0.6319444444444444 | complete |
| phi | C3 | 3 | 0.7583333333333333 | complete |
| phi | C5 | 3 | 0.7166666666666667 | complete |

qwen C5-C1: +0.0181, paired seed/family interval [-0.08472222222222223, 0.1625]; 3 seeds.

qwen C5-C2: -0.0361, paired seed/family interval [-0.08055555555555556, 0.004166666666666667]; 3 seeds.

qwen C5-C3: -0.0389, paired seed/family interval [-0.08333333333333333, 0.001388888888888889]; 3 seeds.

qwen C5-C4: -0.0014, paired seed/family interval [-0.05416666666666667, 0.06527777777777778]; 3 seeds.

qwen C5-A1: +0.0264, paired seed/family interval [-0.025, 0.09444444444444444]; 3 seeds.

qwen C5-A2: +0.2569, paired seed/family interval [-0.03333333333333333, 0.45]; 3 seeds.

qwen C5-A3: -0.0222, paired seed/family interval [-0.08055555555555556, 0.041666666666666664]; 3 seeds.

phi C5-C1: +0.0847, paired seed/family interval [-0.020833333333333332, 0.17916666666666667]; 3 seeds.

phi C5-C3: -0.0417, paired seed/family interval [-0.09722222222222222, 0.018055555555555554]; 3 seeds.

## Unfinished or limited evidence

Human-review packet: 0 actual outputs; no human ratings have been supplied.
External evaluation uses a fixed 50-question subset and an adapted independent-family judge; it is not an official comparable LongMemEval score. Structured synthetic planning and scripted users limit naturalistic and domain-transfer claims.
No coalition or narrative-profile benefit follows merely from peer messages, character labels, or a positive point estimate. Consult the ablations and mechanism diagnostics.
Empty tables and panels identify unexecuted requirements. The actual run registry, not queued commands, determines completion.

Regenerate: `PYTHONPATH=src .venv/bin/python -m pcc.package`, then `bash scripts/build_paper.sh`.
