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
PYTHONPATH=src python -m pcc.package
bash scripts/build_paper.sh
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
- [Confirmatory specification](STATISTICAL_PLAN.md), effective only with `configs/freeze.json`
- [Related work and novelty matrix](literature/NOVELTY_MATRIX.md)
- [Decisions](DECISIONS.md), [AI assistance](AI_ASSISTANCE.md),
  [conference requirements](paper/CONFERENCE_REQUIREMENTS.md)
- `data/manifests/`: family ownership and exact hashes; regenerate from code
- `configs/run_exclusions.json`: retained failed/invalid engineering runs
- `artifacts/run_registry.jsonl`: actual status, revision, commit, budget and paths
- [Descriptive reporting extension](analysis/README.md): explicitly post-baseline
  domain/structure, training-exposure and resource tables; no new confirmatory tests.
  `bash analysis/regenerate_all.sh` regenerates both reporting layers and the PDF.

Main results, ablations, external validation, independent-family confirmation,
human review and final manuscript evidence remain subject to pilot gates. The
CLI refuses locked-test evaluation without a hashed freeze record. Never create
that record simply to bypass a failing gate.

## Resumable execution

`pcc.pilot_campaign` and `pcc.final_pilot_checks` are bounded pilot controllers.
After the evidence gates, measured allocation and analysis hashes are frozen,
`PYTHONPATH=src .venv/bin/python -m pcc.campaign --dry-run` prints the exact main
queue; omit `--dry-run` to execute it using the SSH environment variables above.
The local controller mirrors artifacts every minute and after each stage. It stops
on errors, unknown GPU occupants, the reservation ceiling or low local storage.

Failed jobs retain their original IDs and cost. To resume a failed training stage,
record an infrastructure reason and fresh run ID in ignored
`artifacts/campaign_resume.json`, with the last valid `training/optimizer.pt` path.
Only `run_id`, `checkpoint` and `reason` are accepted; experimental settings cannot
be changed through this mechanism. Downstream adapter paths follow the audited
alias. A completed run cannot be replaced through infrastructure resume.

Example override (use the actual failed run ID and checkpoint):

```json
{"main-qwen-c3-17-r0-fit":{"run_id":"main-qwen-c3-17-r0-fit-resume1","checkpoint":"artifacts/runs/main-qwen-c3-17-r0-fit/training/optimizer.pt","reason":"Documented infrastructure interruption"}}
```

Exact source snapshots, model revisions, dataset hashes, configuration and adapter
checksums accompany later runs. Identical completed safetensors may share local
hard links; all named artifacts remain available. Active checkpoint writes are
atomic. No base model or bulk run trace belongs in Git.

The recorded [serialization amendment](reports/SERIALIZATION_AMENDMENT_002.md)
adds a narrowly scoped, frozen restart map for four completed C1 stages found
scientifically invalid by a CPU grammar audit. This is distinct from ordinary
infrastructure resume. The original freezes and excluded artifacts remain; all
spending is counted. `configs/serialization_restarts.json` changes only IDs and
downstream artifact paths. It cannot alter seeds, samples or training settings.

Repair validation is reproduced with `analysis/audit_serialization.py` in the
inference environment, the two modes of `analysis/run_serialization_pilots.py`
(the second takes `--reference-refresh`), and
`PYTHONPATH=src .venv/bin/python analysis/serialization_report.py` locally.
These controllers require the main boundary hold and exclusive queue lock.
They reuse recorded pilot supervision; see the run registry for its exact hashes.
Malformed or capped responses remain failures and are never retried for a score.
The amended runtime forecast is diagnostic and does not change the fixed grid.
