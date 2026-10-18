# Completed-evidence manuscript for scientific review

18 October 2026 UTC. The requested writing and local analysis pass is complete.
The article describes a complete, explicitly scoped empirical study. The larger
original experiment queue has not all completed, and human scientific review
has not yet occurred.

## Review artifacts

- [main.tex](manuscript/main.tex): the entire paper in one ASCII TeX source,
  including tables, appendices, macros, disclosure, and inline bibliography.
  There are no input/include or BibTeX dependencies.
- [main.pdf](manuscript/main.pdf): **17 main-text pages, 22 total pages, six figures,
  20 verified and cited references, and a 194-word abstract**.
- All referenced figures are beside the source. The retained official class
  matches the freshly retrieved conference archive. No template dimensions,
  body font size, or spacing were reduced.
- The final prose section is the sole accurate AI-assistance declaration.
  Source and PDF metadata are anonymous.
- [Reference verification](REFERENCE_VERIFICATION.md) and its
  [machine-readable record](records/reference-verification-v7.json) preserve full
  author order, publication status, primary URLs, inspected material, and claim support.
  The inline bibliography follows the template's alphabetical order and six-author rule.
- [Structural checks](records/manuscript-checks.json) and
  [visual review](records/manuscript-visual-review-v7.json) identify the checked artifact.

## Completed evidence used

| Study | Independent bases | Decisions | Accepted model calls | Role |
|---|---:|---:|---:|---|
| Qwen3 pilot | 24, including 12 scheduling | 1,152 | 2,304 | Development |
| Original validation, two models | 36 shared, including 18 scheduling | 5,184 | 10,368 | Exploratory validation |
| Main held-out, two models | 192 shared, 96 scheduling and 96 workflow | 27,648 | 55,296 | Primary scheduling and secondary workflow |
| Qwen3 mechanism held-out | 48 fresh, 24 per task | 576 | 1,152 | Separate prospective extension |
| Root diagnostic | Six reused development bases | 192 | 192 fresh root calls | Exploratory fixed-summary replay |
| Fresh-verification diagnostic | Six reused development bases | 30 | 72 | Small supplementary probe |

The numerical pipeline audit reuses 60 pilot/validation bases and covers 3,168
hierarchical trajectories and 6,336 summaries. Those units are not independent
problems. The mechanism study shares manager calls across access arms, explaining
its physical-call total. No stage is pooled with another to inflate sample size.

On main scheduling, averaging both organizations and all three policies, Qwen3
accuracy is 88.72% without repetition and 88.54% with exact copies, a change of
-0.17 percentage points [95% base-cluster interval -2.21, +1.74]. Phi-4 changes
from 80.03% to 78.95%, or -1.09 points [-3.17, +1.00]. Qwen3 has 93 corrections
and 97 regressions; Phi-4 has 143 and 168. This does not establish equivalence.
The direct hierarchy interactions also remain uncertain.

The new exploratory stochastic comparison uses generation 0 versus 1 within
each condition. Exact repetition changes answer disagreement by -0.17 points
[-1.74, +1.39] for Qwen3 and +2.52 [+0.61, +4.51] for Phi-4. This comparison
is distinct from cross-condition same-index transitions. Each cell has only two
generations, and all inference resamples complete base clusters.

The root diagnostic gives 8/12 correct world answers with ordinary frozen
summaries and 12/12 with lossless delivery. Uniform objective repetition also
gives 12/12 under frozen summaries, but two contexts still lack a uniquely
justified answer. Repetition is not information repair. The separate mechanism
study's workflow uniform-repetition decrease is secondary and does not isolate
exception handling or context length.

## Local reproduction and analysis correction

