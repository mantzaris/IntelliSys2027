# Dialogue interpretation 005 — historical package

**Portable reader update, evidence_validation_006:** use the [committed evidence index](../evidence_validation_006/EVIDENCE_INDEX.md), [chronological exchanges](../evidence_validation_006/DIALOGUE_EXCHANGES.md), and [portable CASEBOOK_V2.pdf](../evidence_validation_006/CASEBOOK_V2.pdf). That package commits the selected evidence and regenerates all48 episodes offline from a fresh clone. The original [CASEBOOK.pdf](CASEBOOK.pdf) remains unchanged as a historical artifact; its absolute workstation context links are superseded.

The original full atlas, accessible transcript, expanded AI readings and25MiB raw archive were local ignored artifacts, so their old relative links were unavailable in a fresh clone. They are not public downloads. The006 reader extracts committed selected records and writes its replacement views under006/extracted/author. See its index for exact commands, author/reviewer separation, selected-versus-whole-archive verification limits, and numerical reproduction.

This nonfrozen documentation correction does not change the005 scientific protocol, selection, source records, AI interpretations, PDF or rating forms. Prior/new README hashes are recorded in [PRESENTATION_CHANGES.json](../evidence_validation_006/PRESENTATION_CHANGES.json). The historical PACKAGE_MANIFEST records the earlier README hash; this explicit change record explains that difference.

## Original scope and preserved records

The48 episodes comprise36 anchors plus12 opposite-world episodes,11 unique families, and matched C3/C5/A1 round-zero collections with the same untrained Qwen model. The smaller mechanism pilot, refreshed collections and antagonist-free evaluations remain separate populations. Components are frozen shared model contexts with recorded history, motives and optional biographies, not independently trained personalities or hidden reasoning streams.

[PROTOCOL.md](PROTOCOL.md), [EVIDENCE_CUTOFF.json](EVIDENCE_CUTOFF.json), [SELECTION.json](SELECTION.json), [MATCHED_CASES.md](MATCHED_CASES.md), [MANUSCRIPT_SECTION.md](MANUSCRIPT_SECTION.md), and [CLAIM_TO_EVIDENCE.csv](CLAIM_TO_EVIDENCE.csv) retain the original scope, interpretations and chronology. Human ratings remain pending. The old [blank full-episode forms](human_forms/rater_1.csv) remain unchanged and are not automatically additional work for the new fixed-event review.

## Numerical reproduction

From dualingCharacters, with existing project dependencies:

```bash
PYTHONPATH=src:. python -m supplements.dialogue_interpretation_005.reproduce --numbers-only
```

The committed family table reproduces72 original contrasts without raw traces. Full historical regeneration scripts require the original raw bundle specified in [EVIDENCE_BUNDLE_MANIFEST.json](EVIDENCE_BUNDLE_MANIFEST.json); those scripts write005 outputs and should not be used to overwrite historical products during this validation stage. Use the006 reader workflow for the portable selected evidence.

The compatible/incompatible proposal in [NEXT_EXPERIMENT.md](NEXT_EXPERIMENT.md) remains historically unchanged. Its separately frozen executable continuation is in006, disabled and unscheduled pending required core/review work and owner/budget gates. No new worker or waiter was launched.
