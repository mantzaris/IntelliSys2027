# Pilot mechanism audit, amendment v1

This is a dated exploratory reanalysis of the preserved Qwen3 pilot, not a new
held-out test. The original analysis and outputs are unchanged. The original
held-out run had already started when the user introduced the revised question;
no held-out model choices were inspected to design this amendment.

The pilot contains 24 independent base pairs (12 scheduling, 12 secondary
workflow), 1,152 trajectories and 2,304 accepted model calls. Worlds, policies,
renderings and stochastic repetitions from one base remain dependent. Reanalysis
reproduces the original score hash; numerical differences are below 1e-12.

All selected reports were correct. In each population, 3 of 24 selected world-level
reports were Boolean-counterfactual-decisive. Objective reports are outside that
Boolean-flip definition, so the other reports must not all be called irrelevant.
Scheduling repeated each of the four task families in six worlds. Workflow
repeated objectives and delivery in ten worlds each, screening and audit in two
each. No selected objective favored a globally fastest infeasible candidate.
The pilot therefore does not identify false-report effects or systematically test
the proposed target-specificity explanation.

Paired estimates below average ordinary and checklist policies within each base,
then weight bases equally. Intervals resample independent bases within mutation
family and change status (10,000 draws). A positive value means increased
correctness or retention. These are development estimates, not confirmatory tests.

| Population | Repetition | Correctness change, pp [95% CI] | Necessary-claim retention change, pp [95% CI] | Boolean-critical retention change, pp [95% CI] |
|---|---|---:|---:|---:|
| schedule | exact | +13.5 [+4.2, +22.9] | +5.2 [-0.0, +10.4] | -0.3 [-1.2, +0.7] |
| schedule | paraphrase | +10.4 [+1.0, +19.8] | +3.6 [-1.0, +8.2] | -0.9 [-2.2, +0.3] |
| workflow | exact | +2.1 [-3.1, +7.3] | +0.3 [-1.9, +2.6] | -2.2 [-4.3, +0.0] |
| workflow | paraphrase | +4.2 [-2.1, +10.4] | +0.7 [-0.9, +2.3] | -1.0 [-2.1, +0.0] |

Gains were not distributed uniformly. The largest scheduling point estimates
occurred in numerical-mutation bases. Both policies benefited on exact copies;
paraphrase gains were larger under ordinary synthesis. The subgroup estimates
below are exploratory, with only four independent bases per mutation family.

| Mutation family | Exact correctness change, pp [95% CI] | Paraphrase change, pp [95% CI] |
|---|---:|---:|
| numeric | +34.4 [+6.2, +62.5] | +21.9 [-6.2, +50.0] |
| identity | -3.1 [-6.2, +0.0] | +0.0 [+0.0, +0.0] |
| dependency | +9.4 [+6.2, +12.5] | +9.4 [+6.2, +12.5] |
| quantifier | +0.0 [+0.0, +0.0] | +0.0 [+0.0, +0.0] |
| condition | +0.0 [-6.2, +6.2] | +6.2 [+0.0, +12.5] |
| version | +6.2 [-6.2, +18.8] | +6.2 [-6.2, +18.8] |

Repeated-objective scheduling bases had a +33.3 pp point estimate under each
repetition type, but there were only three such bases and singleton strata prevent
the requested stratified interval. This is not a randomized target comparison.
Four-job versus five-job estimates also differ; job count is entangled with family
and target, so these data do not identify a task-difficulty effect. The new
within-world target comparisons address this limitation directly.

Necessary scopes are those whose removal makes the correct choice underdetermined;
this includes objective values. Boolean-critical scopes are those whose isolated
truth-value flip changes the choice. Retention requires an explicit correct value
at the correct scope, with no contrary value or unresolved flag. Failed summaries
count as losses. Claims and citations are measured separately. These are observable
outputs, not a faithful record of hidden reasoning.

Flat scheduling was at its accuracy ceiling. No pilot output failed parsing or
hit the output cap, so the observed gains were not a reduction in those operational
failures. Valid JSON nevertheless included empty summaries and Boolean values in
objective scopes. Necessary-claim retention is more informative here than a metric
restricted to mandatory Boolean constraints, whose retention was near ceiling.

Calibration and confidence do not move uniformly. In hierarchical scheduling,
the exact-copy Brier change was -0.083 [-0.138, -0.029];
the paraphrase Brier change was -0.061 [-0.127, +0.007].
The full CSV retains log loss and confidence changes conditional on an unchanged
choice; conditioning on answer consistency is descriptive and cannot establish
increased reliability. Subgroup estimates by task, family, policy and job count
are also retained. Singleton-stratum intervals are withheld; zero-width empirical
intervals elsewhere do not establish robustness.

The systematic trace selection takes the largest and smallest base-average
accuracy change per mutation family and a hash-selected entirely unchanged base
when one exists. A zero extremum is explicitly labeled, not narrated as a gain or
loss. Selection IDs and all matched outputs are in `trace_selection.csv` and the
ignored, locally mirrored `artifacts/analyses/pilot-mechanism-v1/trace-packets.json`.
The following inspected examples diagnose different failure locations:

| Base pair | Inspection finding | Interpretation |
|---|---|---|
| `e765f8bb5f0e2aad` | Baseline manager reports objectives as Boolean values; repeated input produces numerical 8/9/9 and the correct choice C39. | Numerical meaning/type preservation, despite full Boolean-critical retention in both arms. |
| `973c791a1ea121ee` | The repeated root chooses C20 despite receiving its failed resource finding; C71 is correct. | Integration failure after the decisive information reaches the root. |
| `160bd558b5de3da4` | Repeated-input manager emits an empty assertion list; the root returns INSUFFICIENT instead of C76. | Loss at the summary boundary, despite syntactically valid output. |
| `468f3ff2a65c256b` | The manager on the unchanged branch becomes empty; correct C14 changes to INSUFFICIENT. | An unaffected branch can vary; this individual deterioration cannot be attributed solely to its repeated report. |
| `319832d2a013062e` | Baseline summary omits objectives; paraphrased input retains 5/7/11 and the root chooses C74. | Objective delivery can be a bottleneck. |
| `d875d0de865444e5` | Both inputs select correct C12 despite a lost irrelevant finding. | Answer stability alone does not show complete information preservation. |

The aggregate source files, rather than these selected examples, determine effect
estimates. A new calibration metric does not change the trace-selection hash.

Among paired calls on the unexposed manager branch, prompts and requested seeds
were identical in all 192 comparisons per population. Raw responses differed in
17 scheduling and 20 workflow comparisons; normalized emitted findings differed
in 0 and 2, respectively. The audit does not identify the numerical or batching
cause. The new extension explicitly shares identical manager computations within
a world and stochastic repetition, so bypass sees the same summaries. Separate
stochastic repetitions remain separate. Physical calls and logical decision-graph
costs are reported separately.

The pilot supports a conditional investigation of summary transport and integration.
It does not establish that repetition suppresses exceptions, that selective
repetition generally helps, or that all gains are mediated by claim retention.
The bounded extension separates decisive, nondecisive, favorable-but-limited,
false and uniform repetition; matches overlapping presentations; and uses bypass,
lossless transport, length and position interventions. Existing full live-worker
baselines failed adequacy (Qwen3 4/12; Phi-4 3/12), so the new fresh-execution probe
is explicitly narrow and diagnostic. No new source observations are claimed.

Reproduce with the commands in `README.md`. All numerical statements trace to
`results/pilot-mechanism-v1/` or `records/gates/live-development-v8-*.json`.
