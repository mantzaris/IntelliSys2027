# Overnight progress report

Window began **2026-10-24T02:36:22+00:00** (2026-10-23 22:36:22 EDT). This report was generated **2026-10-24T06:23:00.469282+00:00** (2026-10-24 02:23:00 EDT), after **3.78 actual hours**. Target handoff: 2026-10-24T12:36:22Z. The ten-hour supervision session remains active.

## Scientific and operational integrity

All **58 core** and **21 supplementary** frozen files match. No scientific file, model, seed, endpoint, training budget, sample allocation, decoding setting, checkpoint rule or queue order was changed. No duplicate controller or discretionary GPU job was launched. Nothing was pushed, published, submitted or sent to raters. The new tools perform local analysis and read-only monitoring.

Starting commit: `7c4e2ee`. Source/report HEAD when generated: `ffa03208dcefa0e8919aa0e1803837d511893a32`. The final report commit, if later, is visible in `git log`; a report cannot embed its own eventual commit hash.

- `ffa0320 Record first C5 comparison and refresh reproducible evidence reports`
- `3ed5b01 Extend exposure diagnostics and overnight handoff tooling`
- `09fb6a1 Add overnight monitoring and incremental evidence package`

## Queue and resources

**27/241** scheduled core stages are complete. **10** completed after the starting inventory. Current stage: `main-qwen-c1-29-r0-collect` (running); 448 generation requests and 0 training input tokens in the latest stage status. Progress snapshot: 2026-10-24T06:20:07.432673+00:00.

Newly completed stages:

- `main-qwen-c5-17-r0-collect`
- `main-qwen-c5-17-r0-fit`
- `main-qwen-c5-17-r1-collect`
- `main-qwen-c5-17-r1-fit`
- `main-qwen-c5-17-eval`
- `main-qwen-a1-17-r0-collect`
- `main-qwen-a1-17-r0-fit`
- `main-qwen-a1-17-r1-collect`
- `main-qwen-a1-17-r1-fit`
- `main-qwen-a1-17-eval`

Reserved GPU time: **11.2559 h before**, **3.6065 h during**, **14.8625/96 h cumulative**, with **81.1375 h remaining** at the snapshot. Review consumption: **0.0000/2 h** cumulatively. Start-boundary reconstruction has approximately one-second clock precision. Failed attempts, loading and profiling are charged; utilization does not discount reservations.

The timing-based expected full-core total is **80.76 h**; the conservative timing scenario is **90.20 h**. These are forecasts, not guarantees or permission to shrink the grid. The earlier 92.74 h forecast is preserved separately. Supplementary work requires all 241 core stages, exact prerequisites, the cumulative two-hour subcap, and at least 30 minutes of contingency plus its existing margin.

Hardware snapshot: NVIDIA RTX 6000 Ada Generation, 49140 MiB, 40136 MiB, 90 %. Local free storage: 29.26 GiB; remote free storage: 24.18 GiB. Mirrored current status age: 2.4 seconds. Completed evaluation trace and adapter mirror checks are in [MIRROR_CHECKS.json](MIRROR_CHECKS.json).

Remote container PID1 start: Fri Oct 23 13:03:29 2026; measured container elapsed seconds: 62197. Completed-run sampled GPU-busy time: 12.773 h; utilization-weighted samples: 12.121 h. These are distinct from reservation time and unknown billed pod uptime. The actual hourly rate is unavailable; no dollar cost is invented.


## Main results — incomplete grid

Each row is a complete eligible 64-turn evaluation on 240 paired families (480 conversations). No pilots, partial evaluations or excluded runs enter these estimates. The single untrained reference per model is reused, not independent replication.

| Model | Condition | Seed | Paired successes | Conversation successes |
|---|---|---:|---:|---:|
| qwen | base | 17 | 67/240 | 195/480 |
| phi | base | 17 | 27/240 | 110/480 |
| qwen | C1 | 17 | 186/240 | 390/480 |
| qwen | C3 | 17 | 177/240 | 381/480 |
| qwen | C4 | 17 | 179/240 | 382/480 |
| qwen | C5 | 17 | 168/240 | 362/480 |
| qwen | A1 | 17 | 169/240 | 369/480 |

