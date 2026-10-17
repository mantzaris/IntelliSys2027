# Rep-sensitivity

Controlled experiments on duplicated, near-duplicated and complementary reports
in hierarchical LLM systems. Everything for this study lives in this directory.
Work and commits stay on `main`. The latest continuation request authorizes pushing
completed changes; background completion automation still only commits locally.

**Allowance amendment, 17 October 2026 UTC:** the user increased the cumulative
additional-experiment allowance from two to **eight hours (28,800 seconds)**.
The prior 500.03 seconds remain charged, leaving **28,299.97 seconds** at the
amendment. The existing queue is running on the RTX 6000 Ada. Samples, prompts,
inference settings, stage order and individual diagnostic limits are unchanged.
See [EXPERIMENT_ALLOWANCE_STATUS.md](EXPERIMENT_ALLOWANCE_STATUS.md) for the
effective controller changes and recovery commands. Older two-hour references
below describe the original authorization, now superseded prospectively.

**Manuscript consolidation, 17 October 2026 UTC:** the complete research draft is
in [manuscript/main.tex](manuscript/main.tex) and [manuscript/main.pdf](manuscript/main.pdf).
The paper has one TeX source, an inline bibliography, and all five figures beside
the source. It contains 14 main-text pages and 19 pages in total, with 21 verified,
cited references and a 209-word abstract. See [MANUSCRIPT_STATUS.md](MANUSCRIPT_STATUS.md)
for the evidence boundary, numerical traceability, and scientific review points.
[REFERENCE_VERIFICATION.md](REFERENCE_VERIFICATION.md) records primary-source checks.

**Replacement GPU, 17 October 2026 UTC:** the current user-provided pod is verified
as an RTX 6000 Ada Generation with 48 GB VRAM. Source and checkpoints are restored, and all checked
pilot, validation, and partial main files match the local copies. The preserved
main checkpoint has 158 completed Qwen3 base pairs and 11,376 trajectories.
See [RUNPOD_MIGRATION_STATUS.md](RUNPOD_MIGRATION_STATUS.md).

An earlier 24 GB RTX 4090 loaded the model with CPU offloading but did not finish
the bounded compatibility probe. The user then supplied this 48 GB Ada to retain
the frozen BF16 settings. The original serial queue is restored with explicit
hardware provenance and unchanged scientific snapshots. No quantized replacement,
altered research prompt, or new treatment has been introduced. At restoration,
the original allowance had 6,699.97 seconds remaining after the probe and a
conservative cleanup margin. The later eight-hour amendment above preserves
these charges. The original pod's last available
mirror was **04:08:59 UTC**. Later output from that pod is unavailable.
The queue descriptions below are dated history. Current controller identity and
recovery details are in `records/execution/replacement-ada-handoff-v1.json`.

To refresh completed result blocks, compile, and check the single-source paper:

```bash
PYTHONPATH=src MPLCONFIGDIR=/tmp/rep-sensitivity-mpl .venv/bin/python scripts/build_manuscript.py
(cd manuscript && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex)
.venv/bin/python scripts/check_manuscript.py
```

Only delimited result blocks are replaced. Authored prose and the inline
bibliography are preserved. Legacy report commands call the same updater. The
mirror's local finalizer refreshes and compiles after each completed stage, while
keeping the separate full-study completion gate. Incomplete analyses never supply
paper estimates. New results still require scientific and visual review.

**Earlier adjacent exploration, 17 October 2026 UTC:** the focused primary-literature
check adds three verified publications on self-correction, identity labels and
authority roles. [PROTOCOL_ADJACENT_V5.md](PROTOCOL_ADJACENT_V5.md) freezes two
small studies sharing four reused development bases: 72 feedback/update calls
and 32 explicit-origin relay/role calls. These are **pending GPU execution**, not
new empirical findings. Their final-priority controller waits for the original
evaluations, frozen confirmation and numerical-preservation replay.

Measured validation batches project 9.9–12.7 minutes including loading for both,
with a hard 15-minute/104-call ceiling inside the **same cumulative two-hour cap**.
A frozen budget-only fallback retains the complete 72-call feedback study or
skips both. No sample, model or round is added after observing responses.
The exact frozen source/config/model hashes and recovery command are in
`records/freezes/adjacent-explorations-v1.json` and
`records/execution/adjacent-explorations-handoff-v1.json`.

