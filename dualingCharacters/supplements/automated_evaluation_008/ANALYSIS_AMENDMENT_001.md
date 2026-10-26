# Analysis completeness correction — before research labels were inspected

The original scientific freeze and `semantic_analysis.py` remain byte-identical. A code review found that its run loader would count only saved judgments in the planned denominator if a run stopped early. That would omit unrecorded planned opportunities and overstate coverage. No research label summaries had been inspected when this defect was identified.

`semantic_analysis_v2.py` retains the frozen selection, metrics, bootstrap, and all actual raw responses. It adds explicitly `not_recorded` derived rows for planned identities with no response, including all declared probe identities. These are missing observations, not fabricated model outputs or negative labels. Raw files remain untouched. Duplicate or unexpected identities fail validation. Planned denominators remain 692 base tasks/model, 108 probes/model, and the preselected 32 compatibility tasks/model when their inputs exist. Held-out controls remain outside research denominators.

No prompts, models, sample sizes, calibration keys, stopping rules, or inference allocation change. This is a correction to missingness accounting, not a response to comparative outcomes. The amendment manifest binds the corrected analysis separately; earlier code and results remain reproducible.
