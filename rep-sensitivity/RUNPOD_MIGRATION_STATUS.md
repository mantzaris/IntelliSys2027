# Replacement RunPod, 17 October 2026

The current pod is the user's replacement **NVIDIA RTX 6000 Ada Generation**,
with 49,140 MiB of VRAM and driver 570.124.06. Its direct endpoint is
`195.26.233.98:19604`, discovered through the supplied RunPod SSH proxy. The
project is restored at `/workspace/rep-sensitivity`. The working RSA key was
reused without copying it to the pod or repository.

The user first supplied a 24 GB RTX 4090. After its bounded compatibility test,
the user explicitly chose a GPU with at least 48 GB to continue the frozen runs
and supplied the current Ada. The 4090 is no longer the active project endpoint.

## Preserved work

The locally saved source, frozen implementations, raw calls, and checkpoints
were restored. All 2,332 checked pilot files, 10,444 validation files, and 23,010
partial main-run files match their local counterparts byte for byte. See
`records/execution/rtx4090-restored-mirror-v1.json`.

The preserved Qwen3 main checkpoint contains 158 complete base pairs, 11,376
trajectories, and 22,848 accepted calls. Its last accepted call is dated
04:08:04 UTC. There are 32 additional start records without a corresponding
accepted output. No partial held-out decisions were inspected. No missing result
is represented as completed. Outputs after the last successful original-pod
mirror at 04:08:59 UTC are unavailable.

The completed pilot, both validation runs, and existing analyses remain intact.
The unfinished main evaluations, frozen diagnostics, confirmation, and numerical
preservation replay remain pending. Their source, prompts, manifests, and
sampling settings have not been changed by this migration.

## Earlier RTX 4090 compatibility check

The pinned Qwen3 and Phi-4 BF16 weight files occupy approximately 27.51 and
27.31 GiB respectively. Each exceeds the 4090's VRAM before accounting for
the attention cache and temporary tensors. Reducing the batch size alone cannot
make these unquantized weights fit entirely on this GPU.

The original inference versions were installed in an isolated environment.
Qwen3's eight downloaded shards pass their recorded authoritative checksums.
The model revision is `40c069824f4251a91eefaf281ebe4c544efd3e18`. The installed
PyTorch runtime reports `2.8.0+cu128`, vLLM is `0.10.2`, transformers is `4.55.4`,
and NumPy is `2.1.2`.

The fixed compatibility probe in `configs/rtx4090-probe-v1.json` tests CPU
offloading of 12 GiB, preserving the BF16 weights. Its 32 prompts are selected
by request hash from the completed development pilot without using correctness.
The output cap is deliberately reduced to 64 tokens for this hardware test.
These outputs are not scientific observations and are never accepted into any
study run. The probe has an eight-minute wall allowance, including loading and
shutdown, charged to the existing cumulative 7,200-second journal.

vLLM documents that offloading transfers weights between CPU and GPU on each
forward pass. This makes memory compatibility different from practical
throughput. See the [versioned vLLM documentation](https://docs.vllm.ai/en/v0.10.2/api/vllm/entrypoints/llm.html).
The model loaded, but the probe did not return a complete batch before the
worker stopped after **450.03 seconds**. No research calls were accepted. There
is no measured completed-batch throughput or new accuracy result. The GPU was
confirmed idle at 16:30:45 UTC. The ledger conservatively adds 50 seconds for the
interval between worker termination and that observation. Its cumulative charge
is **500.03 seconds**, leaving **6,699.97 seconds** of the existing allowance.
Timing and stop records are under `records/execution/rtx4090-probe-v1/`.

## Recovery and interpretation

`scripts/sync.sh` and `scripts/check_mirror.py` now default to the Ada's direct SSH
endpoint and retain environment overrides. The existing mirror loop continues
to protect completed artifacts locally. Host-key checking remains enabled.

Both pinned model snapshots pass their recorded shard checksums on the Ada.
The runtime uses BF16 weights, zero CPU offload, and the original sampling,
batching, context, output, tokenizer, and prompt settings. The opt-in runtime
adapter adds a hardware-segment identifier to newly accepted response records
and writes environment metadata under `records/environment/replacement-ada-v1/`.
It leaves archived scientific source files and decoding settings unchanged,
preserves the existing cache keys, and never overwrites the old environment
records. Existing calls are reused. The 32 interrupted starts are explicitly
recorded as ambiguous before resumption.

`scripts/resume_replacement_pod.py` invokes the existing immutable runners in
their original order. Qwen3's main/supporting/live stage is followed by the
frozen root diagnostic, mechanism extension and original Phi-4 stage. The
confirmation, numerical-preservation, and adjacent studies retain their existing
dependencies and cumulative budget checks. Optional studies can be skipped by
their frozen allocation rules. No new treatment or outcome-based selection was
introduced.

At 16:47:36 UTC, **96 newly accepted calls** had been mirrored locally. Their
allocated batch time totaled 158.31 seconds. Their decoding settings match the
original environment record exactly, and each new response carries the replacement
hardware identifier. This is an operational check, not an interim accuracy
analysis. There were still 158 complete base pairs at that checkpoint. Cached
completion messages emitted during recovery are not counted as new pairs.

The replacement uses the same GPU architecture but a different physical GPU and
driver. Bitwise identity across devices is not asserted. New response records
identify this execution segment for subsequent analysis. The finished
single-source manuscript is unchanged and retains pending-result statements.

The original migration record is `records/execution/rtx4090-migration-v1.json`.
The Ada runtime manifest is `records/execution/replacement-ada-v1.json`, and its
detached controller PID is in `records/execution/replacement-ada-handoff-v1.json`.
These operational counts are independent of scientific outcomes. All **91
integrity tests** pass, including checks that the adapter preserves sampling
inputs, response text, source identity, and historical environment records.

## Reproducing the runtime setup

On a restored project with the pinned virtualenv, the following reconstructs
the runtime archive from tracked source and installs its opt-in startup hook.
The hashes must match the prospective runtime manifest.

```bash
.venv/bin/python - <<'PY'
import hashlib, json, site
from pathlib import Path
root = Path.cwd()
config = json.loads(Path('records/execution/replacement-ada-v1.json').read_text())
archive = root / config['runtime_adapter_archive']
archive.mkdir(parents=True, exist_ok=True)
for name, key in [('gpu_environment_segment.py', 'runtime_adapter_sha256'),
                  ('resume_replacement_pod.py', 'controller_sha256')]:
    data = Path('scripts', name).read_bytes()
    assert hashlib.sha256(data).hexdigest() == config[key]
    target = archive / name
    assert not target.exists() or target.read_bytes() == data
    target.write_bytes(data)
site_dir = next(Path(p) for p in site.getsitepackages()
                if p.startswith(str(root / '.venv')))
hook = archive / 'gpu_environment_segment.py'
(site_dir / 'rep_execution_segment.pth').write_text(
    'import os,runpy; os.environ.get("REP_EXECUTION_SEGMENT") and runpy.run_path('
    + repr(str(hook)) + ', run_name="rep_gpu_environment_segment")\n')
PY
```

The existing controller is already detached and running. Do not launch a second
copy. If recovery is needed after an interruption, inspect its stage markers and
failure records first. Its entry point is recorded in
`records/execution/replacement-ada-handoff-v1.json`, with
`REP_EXECUTION_SEGMENT` set to the absolute runtime-manifest path and `PYTHONPATH`
set to the first stage's archived snapshot. Ledger locks prevent concurrent
writers, and accepted calls are recovered from their original hashes.
