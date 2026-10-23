# Infrastructure amendment 001 — completed archive protection

Recorded 2026-10-23 after the Qwen base evaluation and during the Phi base
evaluation. No confirmatory parameter-training stage had started. The original
pre-test freeze is preserved byte-for-byte in `configs/freeze_original.json`:
SHA256 `3a35d0015e5447de1ca5eb3d6e77ab3c6e12ba3ad54bfcaf07799ad55443e525`.

The first Qwen baseline completed 240 paired families, 480 conversations and
30,720 model requests. A local archive count briefly returned 30,688 records.
Read-only inspection verified that the pod's complete archive had all 30,720.
The next normal synchronization restored all records locally, with the correct
original-byte hash
`6238d5f614790bcd77cc82689d9e2f824358c9fe0211c4346fb58bb02d08bf53`.
Its archive hash is
`fa8402fef5538f4549737bbc791f9dd957935b66b167c2a7dad3c5a79cee2089`.
The authoritative GPU outputs and complete summary were unaffected.

Cause: periodic rsync pulls leave an earlier plain append-only trace locally.
After the complete compressed trace arrived, local compaction could recompress
that stale prefix over the newly received archive and replace its manifest.
Subsequent pulls repaired it, but the interval of incomplete local evidence was
unacceptable. No experimental condition or score caused this amendment. The
baseline paired-success value was available during the audit; this is explicitly
an amendment after test access, not a new claim of an untouched pre-test code freeze.

Changes are limited to infrastructure and its regression test:

- `storage.py` verifies existing archive and uncompressed-byte hashes, checks
  that a remaining plain trace is an exact prefix, and removes only that confirmed
  duplicate. It never overwrites a completed archive with a stale plain file.
  Conflicting or unverifiable files are preserved and raise an error. Completed
  conversational traces must also match the total turn count in their episode
  summaries before original files are removed.
- `campaign.py` adds an explicit hold check between GPU stages, allowing a current
  stage to finish before an infrastructure review. The already-running old
  controller is held before training using a reversible directory at the next
  configuration path, which causes configuration writing to stop before another
  GPU process starts. This directory is not a run record or fabricated result.
- Regression tests simulate the stale-prefix mirror and verify both full
  record preservation and refusal to discard conflicting or missing records.
  All 20 tests pass.

The current Phi baseline is allowed to finish. Afterwards, stop the old controller,
pull and verify both complete archives, remove the documented hold directory and
marker, and restart the controller with the amended integrity code. Preserve
both baseline runs and their exact original source snapshots; do not rerun or
replace them. Maintain the original resource ledger, including all elapsed time.

The updated freeze records this amendment and exact changed-file hashes. The
queue, hypotheses, model revisions, datasets, seeds, endpoints, character behavior,
training quotas, checkpoint rule, exclusions and analysis remain unchanged.
