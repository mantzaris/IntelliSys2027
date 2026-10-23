# Persistent Character Conflict for Learning Conversational Recovery

Author-directed research in progress. Read [RUN_STATE.md](RUN_STATE.md) for the
latest executed phase and unfinished requirements. Do not interpret engineering
profiles or pilot comparisons as confirmatory results.

All work is under this directory on `main`; the author pushes commits. Bulk data,
raw traces, adapters, optimizer checkpoints and model caches are Git-ignored.
Small manifests, configs, source, tests, compact tables and reports are versioned.

## Reproduce

Requires Python >=3.11. The existing pod supplies PyTorch 2.8.0+cu128. Create an
isolated `venv --system-site-packages`, install `requirements-gpu.txt`, and preserve
the resolved `pip freeze` under `artifacts/environment/`. Do not replace the pod's
global environment. Set `HF_HOME` to an adequately sized cache on the pod.

```bash
python -m pip install -r requirements-gpu.txt
python scripts/download_models.py
PYTHONPATH=src python -m pytest -q
PYTHONPATH=src python -m pcc.cli manifests
PCC_CODE_COMMIT=$(git rev-parse HEAD) PYTHONPATH=src python -m pcc.cli profile \
  --config configs/profile_bf16.json --run-id my-bf16-profile --families 1 --horizon 16
PCC_CODE_COMMIT=$(git rev-parse HEAD) PYTHONPATH=src python -m pcc.cli pilot \
  --config configs/pilot_c5.json --run-id my-c5-pilot --families 4 --horizon 16
PYTHONPATH=src python -m pcc.cli analyze
PYTHONPATH=src python -m pcc.diagnostics
```

These commands run actual GPU inference and LoRA optimization. They create a
unique run directory and refuse overwriting. Use only one GPU worker; the runner
checks other GPU processes and takes an exclusive lock. Its conservative active
GPU accounting includes model-load and reserved process time and failed runs.
The 96-hour authorization is a ceiling, not an allocation target. Dollars remain
unknown until an actual pod rate is supplied. Source-only tests run locally without
PyTorch; use this project's `.venv/bin/python` on this host, whose default `python`
is an obsolete interpreter.

For local/pod mirroring, set `PCC_SSH_HOST`, `PCC_SSH_PORT`, and optionally
`PCC_SSH_KEY` and run `bash scripts/sync.sh push` or `pull`. Model caches are not
copied back. The current pod has no verified separate persistent volume; frequent
local checkpoint copies are required. Do not rely on the container as the only copy.

## Scientific audit

- [Method and information boundaries](METHOD.md)
- [Draft statistical plan](STATISTICAL_PLAN_DRAFT.md), not yet frozen
- [Related work and novelty matrix](literature/NOVELTY_MATRIX.md)
- [Decisions](DECISIONS.md), [AI assistance](AI_ASSISTANCE.md),
  [conference requirements](paper/CONFERENCE_REQUIREMENTS.md)
- `data/manifests/`: family ownership and exact hashes; regenerate from code
- `configs/run_exclusions.json`: retained failed/invalid engineering runs
- `artifacts/run_registry.jsonl`: actual status, revision, commit, budget and paths

Main results, ablations, external validation, independent-family confirmation,
human review and final manuscript evidence remain subject to pilot gates. The
CLI refuses locked-test evaluation without a hashed freeze record. Never create
that record simply to bypass a failing gate.
