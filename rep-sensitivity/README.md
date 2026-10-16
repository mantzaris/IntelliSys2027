# Rep-sensitivity

Controlled experiments on duplicated, near-duplicated and complementary reports
in hierarchical LLM systems. Everything for this study lives in this directory.
Work and commits stay on `main`; the user performs the push.

**Status at 2026-10-16 06:45 UTC:** the Qwen3 development pilot is complete;
Qwen3 and Phi-4 passed the competence and summary gates. The frozen validation
pipeline is executing. At this checkpoint, this is not a completed
held-out study. See `DECISIONS.md`, `PROTOCOL.md`, the machine-readable manifests
and the actual `results/*/analysis.json` files. A compiled anonymous working draft
is in `manuscript/main.pdf`; it is explicitly incomplete and not human-reviewed.
Do not present implemented controls as completed experiments.
Later stage completion is recorded in `records/study-report-status.json` and,
only after complete raw-output audits and PDF checks, `records/review-package.json`.

## Layout

- `src/rep_sensitivity/`: generators, two verifiers, schemas, reports, independent
  graph representations, policies, adapters, replay, live workers, controls and analysis.
- `configs/`: versioned designs, analysis contrasts, and clearly blocked provisional runs.
- `tests/`: scientific integrity and execution-resume checks.
- `records/`: small model/environment manifests, checksums, run audits and PDF checks.
- `results/`: compact regenerated tables, decision records and exported figures.
- `artifacts/runs/`: ignored immutable raw prompts/responses, frozen corpora and events;
  synchronized between RunPod and this local project. Never include bulk artifacts in Git.
- `artifacts/models/`, `.venv/`, `logs/`: ignored reproducible caches and operational files.

## Local setup and integrity checks

```bash
cd rep-sensitivity
python3.10 -m venv .venv
.venv/bin/pip install -r requirements-analysis.txt
.venv/bin/pip install -e . --no-deps
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
PYTHONPATH=src .venv/bin/python -m rep_sensitivity.cli generate --config configs/pilot-v7.json
```

`generate` writes an immutable corpus and verifies the actual trajectory/call
counts. It does not contact a model. All scheduling instances are checked by an
event-sweep and an independently coded time-slot verifier. Workflow evaluation
uses recursive and stack-based implementations.

## Existing RunPod environment

The project is `/workspace/rep-sensitivity` on the existing RTX 6000 Ada pod.
`scripts/sync.sh` defaults to the user-provided direct SSH endpoint and the working
RSA key. Override `RUNPOD_HOST`, `RUNPOD_PORT`, `RUNPOD_KEY`, `RUNPOD_PROJECT`, and
`RUNPOD_KNOWN_HOSTS` as needed. Host-key checking remains enabled. Never add private
keys to the repository. The old unrelated `runpod-thermo` SSH alias is not used.

```bash
bash scripts/sync.sh push-source
bash scripts/sync.sh pull
# Optional bounded hourly mirror, copies once per minute:
bash scripts/mirror_loop.sh
```

For reproducing the isolated GPU environment on the same existing pod:

```bash
cd /workspace/rep-sensitivity
python -m venv --system-site-packages .venv
.venv/bin/pip install --no-cache-dir 'vllm==0.10.2' 'transformers==4.55.4' \
  'huggingface-hub==0.34.4' 'openai==1.109.1' 'matplotlib==3.10.7' 'pytest==8.4.2'
.venv/bin/python scripts/download_models.py qwen3
.venv/bin/python scripts/check_model_snapshot.py qwen3
.venv/bin/python scripts/download_models.py phi4
.venv/bin/python scripts/check_model_snapshot.py phi4
```

Exact resolved dependencies are in `records/environment/pip-freeze-gpu.txt`.
Downloads reuse pinned Hub revisions when metadata already exists. Mistral-7B requires the official v3 SentencePiece file under the filename expected
by Transformers. Run `scripts/prepare_mistral_tokenizer.py` after downloading it;
the derived directory preserves bytes and records its aliases and checksums. Public access
uses no private token. Qwen2.5-7B's reproducible weight cache was removed after its
completed check to make room for newer weights; all its raw experiment data remain.
The selected families are Qwen3-14B (BF16, non-thinking) and Microsoft Phi-4
(BF16). Both passed the unchanged development competence gate and summary check;
their pinned revisions and native chat templates are recorded under
`records/models/`. Mistral-Small-24B INT8 failed the gate and its reproducible
weight cache was evicted. Historical Mistral/Nemo checks contain a
tokenizer-interface limitation; they are development diagnostics, not a clean
model ranking.