| Model | Comparison | Seed | Difference, pp | Exploratory 95% interval, pp | Both / first only / second only / neither |
|---|---|---:|---:|---:|---:|
| qwen | C5-C3 | 17 | -3.75 | [-8.33, 0.83] | 157 / 11 / 20 / 52 |
| qwen | C5-C1 | 17 | -7.50 | [-11.25, -4.17] | 167 / 1 / 19 / 53 |
| qwen | C5-C4 | 17 | -4.58 | [-7.92, -1.25] | 165 / 3 / 14 / 58 |
| qwen | C5-A1 | 17 | -0.42 | [-5.42, 4.58] | 151 / 17 / 18 / 54 |
| qwen | C3-C1 | 17 | -3.75 | [-7.50, 0.00] | 171 / 6 / 15 / 48 |

One-seed intervals resample paired families (10,000 draws, seed 40721); they do not estimate training-seed variation. An interval containing zero does not establish equivalence. Complete planned three-seed comparisons use the unchanged frozen two-way procedure and fixed multiplicity family. Interim inspections never change stopping, sampling or checkpoints. [Interim-look log](INTERIM_LOOKS.jsonl), [complete-seed contrasts](complete_seed_contrasts.json).


## Exposure, failures and mechanism limits

**10 completed fits** have actual-loss exposure summaries. The six original verified audits were reused; newly completed fits were reconstructed from the exact tokenizer, sampler and packing stream and checked against every optimizer-step target count. Buffer-loaded windows, orphan-masked suffixes and resume replay are separately accounted.

[Exposure and curriculum associations](CURRICULUM_ASSOCIATIONS.md) explicitly distinguish common input-token budgets from unequal target exposure. [Failure taxonomy](failure_taxonomy.csv) uses exclusive categories; [overlap counts](failure_overlaps.csv) retain nonexclusive flags. [Strata](strata.csv) separate familiar/held-out rules, worlds, framing and ambiguity. All 30 ambiguous locked families are creative/held-out, and all domains share the same six-slot schema. [Qualitative examples](QUALITATIVE_APPENDIX.md) are deterministically selected illustrations, not human validation.

Training peer matches are typed coordination candidates, not proof of coalitions or hidden intentions. Temporal action/error associations may include genuine intervening user updates and are not causal attack severity. Original separate-slot motives can be jointly satisfied; original C4/C5 communication routing differs. A C5 advantage by itself would not identify biographies, private histories, peer interaction, memory necessity or broad transfer.


## Supplement and human-review status

Review coordinator status: **waiting_for_core**. [Readiness manifest](SUPPLEMENT_READINESS.json) reports exact pending checkpoints and the full-core gate. The post-C1 supplementary protocol and selection rules remain frozen. No unavailable memory/mechanism result is inferred.

The original 60-item blinded action packet, item identities and private key are preserved; two rating forms remain blank. The separate 120-output prose packet requires its declared completed natural-language validation outputs. Missing inputs are listed in [human-review status](HUMAN_REVIEW_STATUS.json); no pilot or other condition is substituted and no ratings are fabricated.


## Reproducible package and continuation

[Figures and captions](FIGURES.md), [training curves](TRAINING_CURVES.md), [compute and gains](COMPUTE.md), [author-review LaTeX](../../paper/overnight_author_review.tex), [draft status](DRAFT_STATUS.json), [analysis commands](../../analysis/overnight/README.md), [tests](TESTS.json), [provenance](PACKAGE_PROVENANCE.json). Raw traces, adapter weights, optimizer checkpoints and PDF build products remain in the established ignored local mirror. The paper is incomplete and requires human scientific authorship and review; AI assistance is logged.

Core owner: `787315  787313    09:45:18 python`. Review owner: `1291869 1291862    04:22:35 python`. Core state/log: `artifacts/campaign_state.json`, `artifacts/campaign_controller.log`; review state/log: `artifacts/review_001/controller_state.json`, `artifacts/review_001/controller.log`. Shared campaign lock: `artifacts/campaign.lock`; GPU lock: `artifacts/gpu.lock`.

Run `PYTHONPATH=src .venv/bin/python -m analysis.overnight.monitor` for a read-only live check, then `PYTHONPATH=src .venv/bin/python -m analysis.overnight.update` to integrate newly completed evidence. Do not launch another controller. [Recovery instructions](RECOVERY.md) require proving a worker has stopped, preserving artifacts, using the existing resume map, and allowing at most two retries of the same infrastructure fault. No scientific redesign is authorized while the author is asleep.

Next author decisions, when the relevant evidence is ready: review the bounded scientific interpretations; arrange two independent raters for the preserved packets; decide whether later work should test incompatible goals, routing and transfer beyond the shared schema. These are future review decisions, not prerequisites for continuing the already frozen queue.
