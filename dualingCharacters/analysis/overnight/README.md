# Overnight continuation reporting

This is an unfrozen descriptive/operational layer. It does not schedule GPU work
or change either scientific freeze. Session timestamps and ownership are under
`reports/overnight_20261024T023622Z/SESSION.json`.

From `dualingCharacters`, in the existing local analysis environment:

```bash
PYTHONPATH=src .venv/bin/python -m analysis.overnight.monitor
PYTHONPATH=src .venv/bin/python -m analysis.overnight.update
PYTHONPATH=src .venv/bin/python -m analysis.overnight.mirror
PYTHONPATH=src .venv/bin/python -m analysis.overnight.human
PYTHONPATH=src .venv/bin/python -m analysis.overnight.readiness
PYTHONPATH=src .venv/bin/python -m analysis.overnight.handoff
PYTHONPATH=src .venv/bin/python -m unittest analysis.overnight.test_analysis -v
```

The monitor and mirror check use the existing SSH identity and host; environment
variables can supply the established connection settings. They are read-only.
Use `monitor --local-only` without network access. Monitoring snapshots and caches
are Git ignored; compact current state, forecasts, results and figure provenance
are saved in the timestamped report directory.

`update` audits only newly completed inputs. It imports the frozen sampler,
loss-mask reconstruction and score functions. It caches raw-derived final metrics
and validated artifact fingerprints, and reuses the six prior exact exposure
reconstructions. `update --force` regenerates aggregate reports/figures from the
validated caches; it still does not unnecessarily rescan unchanged raw artifacts.
For a new checkout, copy the established ignored raw-artifact mirror first.
No artifacts means no reproducible measured result; missing data are not fabricated.

All final paired contrasts retain authorized/hypothetical worlds within a family.
One-seed intervals use the existing exploratory family bootstrap, not seed-population
inference. The unchanged `pcc.study_analysis` runs when new evaluations arrive;
its two-way estimator and fixed Holm comparison family are retained. Explicitly
complete three-seed comparisons are also exported separately.

Compile the author-review PDF using the existing conference template:

```bash
PYTHONPATH=src .venv/bin/python -m analysis.overnight.draft
TEXINPUTS="$PWD/artifacts/public_assets:" BSTINPUTS="$PWD/artifacts/public_assets:" \
  latexmk -cd -pdf -interaction=nonstopmode -halt-on-error paper/overnight_author_review.tex
```

No new citations are added to the existing verified bibliography. PDF/build logs,
raw prompts, adapters and human sheets are kept out of Git. Figures are saved as
PDF/SVG with PNG previews and exact source hashes. Read their generated captions
before interpreting uncertainty or pending cells.

`associations`, `training_curves`, `compute`, and `qualitative` regenerate their descriptive
tables/figures/illustrations from validated aggregates and completed logs. The
incremental updater calls them when their inputs change. `handoff --final` records
the actual end of this supervision session; it does not stop a healthy campaign.
The readiness check never binds checkpoints or bypasses the original coordinator.
