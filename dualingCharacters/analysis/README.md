# Descriptive reporting extension

This extension was written on 2026-10-23 after the two baseline outcomes were
available and before the first trained-policy test outcome. It is explicitly
exploratory reporting, not part of the original pre-test analysis freeze.
It makes no model calls and changes no scientific input, checkpoint, sample,
endpoint, comparison, multiplicity rule or GPU job. All original analysis source
hashes continue to verify against the recorded freeze and infrastructure amendment.

The tables expose all predefined domain-by-structure cells, familiar versus
held-out domain framing, actual training exposure and per-run resources. They
provide counts and rates, without new p-values or selected subgroup claims.
The same scenario families repeat across training seeds; rows are not additional
independent subjects. Held-out domain framing retains the common categorical schema.

Packed-window counts include examples read into the stream buffer; they should
not be confused with complete uniquely supervised trajectories. Exact target
tokens and input tokens are reported separately. Resume processes identify their
original run, and failed-process costs remain visible. Activity samples are
approximate; conservative reservation time still governs the 96-hour ceiling.

Regenerate the frozen core analysis, these explicitly descriptive tables and the
paper with one command from the project directory:

```bash
bash analysis/regenerate_all.sh
```

The new outputs have the prefix `reports/tables/exploratory_`. Their input-file and
analysis-source hashes are saved in `exploratory_descriptive_trace.json`. The GPU
controller continues to produce the original core package automatically; this
wrapper adds the separate descriptive layer for author review.

The wrapper first runs `audit_artifacts.py`, a read-only check of completed local
source snapshots, recorded checkpoint hashes, compressed/original trace hashes
and conversational row counts against episode summaries. The compact audit is
saved as `reports/tables/artifact_integrity.json`. Active and failed runs are
excluded from final-file checks and listed explicitly. Early pilots without
per-run source snapshots retain that qualification; passing integrity checks
does not make an invalid pilot scientifically valid. Run the audit after the
controller has synchronized a completed stage, not during an incomplete pull.
Some early pilot checkpoint manifests contain an entry hashing a previous
version of the manifest itself. The audit records this historical metadata defect
and verifies the actual adapter/configuration files separately. Current atomic
checkpoint writing excludes the manifest from its own file list. No original
pilot metadata is rewritten to hide this limitation.

`retrieval_descriptives.py` reports selected-source volume, canonical authorizing
source coverage, current visibility of emitted references, and extra clarification
fields from actual structured-evaluation prompts. Each setting keeps its original
fixed sample; the 240-family main sample and 48-family extensions differ.
This descriptive extension was added
during the first trained-policy evaluation, after baseline outcomes were known.
It changes no frozen metric or test. Source volume is an observed cost; deciding
which retrievals were unnecessary requires a separate necessity analysis.
A reference absent from the current retrieved set may still have been observed
earlier, so current visibility is distinguished from citation validity.
Final-turn coverage is separated from the all-turn average. The same script
audits source availability in all 96 preselected fixed-recovery snapshots;
the memory fault leaves those sources unchanged. No case is filtered on its
availability or outcome, and absent canonical evidence is not treated as a
proof that recovery is impossible.

`publication_tables.py` projects the saved main, ablation, transfer and external
aggregates into manuscript tables; it adds no estimators or hypothesis tests.
Every number has an aggregate-file hash in `publication_tables_trace.json`.
`design_coverage.py` also checks whether paired worlds still require distinct
final behavioral decisions and whether ambiguity masks the controlled update.
This is a data-only audit, not a new performance endpoint. All scheduled test
families retain the intended authorized-versus-hypothetical distinction.

`PYTHONPATH=src .venv/bin/python analysis/progress.py` reads queue status and
resource counters without opening task-success outputs. It resolves documented
restart aliases and counts only completed scheduled stages; local mirroring may
lag by about one minute. The GPU/controller locks remain the authority for whether
another process may start.

`audit_lineage.py` verifies completed scheduled stages against the resolved queue:
loaded-parent adapter hashes, continuation into the next fit, the actual supervision
file, the fixed final optimizer step, and matching initial adapter weights within
each model/seed. It reads no task-success scores. Its scope and the separate audit
requirement for optimizer-checkpoint interruptions are recorded in
`reports/tables/adapter_lineage.json`.
