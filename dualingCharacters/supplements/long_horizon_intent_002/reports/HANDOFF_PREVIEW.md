# Intent 002 handoff preview — session still active

Start: 2026-10-24T13:06:05+00:00 (2026-10-24T09:06:05-04:00). Preview: 2026-10-24T15:30:05.243794+00:00; work continues until the recorded deadline.
Actual elapsed at report: 2.400 hours. One shared deadline: 2026-10-24T21:06:05+00:00.

Local main: `993b9196887cbbfad2a5a770a103a5f003a5aa16`; starting commit `be7c06e`. Nothing pushed, published or submitted. All 58 core, 21 review and 34 intent scientific files verify unchanged.

Core: 51/241 stages complete, 6 newly completed this session. Active: `main-qwen-a1-29-eval`. Next: `main-qwen-c1-43-r0-collect`. Current failed queue stages: 0. Historical excluded artifacts remain preserved and listed in HANDOFF_STATE.json. No infrastructure retries were needed.

## Current core evidence — interim until planned seed sets complete

| Model | Condition | Seed | Paired success /240 |
|---|---|---:|---:|
| qwen | base | 17 | 67 |
| phi | base | 17 | 27 |
| qwen | C1 | 17 | 186 |
| qwen | C3 | 17 | 177 |
| qwen | C4 | 17 | 179 |
| qwen | C5 | 17 | 168 |
| qwen | A1 | 17 | 169 |
| qwen | C1 | 29 | 138 |
| qwen | C3 | 29 | 181 |
| qwen | C4 | 29 | 165 |
| qwen | C5 | 29 | 180 |

| Contrast | Seed | Difference, pp | Family 95% interval, pp | Both / only C5 / only control / neither |
|---|---:|---:|---|---|
| C5-C3 | 17 | -3.75 | [-8.33, 0.83] | 157 / 11 / 20 / 52 |
| C5-C3 | 29 | -0.42 | [-2.50, 1.67] | 177 / 3 / 4 / 56 |
| C5-C1 | 17 | -7.50 | [-11.25, -4.17] | 167 / 1 / 19 / 53 |
| C5-C1 | 29 | 17.50 | [11.67, 23.33] | 129 / 51 / 9 / 51 |

These one-seed intervals preserve paired scenario families; they do not represent training-seed uncertainty or equivalence. Complete-seed frozen analysis is retained in the original tables and `complete_seed_contrasts.json`. Do not average unmatched seed sets to create a contrast.

## New evidence and unfinished requirements

20 fits have exact loss-exposure reconstruction. See [progress](PROGRESS_REPORT.md), [clarification/source audits](clarification_audit.csv), [temporal source audit](source_dynamics_selected_turns.csv), [illustrations](ILLUSTRATIVE_APPENDIX.md), and [claims](CLAIM_TO_EVIDENCE.md).
The existing horizon interaction is pending its actual 32/128-turn runs. Dynamic 64-turn analyses retain initial failures and show that final correctness can coexist with substantial intermediate reversion; source access changes with scripted requests. These are exploratory associations, not causal memory/retrieval effects.
Fresh intent inference, timing allocation, GPU validation of the natural-language interface, and human ratings remain pending. The 16-family benchmark, disjoint engineering cases, private ledgers, balanced tiers, common runner, scoring/blinding and deadline controls are implemented and frozen. No new qualitative performance, crossover or robustness benefit is claimed.

## Resource reconciliation

Before session: 21.4731 reserved GPU-hours. During session through 2026-10-24T15:29:08.730570+00:00: 2.3249 hours. Cumulative: 23.7981/96; remaining: 72.2019; after 0.5-hour contingency: 71.7019. Review supplement: 0.0000/2; intent extension: 0.0000/2.
Core forecast total: expected 80.31, conservative 88.06 reserved hours. This is a forecast, not permission to shrink cells or spend beyond 96 hours. Pod elapsed: 95138 seconds at snapshot; this is separate from reserved GPU time and sampled utilization. Actual dollar rate is unknown.

## Human review and paper package

The original 60-action packet is preserved; actual annotation counts are in LEGACY_HUMAN_PACKET_STATUS.json. The original 120-prose packet awaits its required natural-language runs. The intent packet is separate and awaits actual outputs; no items or human ratings were fabricated and no raters were contacted.
[Figures](INTENT_FIGURES.md) · [author-review manuscript section](../MANUSCRIPT_SECTION.md) · [compiled draft](draft/intent_author_review.pdf) · [provenance](PROVENANCE.json) · [reproduction](../README.md). This is incomplete evidence and an author-review draft, not a complete submission or acceptance guarantee.

## Ownership and recovery

Core controller PID 787315; review coordinator PID 1291869. Current remote GPU processes: ``. The healthy core continues separately under its original authorization; it was not stopped to end this session.
Core state/log: `artifacts/campaign_state.json`, `artifacts/campaign_controller.log`, `artifacts/campaign_configs/<run_id>.log`. Core ownership lock: `artifacts/campaign.lock`; remote GPU lock: `artifacts/gpu.lock`. Review state: `artifacts/review_001/controller_state.json`. Intent is disabled, with no new background waiter. Older optional work remains behind its unresolved priority guard.
Read-only check: `PYTHONPATH=src .venv/bin/python -m supplements.long_horizon_intent_002.operations monitor`. Integrate completed evidence: `PYTHONPATH=src .venv/bin/python -m supplements.long_horizon_intent_002.regenerate`. Verify mirrors: `PYTHONPATH=src .venv/bin/python -m supplements.long_horizon_intent_002.operations mirror`.
For infrastructure recovery, first prove both original controller and GPU worker stopped; a dropped SSH connection is insufficient. Preserve/mirror partials and resource records, use the original `artifacts/campaign_resume.json` aliases and valid atomic optimizer checkpoint where supported, and allow at most two retries of the same infrastructure fault. Never rerun a completed evaluation for a different score. See the unchanged [recovery procedure](../../../reports/overnight_20261024T023622Z/RECOVERY.md). Scientific defects require a documented safe-boundary hold and preserved originals.

## Next author decisions

No routine decision is needed for the healthy original core queue. Later review: (1) assess the narrower claims supported by seed variation, intermediate reversion and source access; (2) review the authored intent ledgers/rubric and authorize a later execution window if desired, retaining existing GPU caps; (3) arrange independent human raters once the required outputs exist. No permission is inferred from elapsed time.
