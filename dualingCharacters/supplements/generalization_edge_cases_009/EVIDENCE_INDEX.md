# Evidence access

- **Start with:** [RESULTS.md](RESULTS.md), followed by [OVERVIEW.md](OVERVIEW.md) and [MANUSCRIPT_ADDENDUM.md](MANUSCRIPT_ADDENDUM.md).
- **Exact selected dialogues:** [DIALOGUES.html](DIALOGUES.html), accessible [Markdown](DIALOGUES.md), and the compressed complete chronological companion `evidence/FULL_DIALOGUES.html.gz` (1.3 MB). Run `gzip -dc evidence/FULL_DIALOGUES.html.gz > FULL_DIALOGUES.html` from this directory before following full-context links. The uncompressed 39 MB view is deliberately not duplicated in Git.
- **All new raw records:** `evidence/edge009_records.tar.gz`, directly committed. [Reproduction instructions](REPRODUCE.md) extract it offline. `evidence/MANIFEST.json` gives each file's hash and archive checksum. The archive contains all completed and partial new run records; profiles stay separate from research denominators.
- **Design:** [PROTOCOL.md](PROTOCOL.md), [DATASET_CARD.md](DATASET_CARD.md), `ALLOCATION.json`, `SCIENTIFIC_FREEZE.json`, `inputs/scenarios.json`, `tables/expectations.csv`.
- **Numerical inputs and results:** `tables/episodes.csv`, `tables/families.csv`, `tables/summary.csv`, `tables/contrasts.json`, `tables/behavior_contrasts.json`, `tables/by_pattern.csv`, `tables/opportunity_strata.csv`.
- **Optional replay, only if executed:** `REPLAY_BINDING.json`, `REPLAY_FREEZE.json`, `inputs/replay.json`, `tables/REPLAY_SUMMARY.json`. Its selected states and outcomes never enter the main grid.
- **Original evidence:** stage 008 remains unchanged, including unfavorable training comparisons and failed semantic screens. No human rating requirement has been reintroduced; no ratings or model-judge labels are added here.

A file/line locator such as `edge009-qwen-17-v1/C5_characters.jsonl#L123` refers to `runs/` inside the archive. It is paired with the whole file's SHA256. User scripts and time-indexed analyst expectations are separately serialized in `inputs/scenarios.json`; only public script/catalog fields are passed to models. Numerical and quote reproducibility does not establish broad scientific validity.
