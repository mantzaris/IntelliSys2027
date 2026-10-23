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
