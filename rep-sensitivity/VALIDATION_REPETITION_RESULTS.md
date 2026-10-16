# Validation repetition results

This is a new offline analysis of **already completed original validation**: 36 independent base pairs, 5,184 trajectories and 10,368 accepted calls across two models. It uses no new GPU calls and reads no unfinished main-test choices. Scheduling and workflow results remain separate.

The table matches the pilot’s ordinary/checklist policies. Each row uses 18 scheduling pairs, 144 trajectories per condition, two worlds and two stochastic repetitions. Estimates average complete base clusters; 95% intervals resample bases within mutation-family × decision-change strata.

| Model | Repetition | Single % | Repeated % | Difference, points [95% interval] | Corrections / regressions / unchanged |
|---|---|---:|---:|---:|---:|
| Qwen3-14B | exact | 79.86 | 76.39 | -3.47 [-10.42, 2.78] | 7 / 12 / 125 |
| Qwen3-14B | paraphrase | 79.86 | 78.47 | -1.39 [-5.56, 2.78] | 7 / 9 / 128 |
| Phi-4 | exact | 72.22 | 73.61 | +1.39 [-4.17, 6.25] | 8 / 6 / 130 |
| Phi-4 | paraphrase | 72.22 | 72.92 | +0.69 [-4.17, 4.86] | 8 / 7 / 129 |

The pilot’s large mean benefit does not reproduce in this validation aggregate. The intervals allow modest benefits and harms; this does not establish that repetition is ineffective. Validation uses different job sizes, parameter ranges and renderings, and includes NONE/tie cases absent from parts of the pilot. These are exploratory validation estimates, not a replacement for the frozen held-out test.

With all three policies, scheduling hierarchy accuracy is Qwen3-14B 80.09% → 79.17% (exact); Phi-4 69.44% → 70.83% (exact). Full policy, task, direct exact-versus-paraphrase, hierarchy-interaction and paired-world tables are in the machine-readable analysis.

Failure labels distinguish omitted propositions, wrong scoped values, ignored delivered constraints, feasible-but-suboptimal choices, erroneous support and response-contract failures. Labels overlap. They describe observable outputs; they do not identify an internal reasoning process or causal mediation.

The root diagnostic remains pending until the current Qwen stage finishes. Its frozen inputs contain 8 sufficient-consistent and 4 ill-typed contexts; lossless transport has 12 sufficient-consistent contexts. Repetition holds these states fixed. It includes each candidate objective selectively and all objectives uniformly, but no paraphrase arm. The analysis now distinguishes no consistent completion from multiple possible answers and from a uniquely justified decision.

The influential pilot base `e765f8bb5f0e2aad` remains included. Both worlds have feasible objective values 8, 9, 9. All eight unrepeated hierarchical contexts emit Boolean `true` in every objective slot; only one final answer is correct. Exact repetition restores numeric objectives in all eight and all eight choices are correct. The repeated report concerns C64 (9), whereas C39 (8) is correct. The sole feature hypothesis is improved numerical-objective preservation, tested by the already frozen lossless-transport interaction. This case alone does not isolate arithmetic, position or attention.

Reproduce: `PYTHONPATH=src .venv/bin/python scripts/analyze_validation_repetition.py` and `PYTHONPATH=src MPLCONFIGDIR=/tmp/rep-sensitivity-mpl .venv/bin/python scripts/build_empirical_update.py`. Raw calls remain under ignored `artifacts/runs/validation-v7/`; compact tables and figures are under `results/validation-repetition-v1/`.
