# Reproduce the completed stage

Run from `dualingCharacters/` with Python 3.11+ and the versions in `requirements-cpu.txt`. The existing project `.venv` satisfies these CPU dependencies. No GPU, network, paid service, or private mirror is needed for the packaged analyses. The following commands perform no inference.

```bash
export PYTHONPATH=src:.
export MPLCONFIGDIR=/tmp/automated008-matplotlib
python -m supplements.automated_evaluation_008.bundle --extract
python -m supplements.automated_evaluation_008.rebuild_inputs
python -m supplements.automated_evaluation_008.compact_core
python -m supplements.automated_evaluation_008.mechanical_reproduce
python -m supplements.automated_evaluation_008.controlled
python -m supplements.automated_evaluation_008.controlled_report
python -m supplements.automated_evaluation_008.controlled_interactions
python -m supplements.automated_evaluation_008.deterministic_events
python -m supplements.automated_evaluation_008.overlap
python -m supplements.automated_evaluation_008.semantic_analysis_complete
python -m supplements.automated_evaluation_008.judgment_quality
python -m supplements.automated_evaluation_008.repair_audit
python -m supplements.automated_evaluation_008.calibration_report
python -m supplements.automated_evaluation_008.resource_report
python -m supplements.automated_evaluation_008.dialogues
python -m supplements.automated_evaluation_008.controlled_dialogue
python -m supplements.automated_evaluation_008.figures
python -m supplements.automated_evaluation_008.paper_results
```

`compact_core` verifies the sufficient outcome tables against the original saved headline tables. `core_results` instead audits the full original mirror and adapters; it is an additional artifact-dependent check and is not required for fresh-clone numerical reproduction. Missing original weights are a prerequisite limitation, not a failed compact calculation.

Unit tests without extracted artifacts:

```bash
python -m pytest -q supplements/automated_evaluation_008/tests/test_semantics.py supplements/automated_evaluation_008/tests/test_integrity.py supplements/automated_evaluation_008/tests/test_operational_merge.py
```

Artifact-dependent design/selection integration after extraction:

```bash
python -m pytest -q supplements/automated_evaluation_008/tests/test_controlled.py
```

The synthetic fixtures are software tests and authored calibration controls, never research observations or fabricated human ratings. All research denominators exclude synthetic controls. Agreement retains dimension-level missingness.

Compile both paper copies with the already installed TeX Live/latexmk toolchain:

```bash
bash supplements/automated_evaluation_008/paper/build.sh
```

The optional `pdf_audit.py` link check uses system PyPDF2 (tested at 1.26.0) or pypdf. Poppler (`pdfinfo`, `pdftotext`, `pdftoppm`) supports page/annotation/visual checks. The archived official Springer proceedings class is bundled, unmodified. The current template endpoint denied automated downloading; see `reports/CONFERENCE_TEMPLATE.json`. Compilation is not a declaration of conference-policy compliance or scientific validation.

Historical freezes are checked read-only by `python -m supplements.automated_evaluation_008.protection`. The protocol, initial/final prompt freezes, amendment, allocation, raw outputs, and figure captions explain exactly which analyses are new, reproduced, or limited.

No launch is needed after this stage. Recovery of a failed inference requires checking the recorded status, ownership, locks, remaining reservation allowance, and partial records before any retry. Do not rerun completed judgments to change their labels. The original core resumes through its own native controller and unchanged queue; exact operational ownership and recovery paths are recorded in `SESSION_REPORT.md`.
