# Dialogue interpretation 005

Start with [the offline atlas](DIALOGUE_ATLAS.html), [six-case printable casebook](CASEBOOK.pdf), or [all 16 completed comparative readings](MATCHED_CASES.md). The [paper-sized author-review draft](MANUSCRIPT_SECTION.md) develops four findings; [claim-to-evidence rows](CLAIM_TO_EVIDENCE.csv) separate measurements, provisional interpretations and missing controls.

The atlas contains48 complete episodes, including 36 anchor episodes and 12 linked opposite-world episodes. These represent11 unique families, not48 independent subjects. C3, C5 and motive-only A1 are matched within seed/family/world. All selected dialogues are round-zero collections against the same untrained Qwen model. The smaller mechanism pilot, refreshed collections with different defenders and antagonist-free trained evaluations remain separate evidence populations. Their earlier outcomes are context, not additional qualitative subjects.

The question concerns pursuit, expression and responsiveness. Components are frozen shared model contexts conditioned on observations, bounded recorded history, motives and optional biographies. They are not independently trained personalities or hidden reasoning streams. [PROTOCOL.md](PROTOCOL.md) was frozen before new comparative readings. The dated census and source hashes are in [EVIDENCE_CUTOFF.json](EVIDENCE_CUTOFF.json); selection and old-item links are in [SELECTION.json](SELECTION.json). Later campaign progress never expands this analysis population.

## Reproduce locally

From `dualingCharacters/`, using the established virtual environment and pinned project dependencies:

```bash
PYTHONPATH=src:. .venv/bin/python -m supplements.dialogue_interpretation_005.reproduce
```

This verifies the frozen selection and raw hashes, reuses a source-hash-validated extraction cache, reproduces72 original numerical contrasts, binds manually authored AI readings to exact records, regenerates HTML/Markdown/review materials and performs integration checks. It never makes a model call, starts a controller or resamples the population. Selection, inventory and freeze scripts are provenance tools; do not rerun them to replace the frozen files.

A fresh clone can run meaningful unit tests and reproduce all principal point estimates and intervals **without raw traces**:

```bash
PYTHONPATH=src:. .venv/bin/python -m pytest supplements/dialogue_interpretation_005/test_unit.py supplements/dialogue_interpretation_005/test_verification.py -q
PYTHONPATH=src:. .venv/bin/python -m supplements.dialogue_interpretation_005.reproduce --numbers-only
```

The committed `tables/FAMILY_NUMERATORS.csv` contains1,350 condition/seed/family rows with both worlds retained inside each family. The original behavior004 bootstrap implementation is reused. The complete-input integration check is separate:

```bash
PYTHONPATH=src:. .venv/bin/python -m supplements.dialogue_interpretation_005.verification
```

Missing artifacts produce `reports/PREREQUISITES.json`; they are not replaced by test fixtures or reported as a failed scientific calculation. Unit fixtures are explicitly invented and never enter research outputs. The existing behavior004 regressions test temporal truth, actual inbox clearing, missing follow-up, source authorship, actor boundaries and rating preservation.

## Evidence bundle and Git policy

The full atlas, accessible transcript, expanded AI evidence payload and raw traces are generated local artifacts. They are intentionally outside Git to avoid adding repeated bulk text. The compact case readings, numerical inputs, code, manifests, forms and PDF are committed. [EVIDENCE_BUNDLE_MANIFEST.json](EVIDENCE_BUNDLE_MANIFEST.json) specifies every required payload, byte count and SHA256. The local archive is:

`artifacts/dialogue_interpretation_005/EVIDENCE_BUNDLE.tar.gz`

It contains the 36 raw files for nine bound runs, their source snapshots/status records, selected original records, rendered full atlas, reviewer payload and separate author mapping. It contains no model weights or access credentials. Rebuild with:

```bash
PYTHONPATH=src:. .venv/bin/python -m supplements.dialogue_interpretation_005.bundle
```

For another clone, copy the archive through an authorized channel, verify its SHA256, and extract to a **new empty staging directory** with the same relative layout. Verify each member against the manifest. Copy only missing evidence files into `dualingCharacters/`; do not overwrite any existing artifacts or rating forms. No upload or public release has occurred.

Raw locators are a relative filename, SHA256, **one-based decompressed JSONL record** and field path. Some user quotes resolve through decoded JSON in `prompt[1].content`; those locators include the decoded path. `selected_records.jsonl.gz` preserves the selected original records, not invented reconstructions. The source index retains original author and turn indices. Generated claims exceeding240 characters are distinguished from their applied/delivered prefix.

## Reader and reviewer views

The HTML has no external resources or network calls. Paired-world buttons retain both complete worlds; all transcripts are present without network loading. Expand source/history/memory details as needed. On narrow screens conditions stack. Author excerpts link to exact turns and raw locators. [DIALOGUE_ATLAS.md](DIALOGUE_ATLAS.md) contains the full accessible transcript; [MATCHED_CASES.md](MATCHED_CASES.md) provides the shorter accounts. Structured answers and direct edits are displayed as recorded actions/plans, never invented speech.

Only `artifacts/dialogue_interpretation_005/human_review/reviewer/` is intended for raters. The complete author archive contains condition keys and AI readings and **is not the blinded review packet**. The first batch comprises36 full episodes with new IDs linked to the old24 windows. Two blank form templates are also committed under `human_forms/`; actual future forms must be versioned separately. Old ratings never transfer to expanded stimuli. See [HUMAN_REVIEW_STATUS.md](HUMAN_REVIEW_STATUS.md).

Optional visual verification and PDF printing use only the installed local Chrome and system websocket-client:

```bash
/usr/bin/python3 supplements/dialogue_interpretation_005/visual_check.py
```

This opens a temporary browser profile with page HTTP(S) resources blocked, inspects desktop/mobile/paired-world navigation and the reviewer view, writes temporary PNG previews, prints `CASEBOOK.pdf`, and closes its own browser. It does not touch the campaign. PDF binary metadata is time-dependent; scientific text and source records are deterministic.

The compatible/incompatible extension is concretely specified in [NEXT_EXPERIMENT.md](NEXT_EXPERIMENT.md), but disabled in [EXECUTION_GATE.json](EXECUTION_GATE.json). There is no new GPU job or waiter. Existing review001 mechanism and delivery diagnostics take priority under the original ownership and 96-hour ceiling.