**83 integrity tests pass.** The 17-page anonymous PDF includes a clearly pending
exploratory appendix; its changed page and reference layout have been inspected.
The automatic completion hook analyzes each complete exploration and keeps
mirroring until its final queue entry resolves. See
[ADJACENT_EXPLORATIONS_STATUS.md](ADJACENT_EXPLORATIONS_STATUS.md).

```bash
PYTHONPATH=src .venv/bin/python scripts/analyze_adjacent_explorations.py
PYTHONPATH=src MPLCONFIGDIR=/tmp/rep-sensitivity-mpl .venv/bin/python scripts/build_adjacent_supplement.py
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -p test_adjacent_explorations.py -v
```

Do not start another GPU runner: the archived waiting controller already owns
this queue entry. Source preparation is CPU-only; `--freeze` refuses conflicting
immutable artifacts. Later feedback prompt bytes depend on earlier public outputs;
their construction and dependencies are frozen, and actual prompts are logged.

**Numerical continuation, 2026-10-17 UTC:** [NUMERICAL_PIPELINE_AUDIT.md](NUMERICAL_PIPELINE_AUDIT.md)
traces 6,336 manager summaries from 3,168 hierarchical pilot/validation trajectories
(60 independent bases). Boolean objectives originate in raw model output; no
input, parser, transport or primary-choice scoring discrepancy was found. No new
GPU rerun is required. Policy/model/task-specific frequencies and paired estimates
are in `results/numerical-pipeline-v1/`; representative raw traces include intact
controls. The new objective-only repair replay has six fixed development pairs and
48 fresh root calls, projected at 5.0–6.2 minutes including loading. It runs last,
after protected Phi-4 and confirmation, against the **same cumulative two-hour
allowance**. See [PROTOCOL_NUMERICAL_PRESERVATION_V4.md](PROTOCOL_NUMERICAL_PRESERVATION_V4.md).
Its implementation is complete; its GPU result is pending.
**77 integrity tests pass**, including decision support with irrelevant invalid
objectives and unresolved conflicts.
The latest count/timing snapshot is `records/execution/numerical-continuation-runtime-v4.json`.
The 15-page review PDF has been rebuilt and its changed pages/figures inspected.
`records/execution/numerical-preservation-handoff-v1.json` pins the last-priority
controller and recovery command; the implementation-only amendment preserves
valid integral floats without changing any of the 48 frozen prompts.

```bash
PYTHONPATH=src .venv/bin/python scripts/audit_numerical_pipeline.py
PYTHONPATH=src .venv/bin/python scripts/audit_visible_support_v3.py
PYTHONPATH=src MPLCONFIGDIR=/tmp/rep-sensitivity-mpl .venv/bin/python scripts/build_numerical_report.py
PYTHONPATH=src .venv/bin/python scripts/analyze_numerical_preservation.py
PYTHONPATH=src .venv/bin/python scripts/capture_numerical_execution.py
```

The analyzer emits GPU results only when all planned cases and raw calls exist.
Do not launch a second model server: the archived waiting controller already owns
the queue entry and shares the original cumulative budget journal.

The v3 analysis-only supplement distinguishes invalid fields from decision-relevant
uncertainty: two fixed diagnostic contexts still identify the sole feasible
candidate despite Boolean objectives. It preserves v2 classifications and primary
world scores. No experiment inputs, sample sizes or GPU calls are changed.

**Earlier validation report, 2026-10-16 19:57 UTC:** offline analysis of both completed
original validation runs is available in
[VALIDATION_REPETITION_RESULTS.md](VALIDATION_REPETITION_RESULTS.md). On 18
scheduling pairs with the pilot-matched ordinary/checklist policies (144 decisions
per arm/model), exact repetition changes Qwen3 accuracy from 79.86% to 76.39%
(−3.47 points, 95% cluster interval −10.42 to +2.78), and Phi-4 from 72.22% to
73.61% (+1.39, −4.17 to +6.25). The large pilot mean benefit does not reproduce in
this validation aggregate. These are exploratory validation estimates, not new
GPU executions or completed held-out confirmation.

The 24-pair, 1,152-trajectory pilot and all its original results remain preserved.
The influential pair's repeated report favors C64 (objective 9), while C39 (8) is
correct; all eight baseline summaries replaced objectives with Boolean `true`.
Its complete trace audit is in `results/pilot-interpretation-v2/influential-pair-audit.json`.

