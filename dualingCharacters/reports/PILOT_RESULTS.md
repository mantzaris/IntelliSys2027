# Executed pilot evidence — not confirmatory results

Generated from saved run artifacts by `PYTHONPATH=src python -m pcc.reporting`.

| Run | Before paired success | After paired success | GPU minutes | Status |
|---|---:|---:|---:|---|
| pilot-c3-002 | 0.250 | 0.250 | 7.50 | Pilot, one seed |
| pilot-c5-001 | 0.250 | 0.500 | 7.95 | Pilot, one seed |

Exploratory C5−C3 paired difference: +0.250; family-bootstrap 95% interval [+0.000, +0.750]. This four-family interval does not estimate training-seed variation and cannot establish the primary hypothesis.

Both evaluated learners had antagonists removed. This is an antagonist-free pilot retest, not established general transfer. The revised mandatory communication protocol requires a fresh mechanism audit.

Main three-seed results, learned ablations, independent-family replication, external scores, horizon curves, fixed-state recovery curves and human validation remain pending. Empty cells and absent figures must not be filled with invented measurements.

Invalid/engineering-only runs are retained in `configs/run_exclusions.json`; their resource usage remains counted.
