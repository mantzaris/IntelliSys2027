# Author-review evidence package

This is not a submission-ready paper. Human scientific review remains required.

Measured reservation: 3.670 GPU-hours; inference 97,404,649 input and 6,193,931 output tokens; 1,785,856 training input tokens. Actual dollar cost is unknown.

## Matched learning pilots (one seed; 32 turns)

| Run | Paired success | Conversations |
|---|---:|---:|
| pilot-v4-qwen-base | 0.3750 (16 families) | 0.4375 |
| pilot-v4-qwen-c3-eval | 0.3125 (16 families) | 0.4062 |
| pilot-v4-qwen-c5-eval | 0.3750 (16 families) | 0.5000 |
| pilot-v4-phi-base | 0.2500 (16 families) | 0.3125 |
| pilot-v4-phi-c5-eval | 0.1250 (16 families) | 0.2188 |

Exploratory C5−C3 difference +0.0625, 95% family interval [-0.1875, +0.3125]. This does not estimate training-seed variation or establish H1.

## Main grid

| Model | Condition | Seeds | Paired success | Status |
|---|---|---:|---:|---|
| qwen | C1 | 0 | — | pending |
| qwen | C2 | 0 | — | pending |
| qwen | C3 | 0 | — | pending |
| qwen | C4 | 0 | — | pending |
| qwen | C5 | 0 | — | pending |
| qwen | C6 | 0 | — | pending |
| qwen | A1 | 0 | — | pending |
| qwen | A2 | 0 | — | pending |
| qwen | A3 | 0 | — | pending |
| phi | C1 | 0 | — | pending |
| phi | C3 | 0 | — | pending |
| phi | C5 | 0 | — | pending |

## Unfinished or limited evidence

Human-review packet: 0 actual outputs; no human ratings have been supplied.
External evaluation uses a fixed 50-question subset and an adapted independent-family judge; it is not an official comparable LongMemEval score. Structured synthetic planning and scripted users limit naturalistic and domain-transfer claims.
No coalition or narrative-profile benefit follows merely from peer messages, character labels, or a positive point estimate. Consult the ablations and mechanism diagnostics.
Empty tables and panels identify unexecuted requirements. The actual run registry, not queued commands, determines completion.

Regenerate: `PYTHONPATH=src .venv/bin/python -m pcc.package`, then `bash scripts/build_paper.sh`.
