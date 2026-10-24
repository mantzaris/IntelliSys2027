# Post-review supplement 001

This directory contains exploratory audits designed after seeing C1 and the
available C3 seed-17 result. The original 58-file freeze remains unchanged.
Read [PROTOCOL.md](PROTOCOL.md), [REVIEW_RESPONSE.md](REVIEW_RESPONSE.md), and
[CLAIM_TO_EVIDENCE.md](CLAIM_TO_EVIDENCE.md).

From `dualingCharacters`:

```bash
PYTHONPATH=src .venv/bin/python -m unittest supplements.review_001.test_review -v
PYTHONPATH=src .venv/bin/python -m supplements.review_001.regenerate
PYTHONPATH=src .venv/bin/python -m supplements.review_001.freeze verify
```

The existing analysis environment needs the pinned additions in
`requirements-cpu.txt`. No model weights or GPU are used by these commands.
Exact cached tokenizer exports are in `artifacts/review_001/tokenizers`; their
hashes are recorded in the exposure provenance. Install/download is not part of
regeneration. The run registry identifies completed eligible inputs and excludes
invalid runs explicitly. Running traces are never analyzed.

`controller.py` is the **single replacement post-core coordinator**. It waits for
all original stages and the shared campaign lock, binds fixed checkpoint bytes,
prepares inputs, then profiles under the same remote GPU lock/resource ledger.
It freezes allocation using time only, executes A then B and any admitted optional
modules, resolves the earlier unseen-profile supplement, regenerates reports and
makes local main commits. Do not start a second coordinator. Inspect
`artifacts/review_001/controller_state.json` and `controller.log` for current state.
The usual existing `PCC_SSH_*`, `PCC_REMOTE_DIR`, and `PCC_KNOWN_HOSTS` environment
settings apply; no credentials are stored here.

Raw traces, input prompts, detailed exposure records, checkpoints and reviewer
packets remain Git ignored and locally mirrored. Compact results, manifests and
source are committed. `results/provenance_manifest.json` links the compact tables
to raw trace/checkpoint/config hashes through the individual audit manifests.
Zero-row tables mean pending or not executed when so marked in
`results/supplement_status.json`; they are not evidence of a null effect.

Human materials: `artifacts/review_001/human_review/pilot_actions` contains actual
historical C4/C5 exchanges. New B exchanges will have separate IDs under
`review001_actions` only after all B conditions finish. `items.json` hides condition
labels; `private_key.json` must not be given to blinded raters. Each directory has
a fixed rubric and two initially blank CSV forms. Existing forms and item IDs are
never overwritten. The original prose packet remains separate and unchanged.
