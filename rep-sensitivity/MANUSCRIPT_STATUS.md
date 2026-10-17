# Consolidated manuscript status

17 October 2026 UTC. The writing and presentation pass is complete. The scientific
study remains incomplete and the author has not yet conducted scientific review.

## Draft and organization

- [main.tex](manuscript/main.tex) contains the whole paper, appendices, disclosure,
  tables, and inline bibliography. It has no `\input`, `\include`, or BibTeX dependency.
- [main.pdf](manuscript/main.pdf) has **14 main-text pages, 19 total pages, five
  figures, 21 verified and cited references, and a 209-word abstract**.
- All five figures are beside `main.tex`. Official template dependencies are retained.
- The illustrative capacity example passes both independent scheduling checkers.
- [REFERENCE_VERIFICATION.md](REFERENCE_VERIFICATION.md) links the primary sources.
  Its machine-readable record preserves full author order, publication status,
  relevant inspected passages, and the specific supported claims.
- The sole AI-assistance disclosure is the final prose section before references.
  It describes implementation, experimental operation, analysis, retrieval, and
  drafting assistance, and does not claim completed human review.

The narrative centers on three distinct outcomes: faithful representation,
information sufficient to determine a decision, and correct final selection.
The influential pilot pair is included without becoming a general mechanism claim.
Unfinished supplementary explorations have no result-shaped placeholder tables.

## Completed evidence and pending results

The draft uses the complete 24-base, 1,152-trajectory pilot and the 36-base
validation set shared across two models, with 2,592 trajectories per model.
The main scheduling comparison uses 12 pilot bases and 18 validation bases.
The numerical audit covers 60 distinct bases, 3,168 hierarchical trajectories,
and 6,336 manager summaries. These are separate denominators, not independent
samples of the same size.

The pilot exact-copy accuracy gain is +13.54 percentage points, with a base-cluster
95% interval of [+4.17, +22.92]. Comparable validation estimates are -3.47
[-10.42, +2.78] for Qwen3 and +1.39 [-4.17, +6.25] for Phi-4. These are preserved
completed analyses, not new GPU experiments. They do not demonstrate equivalence
or a reliable numerical-preservation effect.

Both original validation runs, 128 development-control trajectories per model,
and 60 live-development trajectories per model are complete. The smaller controls
are not promoted to confirmation in this paper.

The last local main checkpoint contains **158/192 Qwen3 base clusters,
11,376/13,824 trajectories, and 22,848 accepted calls**. The last accepted call is
04:08:04 UTC and the last successful mirror is 04:08:59 UTC. Partial held-out
choices were not inspected for this writing pass and supply no paper estimates.
Phi-4 main completion, held-out controls/live evaluation, root diagnostics,
mechanism extensions, fresh confirmation, numerical preservation, and the
budget-conditional adjacent explorations remain unverified as completed.

Direct SSH now returns `Connection refused`; the existing RunPod proxy returns
`container not found`. The local mirror process continues retrying. The remote
controller and loaded model cannot be inspected, and no new execution or restart
was attempted. Existing source archives, manifests, queue dependencies, and local
results are preserved. Restored access to the existing pod is needed to advance
the queue. No infrastructure or billing setting was changed.

This pass uses **zero new GPU calls and zero additional GPU execution time**.
The shared additional-experiment cap remains 7,200 seconds. Its last recorded
charge is zero; current remote consumption cannot be certified after loss of
access. See [the execution snapshot](records/execution/manuscript-consolidation-v6.json).

## Numerical traceability

The compact source hashes and generated block hashes are in
[manuscript-content-v6.json](records/manuscript-content-v6.json). Earlier
manuscript traceability records were moved intact to `records/manuscript-sources/`.
Raw outputs and analysis files remain in their existing locations.

| Paper component | Completed source |
|---|---|
| Worked example, Table 1 | Both executable verifiers, result embedded in `records/manuscript-content-v6.json` |
| Stage counts, Table 2 | Pilot and validation manifests and completed analysis inventories |
| Accuracy, transitions, organization effects, Tables 3-4 and Figure 2 | `results/pilot-interpretation-v2/analysis.json`, `results/validation-repetition-v1/analysis.json` |
| Paired-world responsiveness and stability, Table 5 | `validation-repetition-v1/analysis.json`, `paired_world` and `consequential_minus_harmless` |
| Numerical transformation and fidelity, Table 6 and Figure 3 | `results/numerical-pipeline-v1/analysis.json`, `groups`, `comparisons`, and pipeline checks |
| Decision sufficiency, Table 7 | `results/numerical-pipeline-v1/visible-support-v3.json`, `groups` |
| Observable failure labels, Table 8 | `validation-repetition-v1/analysis.json`, `failure_locations` |
| Policy cells, Table 9 | `results/validation-v7/analysis.json`, `summary` |
| Case effects and token use, Figures 4-5 | Pilot `comparisons[].base_effects`; validation `comparisons` and `absolute` |
| Influential case | `results/pilot-interpretation-v2/influential-pair-audit.json` |
| Inference versions and settings | `records/execution/current-runtime.json` and frozen run/environment records |

## Refresh and checks

```bash
PYTHONPATH=src MPLCONFIGDIR=/tmp/rep-sensitivity-mpl .venv/bin/python scripts/build_manuscript.py
(cd manuscript && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex)
.venv/bin/python scripts/check_manuscript.py
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

Only marked result blocks are replaced. All eight legacy report entry points have
been exercised successfully against the single-source organization. The local
finalizer now compiles after a completed stage changes the paper, even while other
stages remain pending. The full-study completion gate and manual push rule remain
unchanged. Later completed findings update the abstract and conclusion through
the same completion checks. A successful build still requires scientific review.

The full suite passes **87 tests**. The paper passes abstract length, single-file,
figure location, citation resolution, table/figure cross-reference, anonymous
metadata, page limit, and overflow checks. Every page was visually inspected, with
figure and table layout corrections applied. Rendered pages and test logs remain
in ignored artifacts rather than Git.

## Points for the author's scientific review

1. Assess the claimed distinction from work that already studies restatement,
   summaries, provenance, and hierarchy. The restricted root interface and
   complementary constraints define the narrower contribution.
2. Review the decision-support abstraction and its conservative treatment of
   unknown or disputed fields. Representation validity and a determined answer
   must remain separate outcomes.
3. Review the exploratory status and policy denominators of pilot/validation
   comparisons. Stage differences do not identify why generalization changed.
4. Integrate only completed held-out and intervention analyses before making
   confirmation or mechanism claims. The current draft deliberately leaves those
   results pending.
5. Review the actual human scientific contribution and truthful assistance
   disclosure against the official conference policy in [CONFERENCE.md](CONFERENCE.md).
   This draft does not certify policy eligibility or submission readiness.
