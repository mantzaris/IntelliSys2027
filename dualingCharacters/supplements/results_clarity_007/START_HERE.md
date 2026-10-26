# What changes when persistent motives and biographies are introduced?

Start with the [eight-page reader edition](READER_EDITION.pdf), its [offline expandable HTML](READER_EDITION.html), and the [two-page findings brief](FINDINGS_BRIEF.pdf). The question concerns this implemented system's pursuit, expressed claims, communication and effect on the user's plan. It does not require or demonstrate a benefit.

Three supported points:

1. **Action channels differ.** Across the common-base round-zero population, C3/C5/A1 emitted 5,408/477/938 direct edits, 828/4,618/1,397 recollections and 969/1,930/4,830 proposals, each out of 10,800 allocated opportunities. Each condition covers 150 unique paired families repeated across generator seeds 17/29/43 (900 episodes); actions are not independent experimental subjects.
2. **Typed preferences persist in both C5 and motive-only A1.** Repeated eligible within-actor direct-goal pairs were 3,623/5,400, 4,831/5,224 and 5,093/5,364 for C3/C5/A1. This is a typed slot/value measure, not semantic coherence, robustness or strategic sophistication.
3. **API, prose, payload and response can diverge.** The six selected matched case groups illustrate recommendations labeled recollect, unsupported correction, generic criticism, and continued advocacy after a visible objection. These are illustrations, not semantic prevalence estimates. Earlier authorization assertions and later “should” recommendations must be read separately.

[Architecture](ARCHITECTURE.md) explains the shared frozen backbone, separate contexts, two interfering actors plus one answerer, fixed retrieval, history and actual transport. [Figure 1](figures/01_action_channels.svg), [Figure 2](figures/02_four_layers.svg), and [Figure 3](figures/03_persistence_and_state.svg) retain mechanical labels and denominators. Exact per-seed counts and original pointwise intervals are in [tables](tables/MECHANICAL_COUNTS.csv) and [contrasts](tables/CONTRASTS.json).

The negative task context remains: C5 paired successes 168/180/172 versus C3 177/181/190, each out of 240 test families at training seeds 17/29/43. Clean training yields 186/138/183. Dialogue differences do not establish learned superiority or broader exploration. See [manuscript revision](MANUSCRIPT_REVISION.md) and [claim-to-evidence table](CLAIM_TO_EVIDENCE.csv).

## Corrected annotation package

[ANNOTATION_V2.md](ANNOTATION_V2.md) is the entry point. Event006-v2 preserves all 72 IDs and windows. Unassessed is missing; explicitly assessed-none is a negative label-set assessment. Each dimension has its own status and agreement denominator. Incoming statement labels never contain secondary recipient-response labels. The eight answerer-directed items display actual answerer JSON; the other 64 are component-directed. See [amendments](AMENDMENTS.md) for the demonstrated v1 defects and presentation correction.

[Two blank forms](review/rater_1_event006_v2.csv), [second form](review/rater_2_event006_v2.csv), [rubric](review/RUBRIC.md), [guide](review/ANNOTATOR_GUIDE.md) and [schema](review/SCHEMA.json) are committed. Build the blinded packet with the command below. Do **not** include the [author-only 72-event worksheet](AUTHOR_EVENT_ANALYSIS.csv), reader interpretations, or condition key when giving materials to raters. These readings are AI-assisted and unvalidated. Historical forms remain untouched; no labels have been inferred or transferred.

## Reproduce offline from a fresh clone

Use Python 3.12 with the repository's existing pinned environment (`.venv`), NumPy, Matplotlib and pytest. PDF rendering additionally uses system Python with ReportLab 3.5.34 and DejaVu Sans fonts at `/usr/share/fonts/truetype/dejavu/`; PDF checking uses PyPDF2, Poppler and a local Chrome browser for visual inspection. No model, GPU, network, original workstation cache or remote artifact directory is required. Verify actual dependency versions in reports/ENVIRONMENT.json and reports/OUTPUT_ENVIRONMENT.json. The source hashes bind committed inputs; no new bulk evidence copy is needed.

From `dualingCharacters/`:

```bash
# Reuse the committed 006 selected-evidence archive; restore full atlas links.
PYTHONPATH=src:. .venv/bin/python -m supplements.evidence_validation_006.reader
# Build 007 numeric tables, exact reader views, figures and author worksheet.
MPLCONFIGDIR=/tmp/clarity007-mpl PYTHONPATH=src:. .venv/bin/python -m supplements.results_clarity_007.build
/usr/bin/python3 supplements/results_clarity_007/pdf_build.py
# New reviewer directory only; refuses to overwrite a rater's work.
PYTHONPATH=src:. .venv/bin/python -m supplements.results_clarity_007.review_package --output /tmp/event006-v2-review
# Verify quotes, fixed selections, routes, forms and source bindings.
PYTHONPATH=src:. .venv/bin/python -m supplements.results_clarity_007.verify
PYTHONPATH=src:. .venv/bin/python -m pytest supplements/results_clarity_007/tests -q
```

The v2 reviewer directory is portable: open REVIEW.html without a server. Its unchanged `items.json`, episode context and fixed windows come from the committed 006 reviewer archive; it excludes author keys and AI interpretations. Use a fresh output directory rather than replacing completed forms. The full author atlas and unchanged 62-page casebook remain [006 appendices](../evidence_validation_006/EVIDENCE_INDEX.md). Original raw-file hashes accompany selected records; checking this package does **not** verify unprovided bytes of whole raw archives.

If using a different environment, replace `.venv/bin/python` with the compatible interpreter. Fresh-clone unit tests use explicitly synthetic software fixtures, never research ratings. Archive-dependent verification reports missing prerequisites instead of inventing data. PDF bytes are deterministic under the recorded ReportLab/font environment; the fixed metadata date is a reproducibility setting, not the session date.

## What remains pending

Two real independent raters must assess the fixed events, preserve originals and calibration decisions, and resolve disagreements only in a separate adjudication file. Dimension coverage and agreement must be reported before semantic comparisons. The next immediate validation is that assessment—not more selected anecdotes. Causal communication claims still require the existing delivery intervention; compatibility and delivery controls answer different questions. See [controlled-evidence status](CONTROLLED_EVIDENCE_STATUS.md). No new scientific model calls or human ratings were added; the existing GPU campaign continues independently under its original ownership and 96-hour ceiling.
