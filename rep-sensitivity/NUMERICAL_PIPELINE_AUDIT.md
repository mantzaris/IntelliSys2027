# Numerical-information pipeline audit

This completed CPU analysis uses immutable pilot and validation outputs: 60 independent base pairs (24 development plus 36 validation, shared across the validation models), 3,168 hierarchical trajectories and 6,336 manager summaries. No partial main outcomes or new GPU responses were used.

The first numerical-to-Boolean change is in the **raw model-generated manager response**. Every audited manager input matches its frozen report text and scope registry; raw assertion values match the parsed values, and parsed summaries match the actual root inputs. All construction, parsing, transport and primary-choice-score discrepancy counts are zero. No manager output was truncated. Representative raw summary text, full objective scope fields, report excerpts and immutable call hashes are in `results/numerical-pipeline-v1/representative-traces.json`. Unaffected controls are included.

The original prompt states that objectives are numbers. Its assertion example uses `true` with an explicit placeholder warning, and its common JSON schema permits Boolean or number at every key. The schema therefore fails to prevent the observed semantic type error. The audit does not establish that the example or schema caused the behavior. Parsing changes object assertions into triples without converting their values. Type-safe scoring distinguishes Boolean `true` from numeric 1; integral floats remain legitimate numbers. The earlier integer/float retention-scoring correction remains separate from this audit. No additional score correction or GPU rerun is indicated.

| Scheduling group | Condition | Bases | Trajectories | Objective fields | Boolean | Omitted | Preserved |
|---|---|---:|---:|---:|---:|---:|---:|
| Pilot Qwen3 (2 policies) | single | 12 | 96 | 288 | 60 | 9 | 219 |
| Pilot Qwen3 (2 policies) | exact | 12 | 96 | 288 | 9 | 9 | 270 |
| Pilot Qwen3 (2 policies) | paraphrase | 12 | 96 | 288 | 24 | 9 | 255 |
| Validation Qwen3 (3 policies) | single | 18 | 216 | 648 | 53 | 34 | 561 |
| Validation Qwen3 (3 policies) | exact | 18 | 216 | 648 | 64 | 35 | 549 |
| Validation Qwen3 (3 policies) | paraphrase | 18 | 216 | 648 | 69 | 36 | 543 |
| Validation Phi-4 (3 policies) | single | 18 | 216 | 648 | 156 | 25 | 458 |
| Validation Phi-4 (3 policies) | exact | 18 | 216 | 648 | 156 | 40 | 449 |
| Validation Phi-4 (3 policies) | paraphrase | 18 | 216 | 648 | 150 | 21 | 474 |

Fields are unique full-scope candidate objectives per trajectory. Copies are not extra denominator units. Boolean, omission, unresolved/conflict and citation labels are reported separately and can overlap; preserved requires every emitted value at the correct scope to match and no unresolved flag. A number at the wrong candidate is not preserved. Numeric errors, scope-citation mismatches, workflow results and all policy strata are in `analysis.json` and `field-summary.csv`. Every number emitted at a known objective key in these intermediate summaries matched its source; failures included Boolean replacement, omission or unresolved information.

The anomaly recurs across bases and models, but the pilot reduction in Boolean replacement does not generalize to validation. Correctly delivered information also does not guarantee a correct root choice. In scheduling validation, with all three policies, Qwen3 made 24 wrong choices among 185 unrepeated contexts with sufficient, consistent, correctly delivered facts. This is an observational conditional denominator, not an estimate of mediation. Workflow sufficiency is conservatively restricted to completely preserved propositions; no unvalidated scheduling scorer is applied to that task.

The direct, exploratory Qwen3 change in the exact-repetition effect from pilot to validation is -17.01 points [95% interval -29.51, -4.86]. It compares 12 pilot with 18 validation scheduling bases, ordinary/checklist policies, two worlds and two repetitions, resampling independent stage clusters. Different graph/parameter/template and NONE/tie distributions preclude attributing this stage difference to one feature. Exact-versus-paraphrase direct contrasts are also reported.

The focused numerical-preservation replay is separately frozen and pending. It reuses the six previously selected diagnostic bases, including two with baseline objective loss and four without, rather than selecting new cases by decision outcomes. Its 48 fresh root calls cross cached upstream single/exact treatments with ordinary/objective-only repaired delivery. All eligible branch-visible objectives are handled equally; every replacement, addition and objective-specific unresolved-flag removal is logged. Other summary content remains intact. The comparison estimates repair of fixed summaries and an interaction conditional on cached manager outputs, not a fresh complete-hierarchy experiment or full causal mediation. Existing fresh confirmation does not independently confirm this repair interaction.

Reproduce with `PYTHONPATH=src .venv/bin/python scripts/audit_numerical_pipeline.py` and `PYTHONPATH=src MPLCONFIGDIR=/tmp/rep-sensitivity-mpl .venv/bin/python scripts/build_numerical_report.py`. Detailed field records stay in the mirrored, ignored artifact package; compact results and representative traces are versioned.

Paired objective-preservation estimates below use the **same two policies** in all stages. Each trajectory contributes the fraction of its three objective propositions preserved. Improvements/regressions compare that fraction; they are not counts of corrected final answers. Calls count all three original hierarchy calls in both paired conditions.

| Group | Bases | Trajectories per arm | Calls, both arms | Single % | Exact % | Difference, points [95% interval] | Improved / regressed / unchanged |
|---|---:|---:|---:|---:|---:|---:|---:|
| pilot-v7 / qwen3 | 12 | 96 | 576 | 76.04 | 93.75 | +17.71 [3.12, 32.29] | 17 / 0 / 79 |
| validation-v7 / qwen3 | 18 | 144 | 864 | 89.58 | 84.72 | -4.86 [-12.50, 0.69] | 2 / 9 / 133 |
| validation-v7 / phi4 | 18 | 144 | 864 | 68.75 | 67.36 | -1.39 [-6.25, 4.86] | 5 / 7 / 132 |

Representation validity and decision support are distinct. The v3 analysis-only supplement retains the strict v2 invalid/contradictory labels but also asks whether the answer is unchanged under **every admissible completion of the unknown or disputed fields**, holding uncontested supplied assertions fixed. It never supplies missing truth. Two of the four invalid baseline contexts in the fixed root diagnostic still identify the only feasible candidate; the other two permit several answers. Thus objective loss is not automatically decision-critical, and correctness in the former contexts is not merely lucky guessing. The six-base repair design stays unchanged; only one of its two baseline-loss bases has decision-relevant numerical uncertainty. This further limits precision and interpretation.

The strict v2 files and original primary world-correctness scores are preserved. `visible-support-v3.json` reports the supplemental denominators. Raw summaries are not repaired by the scorer; it does not settle a disputed field simply because that field is irrelevant to the choice.

| Scheduling baseline, all available policies | Trajectories | Uniquely supported decisions | Root choices violating that decision | Determinate despite representation errors |
|---|---:|---:|---:|---:|
| Pilot Qwen3 (2 policies) | 96 | 75 | 2 | 4 |
| Validation Qwen3 (3 policies) | 216 | 195 | 24 | 10 |
| Validation Phi-4 (3 policies) | 216 | 133 | 15 | 13 |

These are descriptive, dependent trajectory counts. A supported choice is conditional on uncontested supplied assertions; world correctness remains separately scored.
