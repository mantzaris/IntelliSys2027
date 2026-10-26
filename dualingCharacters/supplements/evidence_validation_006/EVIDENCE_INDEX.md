# Portable evidence and validation index

Start with [chronological exchanges](DIALOGUE_EXCHANGES.md), their [offline HTML](DIALOGUE_EXCHANGES.html), or [CASEBOOK_V2.pdf](CASEBOOK_V2.pdf). These are directly committed. The six original paper cases are retained; the unsupported Saturday correction is a clearly labeled added contrast. The [original PDF](../dialogue_interpretation_005/CASEBOOK.pdf) is preserved as a historical artifact; its workstation-specific links are superseded, not silently repaired.

## Obtain and regenerate all selected evidence

The committed [author archive](evidence/author_selected_v1.tar.gz) is approximately 1.04 MiB. It contains all 48 selected episodes,1,344 exact original selected records,2,123 quote locators, unchanged AI-assisted readings, and model/configuration/run provenance. It contains no weights, credentials, remote access details, or unrelated full runs. The [manifest](evidence/AUTHOR_MANIFEST.json) records every member hash and byte count.

From `dualingCharacters/`, with Python 3.11+ and the project's existing dependencies:

```bash
PYTHONPATH=src:. python -m supplements.evidence_validation_006.reader
```

This single offline command checks the committed archive/member hashes, extracts without overwriting changed files, verifies every selected quote against its included original record, rechecks temporal truth, replays all 576 transport actions on CPU, reconstructs actual inbox visibility, and regenerates:

- `supplements/evidence_validation_006/extracted/author/DIALOGUE_ATLAS.html`: complete48-episode author atlas, all 16 previous matched readings, paired-world views and exact source records.
- `.../DIALOGUE_ATLAS.md`: complete accessible transcript and observations.
- `supplements/evidence_validation_006/DIALOGUE_EXCHANGES.{md,html}` and generated PDF input `tables/EXCHANGE_CONTEXTS.json`.

Use the installed `.venv/bin/python` in this workspace; a fresh reader may use an equivalent Python environment. No GPU, network connection, original artifact directory, or model cache is needed. Generated `extracted/` files are intentionally ignored because their compact inputs are committed. To inspect the archive without Python, `tar -xzf .../author_selected_v1.tar.gz -C NEW_EMPTY_DIRECTORY` is an ordinary offline extraction, but the reader command also performs the identity checks.

**Verification scope:** whole original raw-file hashes were verified on the originating mirror before export. The portable archive includes selected records, not the omitted portions of those files. A fresh clone can verify selected-package bytes and source-to-view identity; it cannot recompute the full omitted raw archives' hashes. Original locators remain relative file name, original SHA256, one-based decompressed JSONL record and field path. This limitation is not hidden by the derived episode cache.

## Independent reviewer package

Distribute only [reviewer_events_v1.tar.gz](evidence/reviewer_events_v1.tar.gz) and [its manifest](evidence/REVIEWER_MANIFEST.json) to raters. It is a separate approximately 1.04 MiB archive, without condition/seed keys, role metadata, author mapping, identifying raw filenames, or AI interpretations.

```bash
PYTHONPATH=src:. python -m supplements.evidence_validation_006.reader --reviewer-only
```

Open `extracted/reviewer/REVIEW.html`. It contains 72 fixed event items linked to36 full episode contexts in `EPISODES.html`, a rubric, disjoint authored calibration examples, two blank forms and provenance templates. Both raters assess the same opportunities, with any nonmessages or missing follow-ups retained by rule. In this selected sample all 72 are peer actions:64 component deliveries and 8 answerer notes, all observed. The old36-episode and earlier window packets/forms remain unchanged and are not additional required assignments. The full author repository/archive is **not blinded**; do not give it to raters as the blinded stimulus.

The [author selection key](EVENT_SELECTION.json) links new events, episodes and old window IDs. [Review protocol](review/PROTOCOL.md), [rubric](review/RUBRIC.md), and [readiness report](reports/REVIEW_READINESS.json) document missingness, agreement, workload and limitations. Human ratings are pending. Estimated5.2–8.2 hours per rater excludes calibration, breaks and deep context checks; this is a planning assumption, not measured completion time.

## Numerical reproduction and verification

The existing committed [family-level input table](../dialogue_interpretation_005/tables/FAMILY_NUMERATORS.csv) has 1,350 condition/seed/family rows. Both worlds remain within family. The original frozen bootstrap reproduces 72 comparisons:

```bash
PYTHONPATH=src:. python -m supplements.dialogue_interpretation_005.reproduce --numbers-only
PYTHONPATH=src:. python -m pytest supplements/evidence_validation_006/test_unit.py -q
PYTHONPATH=src:. python -m pytest supplements/evidence_validation_006/test_integration.py -q
```

Unit tests need no research artifacts. Integration checks require archive extraction; missing prerequisites are explicitly skipped/reported. The originating workstation additionally verifies all historical protected forms, which are not all part of this selected package. Passing quote, transport and packaging checks does not validate semantic readings, causal influence or efficacy.

To rebuild the new event packet and source-route examples from extracted selected evidence:

```bash
PYTHONPATH=src:. python -m supplements.evidence_validation_006.events
PYTHONPATH=src:. python -m supplements.evidence_validation_006.presentation
PYTHONPATH=src:. python -m supplements.evidence_validation_006.routes
PYTHONPATH=src:. python -m supplements.evidence_validation_006.review_package
```

Existing changed forms are protected against overwrite. Completed submissions belong in a new external directory, not the blank templates. See [rating ingestion](review/PROTOCOL.md).

PDF regeneration requires ReportLab and DejaVu Sans fonts, both already present on the originating system:

```bash
TZ=UTC /usr/bin/python3 supplements/evidence_validation_006/print_pdf.py
/usr/bin/python3 supplements/evidence_validation_006/pdf_audit.py
```

The PDF's links target internal evidence destinations. Companion filenames and stable episode IDs identify the complete HTML; no original-machine URL is required. Binary PDF timestamps can vary; quotations and source identities are fixed.

## Controlled evidence status

[Compatibility design](compatibility/README.md) and [operational execution prerequisites](EXECUTION_READINESS.md) are prepared, disabled and unscheduled. The CPU-only dry-run checks 64 conversations and 2,816 scheduled calls without inference. Required core and review001 work remain prior dependencies; this stage made no new model calls or GPU reservations. No actual independent human ratings have been received. No public release or upload was created; these files are committed locally only.