## Development, pilot and validation

```bash
.venv/bin/python scripts/resume_archived.py \
  artifacts/runs/competence-qwen3-v7 --model qwen3
# For a new run, snapshot the current source before launching:
.venv/bin/python scripts/launch_snapshot.py --entry development_gate -- --model phi4
```

Only one inference process should occupy the GPU. Re-running an accepted request
reuses its immutable output, including malformed responses. A ledger writer lock
prevents simultaneous writers. New runs archive their implementation and reject
incompatible resume attempts. No API-based judge or paid inference service exists
in this package.

`pilot.json` documents the original 1,152-trajectory pilot, stopped for interface
failure. It requires its historical implementation (`a90bf20`) for exact replay;
the current runner refuses to silently run old configurations with new prompts.
The v2–v7 competence runs are development revisions, not repeated independent
confirmatory experiments. Raw prompts, sampling settings and model identifiers
are stored per call for exact reconstruction even when historical runners differ.

The v5 Qwen3 competence check met its initial gate. The v7 semantic correction
separates predicate criteria from applicability and requires fresh development
validation; earlier runs remain archived. `pilot-v7.json` is the
24-pair development pilot with benchmark v2, two policies, two repetitions, and
value-free ancestry metadata at the summary-only root. Validation was frozen after
pilot output-cap and runtime checks in `configs/frozen/validation-v7.json`.
`validation-candidate-v7.json` and `main-provisional.json` are design inputs,
not evidence of completed execution. The main runner rejects provisional designs.
To execute a scientifically frozen replacement, use:

```bash
.venv/bin/python scripts/resume_archived.py artifacts/runs/pilot-v7 --model qwen3
.venv/bin/python scripts/resume_archived.py artifacts/runs/validation-v7 --model phi4
PYTHONPATH=src .venv/bin/python -m rep_sensitivity.cli run \
  --config configs/ACTUAL-FROZEN-MAIN.json --model SELECTED_MODEL
```

The uppercase main path is an explicitly pending artifact. The active controller
creates `configs/frozen/main-v7.json` after completed validation. Freeze sample
size, model allocation, templates, policies and analysis before held-out inference;
never edit a frozen artifact in place. Do not start these commands concurrently
with the active controller.

## Supporting controls and live workers

The provisional configurations enumerate targeted contrasts and their unresolved
limitations. Execution is blocked until a frozen replacement is created following
replay validation. The commands once frozen are:

```bash
PYTHONPATH=src .venv/bin/python -m rep_sensitivity.cli controls \
  --config configs/ACTUAL-FROZEN-CONTROLS.json --model SELECTED_MODEL
PYTHONPATH=src .venv/bin/python -m rep_sensitivity.cli live \
  --config configs/ACTUAL-FROZEN-LIVE.json --model SELECTED_MODEL
```

Live workers receive minimal role-specific data with actual access recorded.
Four essential verification scopes remain present. Fixed-resource arms bound
combined tokenized inputs plus output allowances to the four-worker baseline;
this token budget does not assert equal FLOPs, latency or independent errors.

## Offline analysis and manuscript

```bash
bash scripts/sync.sh pull
PYTHONPATH=src MPLCONFIGDIR=artifacts/matplotlib .venv/bin/python -m rep_sensitivity.analysis \
  artifacts/runs/pilot-v7 results/pilot-v7 --bootstrap 10000
.venv/bin/python scripts/audit_runs.py artifacts/runs/pilot-v7
.venv/bin/python scripts/build_study_figures.py
.venv/bin/python scripts/build_manuscript_tables.py
.venv/bin/python scripts/build_study_report.py
(cd manuscript && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex)
.venv/bin/python scripts/check_manuscript.py
```