The main decisions and summary aggregates, complete root diagnostic, and mechanism
study reproduce from locally mirrored raw outputs. The audit is in
[manuscript-reproduction-v7.json](records/manuscript-reproduction-v7.json).
The original results remain unchanged. A reproducibility defect in the H3 bootstrap
iterated an unordered set of base IDs. Sorting those IDs fixes process-dependent
Monte Carlo interval endpoints. No observations, scores, estimator, strata, seeds,
or model inputs change. See [the analysis-only amendment](records/amendments/main-bootstrap-order-v2.json).
The paper uses `results/main-reproducible-v2/analysis.json` for these stable endpoints.

From the project directory, with the local raw archive present:

```bash
PYTHONPATH=src MPLCONFIGDIR=/tmp/rep-sensitivity-mpl .venv/bin/python -m rep_sensitivity.analysis artifacts/runs/main-v7 results/main-reproducible-v2
PYTHONPATH=src .venv/bin/python scripts/analyze_main_transitions.py
PYTHONPATH=src .venv/bin/python scripts/analyze_manuscript_main.py
PYTHONPATH=src MPLCONFIGDIR=/tmp/rep-sensitivity-mpl .venv/bin/python scripts/build_manuscript.py
(cd manuscript && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex)
.venv/bin/python scripts/check_manuscript.py
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

The current suite passes **105 integrity tests**, including known transition
fixtures, operational failures, whole-base pairing, and deterministic interaction
ordering. Completed raw outputs are not committed to Git. Their manifests and
curated aggregates are retained, and the raw archive remains local as well as in
the existing checkpoint infrastructure.

| Manuscript content | Generated source |
|---|---|
| Worked example | Two independent checkers; `records/manuscript-content-v7.json` |
| Main primary contrasts and hierarchy interactions | `results/main-reproducible-v2/analysis.json` |
| Absolute cells, policy comparisons, paired-world performance, resource table | `results/manuscript-main-v7/analysis.json` |
| Corrections, regressions, wrong-to-wrong changes, stochastic comparison | `results/main-transitions-v1/analysis.json` |
| Matched pilot/validation comparison | `results/pilot-interpretation-v2/analysis.json`, `results/validation-repetition-v1/analysis.json` |
| Numerical transformations and decision sufficiency | `results/numerical-pipeline-v1/analysis.json`, `visible-support-v3.json` |
| Fixed-summary and lossless replay | `results/root-diagnostic-v1/analysis.json`, `visible-support-v3.json` |
| Fresh mechanism test | `results/mechanism-heldout-v1/analysis.json` |
| Fresh worker probe | `results/fresh-probe-v1/analysis.json` |

Source and generated-block hashes are in
[manuscript-content-v7.json](records/manuscript-content-v7.json). Automatic refresh
updates only marked blocks, never assembles extra TeX sources, and refuses
incomplete evidence. Unfinished optional suites cannot introduce placeholders into
this version. Legacy completion hooks continue to call this updater.

## Evidence outside this article and author review

The separate balanced-objective confirmation, objective-only preservation replay,
and adjacent feedback/authority explorations are not completed evidence in this
paper. The broader supporting/live package is not complete for both models.
Their frozen records and partial outputs are preserved. Last reported remote
access failed with `container not found`; this writing task made no recovery
attempt and does not certify that the queue is running. Existing completion and
mirroring infrastructure was not interrupted.

This revision used **zero new GPU calls and zero additional GPU execution time**.
It does not reset the user's cumulative eight-hour allowance or certify unknown
remote consumption. Historical execution and budget journals remain authoritative.

The author should review the following before submission:

1. The restricted claim of a controlled aggregation benchmark, relative to existing
   work on restatements, summaries, provenance, and hierarchical communication.
2. The report-level sufficiency abstraction. Invalid or disputed fields remain
   flagged even when uncontested information uniquely determines the decision.
3. Pointwise intervals across related contrasts, the workflow competence decline,
   and the exploratory status of the new stochastic-variation analysis.
4. The narrow mechanism evidence. Lossless delivery changes information and
   presentation; an objective-only repair effect and causal mediation remain untested.
5. The actual human scientific contribution and assistance disclosure against the
   current [conference policy](CONFERENCE.md). The draft does not certify
   submission eligibility or completed human review.