At the earlier report, original Qwen3 main had 72/192 completed pairs (5,184/13,824 trajectories);
no partial main choices were inspected. Original Phi-4 remains protected in the
sequential queue. The unchanged 192-call root diagnostic now runs at the first
safe natural boundary after Qwen3 main/support/live, before the previously frozen
514-trajectory development, 30-trajectory fresh-verification, fresh validation and
eligible conditional confirmation. The active runner has no supported mid-run
handoff; no running inference was interrupted or restarted.

A separate **24 fresh scheduling-pair, 480-trajectory, two-model objective
confirmation** follows original Phi-4. It compares selective and balanced exact
and verified-paraphrase repetition; measured batch projections are 77–95 minutes,
including loading allowances, within a hard shared two-hour new-GPU budget.
No new dose exploration is added. See [PROTOCOL_CONTINUATION_V3.md](PROTOCOL_CONTINUATION_V3.md),
`records/freezes/objective-confirmation-v1.json`, and
`records/execution/continuation-venv-correction-v3.json` for the current controller
PIDs, environment and exact recovery commands. The earlier handoff records remain
as history. Completed stages are analyzed and mirrored automatically.

The prior revision passed 69 integrity tests. Validation figures and an anonymous
working manuscript are available. Root, mechanism and fresh-confirmation results
remain pending; human scientific review is required. Current runtime and counts
are in `records/execution/current-runtime.json`; source/config/model revisions are
recorded per immutable run and freeze.
See `PILOT_MECHANISM_AUDIT.md`, `PROTOCOL_AMENDMENT_V1.md`, the preserved
`DECISIONS.md`, `PROTOCOL.md`, the machine-readable manifests
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
- `artifacts/implementations/`: locally mirrored immutable execution snapshots,
  including controller code and its configuration inputs.
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

The project is `/workspace/rep-sensitivity` on the replacement RTX 6000 Ada pod.
The GPU architecture matches the original runs, but the driver and physical
device are recorded as a new execution segment. Consult the migration status
before attempting to start another controller.
`scripts/sync.sh` defaults to the user-provided direct SSH endpoint and the working
RSA key. Override `RUNPOD_HOST`, `RUNPOD_PORT`, `RUNPOD_KEY`, `RUNPOD_PROJECT`, and
`RUNPOD_KNOWN_HOSTS` as needed. Host-key checking remains enabled. Never add private
keys to the repository. The old unrelated `runpod-thermo` SSH alias is not used.

```bash
bash scripts/sync.sh push-source
bash scripts/sync.sh pull
# Optional bounded hourly mirror, copies once per minute:
bash scripts/mirror_loop.sh
# Read mirrored progress without examining held-out model choices:
.venv/bin/python scripts/status.py
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
.venv/bin/python scripts/resume_archived.py artifacts/runs/main-v7 --model qwen3
```

The original main run is initialized and frozen in
`configs/frozen/main-v7.json`. For any new confirmation, freeze sample
size, model allocation, templates, policies and analysis before held-out inference;
never edit a frozen artifact in place. Do not start these commands concurrently
with the active controller.

## Supporting controls and live workers

Original supporting and live configurations are now frozen; execution follows
main replay under the sequential controller. Their commands are:

```bash
.venv/bin/python scripts/resume_archived.py artifacts/runs/supporting-v7 --model qwen3
.venv/bin/python scripts/resume_archived.py artifacts/runs/live-v8 --model qwen3
```

Live workers receive minimal role-specific data with actual access recorded.
These resume commands require the corresponding initialized run directory. Use
`--model phi4` for the second family and run families sequentially.
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
hash and source-score hash. Manuscript tables use completed analysis records only.
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
The draft's abstract length, bibliography citations, single-source organization,
anonymity, and LaTeX overflow checks are automated. All pages of the consolidated
draft have also been visually inspected. Author scientific review remains necessary. See
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

If the controller stops, inspect its failure record and resolve the cause before
resuming; do not start a second process alongside active inference. After Phi-4
validation completes, the exact successor can be recovered on the pod with:

```bash
study_snapshot=artifacts/implementations/69fa1831720a79bbca0735f5b5d4272b08929185e90d2241504e3e772c1fce65
replay_snapshot=artifacts/implementations/77e005c5428fb32bb54df2166d0d2341076ca56422f1b5fad7e3a84957ec3122
PYTHONPATH="$study_snapshot" .venv/bin/python "$study_snapshot/runner.py" \
  --templates "$study_snapshot/configuration" --replay-snapshot "$replay_snapshot"
```