The analysis exports CSV/JSON and PDF/PNG plots; each result links to a manifest
hash and source-score hash. Tables include only completed competence runs.
Main contrasts use complete base clusters, with model-specific reporting and
separate scheduling/workflow results. Calibration uses valid distributions only
and records its denominator. Batch-wall allocation is explicitly distinguished
from measured request latency and GPU kernel time.
Claim metrics are recomputed from immutable responses with a recorded scorer hash.
Equal numeric integer/float values are equivalent; Boolean values remain distinct.
`paired_correctness.csv` reports correct responsiveness/stability, and
`confidence_changes.csv` describes confidence changes among unchanged choices with
its denominator. These descriptive subsets are not additional primary tests.

Measured resource and precision planning is available with
`python -m rep_sensitivity.planning SOURCE_RUN TARGET_CONFIG OUTPUT_JSON`.
Unmeasured model/policy cells remain unavailable rather than receiving assumed
throughput. `scripts/audit_benchmark.py` checks deterministic corpus balance before
model evaluation; its development audit explicitly records the absence of NONE
cases in the 24-pair prefix.

The official `svproc` template files are retained with a source/archive hash.
The draft's abstract length, bibliography citations and LaTeX overflow checks are
automated; human scientific and layout review remains necessary. See
`SCIENTIFIC_REVIEW.md` and `CONFERENCE.md` before considering any submission.

To run a fresh v7 development gate and summary check while reusing a loaded
engine, use `.venv/bin/python scripts/launch_snapshot.py --entry development_gate -- --model qwen3 --pilot`
(or `--model phi4` without `--pilot`). A failed gate prevents further study execution.
To resume an archived protocol after source changes, use
`.venv/bin/python scripts/resume_archived.py artifacts/runs/RUN_NAME --model MODEL`;
this restores its immutable source snapshot in an ignored directory.

Supporting/live analysis uses `python -m rep_sensitivity.aux_analysis RUN_DIRECTORY
RESULT_DIRECTORY`. Control estimates are exploratory, paired by base instance.
The current similarity-removal baseline is character SequenceMatcher at 0.90;
it is not an embedding-based test of semantic equivalence. Information availability
is scored separately so an appropriate INSUFFICIENT answer after lossy admission
is not described as a failure to recover unavailable truth.
Distinct-scope branch placement and exact-copy branch placement are separate
controls. The former records branch-load changes explicitly.

The sequential controller is `scripts/run_study.py`, launched from an immutable
snapshot with `scripts/launch_snapshot.py --entry study`. It qualifies the second
family, runs development checks for controls/live workers, completes validation,
and freezes the remaining protocols under `configs/frozen/` using
`configs/allocation-rule-v1.json`. A failed gate or engine exception stops execution
and leaves a record under `artifacts/runs/study-execution/`. The current snapshot
identifier and launch process are recorded separately; do not run a second GPU
controller concurrently. These controls do not assert that later stages have run.

Fixed live arms bound the complete trajectory token allowance, including the root.
If all reports cannot be admitted within that allowance, the result is explicitly
labeled resource displacement. No report is silently discarded. End-to-end accuracy
is distinguished from a root choice supported by its delivered assertions.
Use `scripts/export_mutations.py RUN_DIRECTORY` to export typed mutation records
that distinguish dependent verification checks from predicates whose truth changes.

The live-worker development check exposed an underspecified objective instruction.
Its failed `live-development-v7` results are preserved. The successor controller
`scripts/run_corrected_live_study.py` retains replay snapshot
`77e005c5428fb32bb54df2166d0d2341076ca56422f1b5fad7e3a84957ec3122` exactly, and uses
a separately archived live implementation with explicit predicate definitions.
It finishes both corrected development checks before any held-out call, then
prospectively supersedes the unused live-v7 plan with `live-v8`. Poor live baseline
competence limits live interpretation; it does not change the qualified replay.
The active successor snapshot/process is recorded in `records/execution/`.
`scripts/resume_archived.py` also restores supporting and live runs from their
own archived code and configuration.

The local mirror can run for a bounded duration with
`MIRROR_ITERATIONS=4320 FINALIZE_COMMIT=1 bash scripts/mirror_loop.sh`.
After all main/supporting/live analyses complete, the completion hook verifies
local raw-output inventories, regenerates tables, compiles and checks the PDF,
and commits compact generated records on `main`. It does not push or submit.
Existing staged changes block automatic committing. A completed package still
requires the scientific review listed in `SCIENTIFIC_REVIEW.md`.
