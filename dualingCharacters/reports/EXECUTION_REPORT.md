# Execution and evidence report — author review required

Generated from saved run records and existing deterministic analyses. Scheduled jobs are not counted as observations. No submission or publication has occurred.

## 1. What ran

52/241 eligible scheduled core stages have completed. Stage counts include collection, fitting, evaluation and validation; they are not independent trained models.

Hardware: one existing RunPod NVIDIA RTX 6000 Ada, 49,140 MiB reported VRAM; PyTorch 2.8.0+cu128, CUDA 12.8 and driver 595.91.07. Hardware inspection is recorded in `RUN_STATE.md`. BF16 rank-8 LoRA performs actual parameter updates; vLLM inference shares the backbone across role contexts.

Recorded project consumption: 24.544/96 reserved GPU-hours, including failed and excluded attempts; 667,578,339 inference input tokens, 41,823,888 generated output tokens and 24,199,168 training input tokens. Observed pod interval: 26.443 hours, which is not total billed lifetime. Actual hourly rate and dollar cost are unknown.

Reproduce the package from saved artifacts:

```bash
cd dualingCharacters
bash analysis/regenerate_all.sh
PYTHONPATH=src .venv/bin/python analysis/progress.py
```

Print the fixed queue with `PYTHONPATH=src .venv/bin/python -m pcc.campaign --dry-run`. Execute it only after confirming that the existing controller has stopped; the authorized SSH environment and resume procedure are in `README.md`. Exact model revisions are in `configs/models.json`. No base-model cache or bulk checkpoint belongs in Git.

| Model | Training condition | Completed seeds | Paired success | Seed SD |
|---|---|---:|---:|---:|
| qwen | C1 | 2/3 | 0.6750 | 0.1414 |
| qwen | C2 | 0/3 | pending | — |
| qwen | C3 | 2/3 | 0.7458 | 0.0118 |
| qwen | C4 | 2/3 | 0.7167 | 0.0412 |
| qwen | C5 | 2/3 | 0.7250 | 0.0354 |
| qwen | C6 | 0/3 | pending | — |
| qwen | A1 | 2/3 | 0.7292 | 0.0354 |
| qwen | A2 | 0/3 | pending | — |
| qwen | A3 | 0/3 | pending | — |
| phi | C1 | 0/3 | pending | — |
| phi | C3 | 0/3 | pending | — |
| phi | C5 | 0/3 | pending | — |

Condition means above may cover different completed seed sets. Do not compare incomplete aggregates across conditions; use matched-seed contrasts and the per-seed tables. The shared untrained reference is not independent replication.

## 2. Primary effect and uncertainty

Pending: no complete matched three-seed contrast is available.

This is C5 minus C3 on antagonist-free 64-turn paired success. The corrected small pilots are engineering checks, not substitutes for this contrast. Excluded serialization runs remain in historical records and resource totals.

## 3. What the controls support

| Qwen contrast | Complete three-seed estimate |
|---|---|
| C5−C4: third character | Pending: no complete matched three-seed contrast is available. |
| C5−A1: narrative versus motives | Pending: no complete matched three-seed contrast is available. |
| C5−A2: private history | Pending: no complete matched three-seed contrast is available. |
| C5−A3: peer interaction | Pending: no complete matched three-seed contrast is available. |

A primary advantage alone cannot establish narrative, persistence, interaction or coalition mechanisms. Character choices and coordination candidates are recorded separately in `main_character_diagnostics.json`; peer-message counts are not proof of a coalition. Severity was not equalized by the common opportunity cap.

## 4. Transfer and independent-family confirmation

All main tests remove antagonists; their estimates above directly assess transfer into the common scaffold. The additional fixed horizon, larger-memory, unfamiliar-fault and recovery settings are distinct diagnostics.

Phi independent-model C5−C3: Pending: no complete matched three-seed contrast is available.

Saved transfer aggregate rows: 6 (includes main and common-subset reference rows; not a count of independent experiments). Saved external scoring rows: 0. LongMemEval uses a predetermined 50-question subset with adapted retrieval and judging; it is not an official comparable score. Unseen-profile supplement status: `deferred_to_review_001_scheduler`.

## 5. Exact unfinished requirements and weaknesses

Unfinished scheduled stages by command: collect=52, evaluate=26, external=8, fit=52, horizon128=5, horizon32=5, judge=2, larger-memory=5, natural=3, recovery=13, short=13, unfamiliar=5. Every exact run ID and state is in `reports/tables/execution_report_trace.json`.

Human review: `packet_outputs_pending`; annotations: `not_supplied`. Two independent raters and subsequent adjudication remain required unless actual completed sheets are supplied. Scientific author review, claim approval and a final current conference-policy check remain outstanding.

Limitations include scripted users, a small shared categorical task schema, concentrated ambiguity cases, only three training seeds, limited power for a five-point effect, teacher-supplied targets, fixed retrieval, potentially unequal interference severity and jointly satisfiable antagonist-owned options. Frozen history-dependent characters are not jointly learned adversaries. The memory study cannot establish AGI, consciousness, universal robustness or general long-horizon planning.

## 6. Candid evidence assessment

Further execution is required. This is an incomplete evidence package, not a submission-ready paper.

All interpretations remain candidates for human scientific review. Failed runs, negative findings and missing cells must remain visible.
