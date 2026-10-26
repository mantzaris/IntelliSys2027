# Automated evaluation evidence

Start with **FINAL_RESULTS.md** and **JUDGE_CALIBRATION.md**. The complete author-review paper is [paper/manuscript.pdf](paper/manuscript.pdf); editable source is [paper/manuscript.tex](paper/manuscript.tex). The identified project copy is `paper/author_review.pdf`. Neither has been submitted.

## Evidence types

- **Deterministic:** mechanical API/state/route facts, current authorized ledgers, compact main-test outcomes, and controlled structured decisions.
- **Automated semantic:** model labels, exact supporting spans, extraction uncertainty, calibration, disagreements, and probes. These have `source_type=automated_model`; they are not human labels or a truth oracle.
- **Controlled:** all 64 compatible/incompatible conversations, including unsuccessful plans and deviations from assigned preferences. This manipulation is not a delivery/no-delivery intervention.

The old 72 event identities and historical human forms are preserved. Current automated assessment does not require recruitment. No human agreement values are supplied.

## Directly readable and machine-readable

- `DIALOGUE_APPENDIX.md`, `CONTROLLED_DIALOGUE.md`: exact illustrative text, chronology, routes, structured answers, and source locators. Retrospective examples are not prevalence samples.
- `tables/CORE_COUNTS.csv`, `CORE_CONTRASTS.json`, `CORE_TRANSITIONS.csv`, `CORE_PENDING.csv`: all eligible completed main evaluations at the fixed cutoff and all pending queue cells.
- `tables/MECHANICAL_COUNTS.csv`, `MECHANICAL_CONTRASTS.json`: prior common-base behavior reproduced from frozen family-level inputs.
- `tables/MODEL_ANNOTATIONS.jsonl.gz`, `SEMANTIC_RATES.json`, `SEMANTIC_CONTRASTS.json`, `JUDGE_AGREEMENT.json`, `STABILITY.json`: independently produced model labels and missingness-aware analyses. See calibration failures before interpreting them.
- `tables/COMPATIBILITY_PRIMARY_RESPONSE.csv`, `COMPATIBILITY_TYPED_TRANSITIONS.csv`, `COMPATIBILITY_RESULTS.json`: primary opportunity-level response accounting and family-level secondary outcomes.
- `tables/JUDGMENT_QUALITY.json`, `REPAIR_INTEGRITY.json`, `EXTRACTED_AUTHORIZATION.json`: invalid spans, format repairs, and conditional ledger checks. A ledger mismatch depends on the extraction being correct.
- `tables/RESOURCE_RUNS.csv`, `RESOURCES.json`: loading, failed attempts, retries, generation, and sampled utilization, separately from the ongoing core.
- `SCIENTIFIC_FREEZE.json`, `ALLOCATION.json`, `RUN_BINDINGS_COMPLETE.json` (with historical bindings retained): prospective input/code/model/sample bindings. Initial profiles, the single prompt revision, and later analysis/operational corrections remain separately versioned.

## Portable inputs

`evidence/RAW_AND_INPUTS.tar.gz` is committed alongside its SHA256/member manifest. It contains exact new judge outputs and controlled traces, selected reconstructed common-base episodes, frozen judge inputs, and compact core outcomes. Extract from `dualingCharacters/`:

```bash
PYTHONPATH=src:. python -m supplements.automated_evaluation_008.bundle --extract
```

Extraction validates every member, rejects unsafe paths, and refuses to overwrite a differing existing file. No workstation, GPU, private artifact directory, or network is needed for the documented CPU reproduction. The historical selected-record archive in evidence006 is also already committed and read directly by existing helpers.

The package verifies its selected reconstructed records and exact new raw outputs. It does **not** independently rehash every original common-base raw archive or include model weights and trained adapters. Original full-archive/checkpoint hashes remain provenance. Rechecking those full source archives or rerunning inference requires the established mirror and pinned model cache; this limitation is explicit.

See `REPRODUCE.md` for numerical reproduction, fresh-checkout tests, PDF compilation, and separation of lightweight tests from artifact integration. Model-launch modules require existing owner authorization, locks, budget checks, and pinned inputs; ordinary reproduction never invokes them.