This controller reuses accepted calls. A recorded model or competence failure
requires investigation; the recovery command does not waive any gate.

The local mirror can run for a bounded duration with
`MIRROR_ITERATIONS=4320 FINALIZE_COMMIT=1 bash scripts/mirror_loop.sh`.
After all main/supporting/live analyses complete, the completion hook verifies
local raw-output inventories, regenerates tables, compiles and checks the PDF,
and commits compact generated records on `main`. It does not push or submit.
Existing staged changes block automatic committing. A completed package still
requires the scientific review listed in `SCIENTIFIC_REVIEW.md`.
## Mechanism amendment (16 October 2026)

The current scientific direction and execution constraints are in
[PROTOCOL_AMENDMENT_V1.md](PROTOCOL_AMENDMENT_V1.md). The completed exploratory
[pilot mechanism audit](PILOT_MECHANISM_AUDIT.md) distinguishes objective/summary
loss from root integration errors. The original frozen study and its hypotheses
remain preserved. New GPU results must not be inferred from implementation or
CPU preflight records.

Inspect locally mirrored counts without reading held-out choices:

```bash
.venv/bin/python scripts/status.py
cat records/mechanism-report-status.json
cat records/execution/mechanism-handoff-v1.json
```

Reproduce the pilot and its dated mechanism analysis from the mirrored raw outputs:

```bash
PYTHONPATH=src .venv/bin/python -m rep_sensitivity.analysis artifacts/runs/pilot-v7 artifacts/analyses/pilot-reproduction-20261016 --bootstrap 10000
PYTHONPATH=src .venv/bin/python scripts/audit_pilot_mechanisms.py
PYTHONPATH=src MPLCONFIGDIR=/tmp/rep-sensitivity-mpl .venv/bin/python scripts/build_mechanism_report.py
```

On the existing pod, CPU-only preflight uses the cached model tokenizer; it does
not load an inference engine. The freeze requires the matching passing-test and
preflight records. Do not overwrite an existing freeze after changing code.
The commands below record the initial freeze procedure. The current working
analyzer has the dated dose-subset correction in
`records/amendments/mechanism-analysis-correction1.json`; inference still uses
the archived source snapshot. Resume that snapshot rather than refreezing the
current tree. Its sole package difference is preserved as a reversible `.patch`
beside the correction record. The local completion hook applies the corrected
analysis without modifying any accepted call or original protocol.

```bash
PYTHONPATH=src .venv/bin/python scripts/preflight_mechanisms.py --config configs/mechanism-development-v1.json
PYTHONPATH=src .venv/bin/python scripts/preflight_fresh_probe.py --config configs/fresh-probe-v1.json
PYTHONPATH=src .venv/bin/python scripts/freeze_mechanisms.py
```

The already queued controller is identified by
`records/execution/mechanism-handoff-v1.json`. It waits for the original Qwen3
main/support/live stage, runs targeted development and the fresh diagnostic, then
validation and the eligible bounded held-out extension. It then resumes original
Phi-4 using the unchanged archived implementation. Do not launch a second
controller while that process is alive. The STOP_AFTER_CURRENT_STAGE marker stops
only the old controller's *next* stage after the current stage completes; its
expected stop record is preserved and explained by the handoff record.

If that controller has exited, resume with the exact `resume_command` in the
handoff record on the pod. Each run also stores its immutable implementation,
configuration, request hashes and score checkpoints. Accepted malformed responses
are reused, not resampled. No push, submission, additional infrastructure or paid
API is part of the controller. Local mirroring continues independently.

After each new suite completes, deterministic offline analysis is:

```bash
PYTHONPATH=src .venv/bin/python -m rep_sensitivity.targeted_analysis artifacts/runs/mechanism-development-v1 results/mechanism-development-v1
PYTHONPATH=src .venv/bin/python -m rep_sensitivity.fresh_analysis artifacts/runs/fresh-probe-v1 results/fresh-probe-v1
PYTHONPATH=src .venv/bin/python -m rep_sensitivity.targeted_analysis artifacts/runs/mechanism-validation-v1 results/mechanism-validation-v1
# Only if the prospective allocation gate launched and completed this suite:
PYTHONPATH=src .venv/bin/python -m rep_sensitivity.targeted_analysis artifacts/runs/mechanism-heldout-v1 results/mechanism-heldout-v1
PYTHONPATH=src MPLCONFIGDIR=/tmp/rep-sensitivity-mpl .venv/bin/python scripts/build_mechanism_report.py
```

