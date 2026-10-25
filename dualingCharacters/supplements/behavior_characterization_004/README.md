# Behavioral characterization 004

Start with [BEHAVIORAL_CHARACTERIZATION.md](BEHAVIORAL_CHARACTERIZATION.md), [SESSION_REPORT.md](SESSION_REPORT.md) and the [claim table](CLAIM_TO_EVIDENCE.md). This is a post-outcome descriptive audit, not a new confirmatory experiment or a claim of benefit.

From the repository's `dualingCharacters` directory, using the existing environment and complete local mirrors:

```bash
PYTHONPATH=src:. .venv/bin/python -m supplements.behavior_characterization_004.reproduce
PYTHONPATH=src:. .venv/bin/python -m supplements.behavior_characterization_004.verify_package
PYTHONPATH=src:. .venv/bin/python -m pytest -q tests supplements/review_001/test_review.py supplements/long_horizon_intent_002/test_intent.py supplements/exploration_003/test_exploration.py supplements/behavior_characterization_004/test_behavior.py supplements/behavior_characterization_004/test_compatibility.py
```

Reproduction verifies the fixed evidence list and raw hashes, regenerates scientific tables, the corrected exposure join, review materials, four figure sets and factual manuscript text, then checks counts and provenance. It uses CPU only and has no scheduler or model-execution path. Missing mirrors cause an error; it does not retrieve or substitute another run. Large derived caches and packet payloads stay in ignored `artifacts/behavior_characterization_004/`. Existing human annotations are never overwritten; changed forms trigger an explicit preservation/review check.

The original17-file scientific manifest remains unchanged. Three explicit amendments preserve it: compressed-action-file packet compatibility, exact legacy C1 format2 exposure linkage, and applicability/denominator clarification for the random control. Read [METRIC_APPLICABILITY.json](METRIC_APPLICABILITY.json) with generic tables. No primary C3/C5/A1 metric, evidence population, original core or prior supplement freeze was changed.

## Tables and provenance

- [CHANNELS.csv](reports/CHANNELS.csv), [ACTION_CHAIN.csv](reports/ACTION_CHAIN.csv): all allocated opportunities, structural validity, delivery, actual memory changes and following answers.
- [PERSISTENCE.csv](reports/PERSISTENCE.csv), [CONTEXT.csv](reports/CONTEXT.csv): actor-local runs and fixed event windows. C2 has no persistent assignment; C6's literal option does not represent every utility term.
- [EVIDENCE.csv](reports/EVIDENCE.csv), [PEER_RESPONSE.csv](reports/PEER_RESPONSE.csv): source authority/visibility and received-message follow-ups, with missingness retained.
- [Primary descriptive contrasts](reports/PRIMARY_DESCRIPTIVE_CONTRASTS.csv), [all fixed contrasts](reports/matched_contrasts.json), [per-seed metrics](reports/metric_summary.csv): paired-family estimates and explicitly limited seed uncertainty.
- [Costs](reports/costs.csv), [run reconciliation](reports/run_cost_reconciliation.csv), [exposure join v2](reports/supervision_join_v2.csv), [secondary defender results](reports/secondary_defender_results.csv): distinct budgets and noncausal context.
- [Figures and captions](reports/figures/CAPTIONS.md), [manuscript section](MANUSCRIPT_SECTION.md), [next unscheduled experiment](NEXT_EXPERIMENT.md).

`DATA_AUDIT.json` binds raw traces, configurations, revisions, defender identities, paired coverage and action order. `RESULTS_PROVENANCE.json`, the presentation/narrative manifests and the final package manifest trace derived outputs. Larger regenerable aggregate CSVs are retained locally but ignored by Git; the compact tables above are committed. Family-rate detail and action-level derived records are ignored artifacts, not independent experimental subjects.

The existing56-item exploration packet remains at `artifacts/exploration_003/human_review/reviewer_v2/`. The separate24-item addendum is at `artifacts/behavior_characterization_004/human_review/reviewer/`; open `PACKET.html` with `RUBRIC.md` and one blank rater form. Its private mapping is in a sibling `private/` directory and must not accompany reviewer delivery. Six [AI-assisted readings](AI_ASSISTED_READINGS.md) are illustrative, unvalidated and separate from both blank forms.

The already authorized core continues under its existing owner and96-hour controls. This package creates no background process, consumes no supplement allowance and leaves intent002 disabled. Operational monitoring/recovery commands and actual handoff status are in SESSION_REPORT.md.
