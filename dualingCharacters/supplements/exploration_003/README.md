# Exploration 003

CPU-only, post-outcome analysis of a fixed local evidence snapshot. The current
assessment is **inconclusive for broader useful exploration**. See
[results](reports/RESULTS.md), [figures](reports/FIGURES.md),
[claim boundaries](CLAIM_TO_EVIDENCE.md), and [session handoff](SESSION_REPORT.md).
The original core experiment and its negative/mixed findings are preserved.

## Reproduce

From `IntelliSys2027/dualingCharacters`, with the existing local artifact mirror:

```bash
PYTHONPATH=src .venv/bin/python -m supplements.exploration_003.reproduce
```

This verifies all previous scientific freezes and the exploration manifest,
validates raw hashes before using derived caches, regenerates tables, preserves
review packet identities and annotations, and builds PDF/SVG/PNG figures. It makes
no model calls and performs no remote writes or scheduling. It will fail rather
than invent missing raw data. Do not rerun the inventory's `capture` operation:
the evidence population is already locked at the cutoff in
`EVIDENCE_SNAPSHOT.json`.

Focused and regression verification:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests supplements/review_001/test_review.py supplements/long_horizon_intent_002/test_intent.py supplements/exploration_003 -q
PYTHONPATH=src .venv/bin/python -m supplements.exploration_003.freeze verify
```

Dependencies were already installed; versions are in `requirements-cpu.txt`.
No installation or environment replacement is needed. Analysis uses local CPU
resources and streams original traces. Derived caches are in the ignored
`artifacts/exploration_003/` directory. The original raw runs and adapters stay in
their established artifact locations; `DATA_AUDIT.json` binds their hashes.

## Evidence and interpretation

`PROTOCOL.md`, `CODEBOOK.md`, and `SCIENTIFIC_MANIFEST.json` record the pre-summary
definitions and snapshot. Main collections are observational and separated by
seed/round; the primary comparison uses the final common-base mechanism pilot.
Older protocols are retained separately. Later campaign completions never enter
this population. Reporting and figure presentation were implemented after the
first summaries and are documented separately in `CHRONOLOGY.md`; they are not
retroactively represented as pre-summary files.

The reviewer-facing packet is
`artifacts/exploration_003/human_review/reviewer_v2/`. Its 56 item IDs and trajectory
content are identical to v1; only the rubric presentation removes study labels.
The separate private key is
`artifacts/exploration_003/human_review/private/mapping.json`. Do not give that key
or the AI-assisted illustrative reading to blinded raters. Both rating forms are
blank. No human labels, model-judge scores or validated semantic breadth are
available. The pre-existing action/prose/intent packets remain untouched.

`LITERATURE_AND_NOVELTY.md` links inspected primary methods and verified versions.
`NEXT_EXPERIMENT.md` proposes the smallest missing comparison and a later research-
diagnosis application. Neither is scheduled or implemented as a GPU worker.

Compact tables, manifests, code and figures are versioned. Bulk traces, review
payloads and caches are deliberately outside Git. No result is a claim of learned
defender exploration, rivalry, coalition formation, a learned equilibrium or broad
task transfer.