Compact analyses, native-token matching audits, protocol freezes and vector
figures belong in Git. Raw calls, detailed trace packets, run manifests with full
inputs, model files and logs remain in ignored `artifacts/` and `logs/`, mirrored
locally. Physical call inventories count shared computations once; trajectory
resource summaries describe logical decision graphs. Small-subset intervals are
withheld when a bootstrap stratum has only one base.

The automatic local finalizer now waits for the amendment's completed analyses or
an explicit allocation-gate decision, as well as original main/support/live. It
does not declare human review or submission readiness. The working manuscript can
be rebuilt before that point, with pending stages explicitly marked:

```bash
PYTHONPATH=src MPLCONFIGDIR=/tmp/rep-sensitivity-mpl .venv/bin/python scripts/build_manuscript_tables.py
PYTHONPATH=src MPLCONFIGDIR=/tmp/rep-sensitivity-mpl .venv/bin/python scripts/build_study_report.py
PYTHONPATH=src MPLCONFIGDIR=/tmp/rep-sensitivity-mpl .venv/bin/python scripts/build_mechanism_report.py
cd manuscript
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
cd ..
.venv/bin/python scripts/check_manuscript.py
```

## Fixed-input root diagnostic and continuation audit

[PROTOCOL_AMENDMENT_V2.md](PROTOCOL_AMENDMENT_V2.md) preserves the original and
v1 confirmation analyses. New pilot interpretation and the root-only diagnostic
are exploratory; original held-out choices were not inspected to choose them.
The latter is frozen in `configs/frozen/root-diagnostic-v1.json` and queued as
recorded in `records/execution/root-diagnostic-handoff-v1.json`. It waits behind
the existing controller and verifies completion of both original model stages.
Do not launch competing inference. No optional boundary investigation is selected
ahead of the core development results.

The diagnostic reports world-oracle accuracy separately from correctness given
the actually visible summaries. A consistent but erroneous summary may warrant
a different answer; missing decision-critical information warrants INSUFFICIENT.
The pre-inference supplement `scripts/audit_root_information.py` scores this
without repairing inputs using hidden truth and leaves the inference freeze intact.

```bash
# Offline reproduction and review figures:
PYTHONPATH=src .venv/bin/python scripts/interpret_pilot.py
PYTHONPATH=src MPLCONFIGDIR=/tmp/rep-sensitivity-mpl .venv/bin/python scripts/build_pilot_interpretation.py
# Progress, provenance and measured runtime, without evaluating held-out choices:
PYTHONPATH=src .venv/bin/python scripts/study_runtime.py
.venv/bin/python scripts/check_mirror.py
# CPU-only initial preflight/freezing procedure (already completed; do not refreeze):
PYTHONPATH=src .venv/bin/python scripts/preflight_root_diagnostic.py
PYTHONPATH=src .venv/bin/python scripts/freeze_root_diagnostic.py
```

If the queued diagnostic controller exits, inspect its log/blocked record before
resuming its immutable snapshot. The exact command and source snapshot are in the
handoff record. The local completion hook reanalyzes only complete mirrored
outputs and waits for the diagnostic before assembling a review package. Raw
outputs, request caches, model files and detailed trace rows stay outside Git.

## Latest continuation commands

```bash
PYTHONPATH=src .venv/bin/python scripts/analyze_validation_repetition.py
PYTHONPATH=src .venv/bin/python scripts/audit_influential_pair.py
PYTHONPATH=src MPLCONFIGDIR=/tmp/rep-sensitivity-mpl .venv/bin/python scripts/build_empirical_update.py
# Called by the mirror hook only after the standalone diagnostic is complete:
PYTHONPATH=src .venv/bin/python scripts/audit_root_information_v2.py
# Analyzes each complete model; incomplete models remain explicitly incomplete:
PYTHONPATH=src .venv/bin/python scripts/analyze_objective_confirmation.py
PYTHONPATH=src MPLCONFIGDIR=/tmp/rep-sensitivity-mpl .venv/bin/python scripts/build_completed_extensions.py
```

The confirmation recovery command in the execution record uses the absolute
`.venv/bin/python` entry path, not its resolved symlink to system Python. Never
start it alongside the active coordinator. Both controllers hold writer locks;
the new budget journal conservatively charges ambiguous attempts on restart.
