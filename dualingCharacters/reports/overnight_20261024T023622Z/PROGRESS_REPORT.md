# Overnight progress report

Window began **2026-10-24T02:36:22+00:00** (2026-10-23 22:36:22 EDT). This report was generated **2026-10-24T11:54:45.453710+00:00** (2026-10-24 07:54:45 EDT), after **9.31 actual hours**. Target handoff: 2026-10-24T12:36:22Z. The ten-hour supervision session remains active.

## Scientific and operational integrity

All **58 core** and **21 supplementary** frozen files match. No scientific file, model, seed, endpoint, training budget, sample allocation, decoding setting, checkpoint rule or queue order was changed. No duplicate controller or discretionary GPU job was launched. Nothing was pushed, published, submitted or sent to raters. The new tools perform local analysis and read-only monitoring.

Core scientific source commit: `a62f1881d23df2282b410243ad4575bb11d1d74a`. Core manifest SHA256: `135e78e2423d0bc42e340098021a912df269a39949d50cb6fbf91d4edb93f2f3`. Review manifest SHA256: `67647b93947969740702e7054af8162635a03c97a64dee10a7895d9ce375ae81`.

Starting commit: `7c4e2ee`. Source/report HEAD when generated: `dc2f65fa651df24b9026622d2fcc0a4b3fc648fd`. The final report commit, if later, is visible in `git log`; a report cannot embed its own eventual commit hash. No tracked files are intentionally left uncommitted. Active campaign state, raw logs, adapters and checkpoints remain Git ignored and locally mirrored.

- `dc2f65f Record second adversarial seed and preserve contrasting seed outcomes`
- `6447796 Retain second clean-training seed and audit adapter lineage`
- `ecfec11 Record motive-only control and ten-fit exposure audit`
- `ffa0320 Record first C5 comparison and refresh reproducible evidence reports`
- `3ed5b01 Extend exposure diagnostics and overnight handoff tooling`
- `09fb6a1 Add overnight monitoring and incremental evidence package`

## Queue and resources

**42/241** scheduled core stages are complete. **25** completed after the starting inventory. Current stage: `main-qwen-c5-29-r0-collect` (running); 320 generation requests and 0 training input tokens in the latest stage status. Progress snapshot: 2026-10-24T11:54:03.240745+00:00.

Next scheduled stage after the active operation: `main-qwen-c5-29-r0-fit`. **198** further stages remain in the unchanged queue. Overnight infrastructure retries: **0**. Historical failed/interrupted attempts and scientific exclusions remain recorded in [the machine-readable state](PROGRESS_STATE.json) and `configs/run_exclusions.json`; they are excluded only under the existing rules, and their compute remains charged.

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
- `main-qwen-c1-29-r0-collect`
- `main-qwen-c1-29-r0-fit`
- `main-qwen-c1-29-r1-collect`
- `main-qwen-c1-29-r1-fit`
- `main-qwen-c1-29-eval`
- `main-qwen-c3-29-r0-collect`
- `main-qwen-c3-29-r0-fit`
- `main-qwen-c3-29-r1-collect`
- `main-qwen-c3-29-r1-fit`
- `main-qwen-c3-29-eval`
- `main-qwen-c4-29-r0-collect`
- `main-qwen-c4-29-r0-fit`
- `main-qwen-c4-29-r1-collect`
- `main-qwen-c4-29-r1-fit`
- `main-qwen-c4-29-eval`

Reserved GPU time: **11.2559 h before**, **9.0419 h during**, **20.2978/96 h cumulative**, with **75.7022 h remaining** at the snapshot. Review consumption: **0.0000/2 h** cumulatively. Start-boundary reconstruction has approximately one-second clock precision. Failed attempts, loading and profiling are charged; utilization does not discount reservations.

The timing-based expected full-core total is **78.87 h**; the conservative timing scenario is **88.57 h**. These are forecasts, not guarantees or permission to shrink the grid. The earlier 92.74 h forecast is preserved separately. Supplementary work requires all 241 core stages, exact prerequisites, the cumulative two-hour subcap, and at least 30 minutes of contingency plus its existing margin.

Hardware snapshot: NVIDIA RTX 6000 Ada Generation, 49140 MiB, 40098 MiB, 100 %. Local free storage: 27.54 GiB; remote free storage: 22.56 GiB. Mirrored current status age: pending first status mirror for this newly started stage. Completed evaluation trace and adapter mirror checks are in [MIRROR_CHECKS.json](MIRROR_CHECKS.json).

Remote container PID1 start: Fri Oct 23 13:03:29 2026; measured container elapsed seconds: 82232. Completed-run sampled GPU-busy time: 18.021 h; utilization-weighted samples: 17.081 h. These are distinct from reservation time and unknown billed pod uptime. The actual hourly rate is unavailable; no dollar cost is invented.


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
| qwen | C1 | 29 | 138/240 | 313/480 |
| qwen | C3 | 29 | 181/240 | 382/480 |
| qwen | C4 | 29 | 165/240 | 357/480 |

| Model | Comparison | Seed | Difference, pp | Exploratory 95% interval, pp | Both / first only / second only / neither |
|---|---|---:|---:|---:|---:|
| qwen | C5-C3 | 17 | -3.75 | [-8.33, 0.83] | 157 / 11 / 20 / 52 |
| qwen | C5-C1 | 17 | -7.50 | [-11.25, -4.17] | 167 / 1 / 19 / 53 |
| qwen | C5-C4 | 17 | -4.58 | [-7.92, -1.25] | 165 / 3 / 14 / 58 |
| qwen | C5-A1 | 17 | -0.42 | [-5.42, 4.58] | 151 / 17 / 18 / 54 |
| qwen | C3-C1 | 17 | -3.75 | [-7.50, 0.00] | 171 / 6 / 15 / 48 |
| qwen | C3-C1 | 29 | 17.92 | [12.08, 23.75] | 131 / 50 / 7 / 52 |

One-seed intervals resample paired families (10,000 draws, seed 40721); they do not estimate training-seed variation. An interval containing zero does not establish equivalence. Complete planned three-seed comparisons use the unchanged frozen two-way procedure and fixed multiplicity family. Interim inspections never change stopping, sampling or checkpoints. [Interim-look log](INTERIM_LOOKS.jsonl), [complete-seed contrasts](complete_seed_contrasts.json).


## Exposure, failures and mechanism limits

**16 completed fits** have actual-loss exposure summaries. The six original verified audits were reused; newly completed fits were reconstructed from the exact tokenizer, sampler and packing stream and checked against every optimizer-step target count. Buffer-loaded windows, orphan-masked suffixes and resume replay are separately accounted.

| Model / condition / seed | Completed fits | Input tokens | Supervised target tokens | R1 recovery windows / families contributing loss |
|---|---:|---:|---:|---:|
| qwen / A1 / 17 | 2/2 | 2,097,152 | 80,051 | 11 / 6 |
| qwen / C1 / 17 | 2/2 | 2,097,152 | 97,683 | 14 / 9 |
| qwen / C1 / 29 | 2/2 | 2,097,152 | 96,822 | 17 / 11 |
| qwen / C3 / 17 | 2/2 | 2,097,152 | 83,466 | 33 / 18 |
| qwen / C3 / 29 | 2/2 | 2,097,152 | 83,913 | 23 / 13 |
| qwen / C4 / 17 | 2/2 | 2,097,152 | 78,417 | 14 / 8 |
| qwen / C4 / 29 | 2/2 | 2,097,152 | 79,997 | 20 / 12 |
| qwen / C5 / 17 | 2/2 | 2,097,152 | 79,238 | 31 / 17 |

Equal input-token quotas do not equalize target-token exposure. A small repeatedly sampled recovery pool is not a larger set of independent failures; partial fits in the table are not full condition budgets.

[Exposure and curriculum associations](CURRICULUM_ASSOCIATIONS.md) explicitly distinguish common input-token budgets from unequal target exposure. [Failure taxonomy](failure_taxonomy.csv) uses exclusive categories; [overlap counts](failure_overlaps.csv) retain nonexclusive flags. [Strata](strata.csv) separate familiar/held-out rules, worlds, framing and ambiguity. All 30 ambiguous locked families are creative/held-out, and all domains share the same six-slot schema. [Qualitative examples](QUALITATIVE_APPENDIX.md) are deterministically selected illustrations, not human validation.

Training peer matches are typed coordination candidates, not proof of coalitions or hidden intentions. Temporal action/error associations may include genuine intervening user updates and are not causal attack severity. Original separate-slot motives can be jointly satisfied; original C4/C5 communication routing differs. A C5 advantage by itself would not identify biographies, private histories, peer interaction, memory necessity or broad transfer.


## Unfinished evidence and submission assessment

The complete three-seed primary comparison, independent-family trained replication, remaining character-count and history/peer ablations, 32/128-turn sensitivity, larger-memory reference, common-fault recovery, unfamiliar interference, external benchmark, natural-language validation and human ratings remain required wherever their scheduled cells are pending. The full ordered list is preserved in the machine-readable state. Horizon and recovery curves must wait for their actual completed inputs; no values are interpolated from the 64-turn results. The post-review memory and contested-goal diagnostics also remain gated. The current package supports interim findings and further work, not a complete submission or a guarantee of acceptance.


## Supplement and human-review status

Review coordinator status: **waiting_for_core**. [Readiness manifest](SUPPLEMENT_READINESS.json) reports exact pending checkpoints and the full-core gate. The post-C1 supplementary protocol and selection rules remain frozen. No unavailable memory/mechanism result is inferred.

The original 60-item blinded action packet, item identities and private key are preserved; two rating forms remain blank. The separate 120-output prose packet requires its declared completed natural-language validation outputs. Missing inputs are listed in [human-review status](HUMAN_REVIEW_STATUS.json); no pilot or other condition is substituted and no ratings are fabricated.


## Reproducible package and continuation

[Figures and captions](FIGURES.md), [training curves](TRAINING_CURVES.md), [compute and gains](COMPUTE.md), [author-review LaTeX](../../paper/overnight_author_review.tex), [draft status](DRAFT_STATUS.json), [compiled review PDF](../../paper/overnight_author_review.pdf), [build provenance](PAPER_BUILD.json), [analysis commands](../../analysis/overnight/README.md), [tests](TESTS.json), [adapter lineage](ADAPTER_LINEAGE.json), [claim-to-evidence table](CLAIM_TO_EVIDENCE.md), [provenance](PACKAGE_PROVENANCE.json). Raw traces, adapter weights, optimizer checkpoints and PDF build products remain in the established ignored local mirror. The paper is incomplete and requires human scientific authorship and review; AI assistance is logged.

Core owner: `787315  787313    15:19:14 python`. Review owner: `1291869 1291862    09:56:31 python`. Remote GPU process snapshot (PID, command): `476648, VLLM::EngineCore`. Core state/log: `artifacts/campaign_state.json`, `artifacts/campaign_controller.log`; review state/log: `artifacts/review_001/controller_state.json`, `artifacts/review_001/controller.log`. Active stage log: `artifacts/campaign_configs/main-qwen-c5-29-r0-collect.log`. Shared campaign lock: `artifacts/campaign.lock`; GPU lock: `artifacts/gpu.lock`.

Run `PYTHONPATH=src .venv/bin/python -m analysis.overnight.monitor` for a read-only live check, then `PYTHONPATH=src .venv/bin/python -m analysis.overnight.update` to integrate newly completed evidence. Do not launch another controller. [Recovery instructions](RECOVERY.md) require proving a worker has stopped, preserving artifacts, using the existing resume map, and allowing at most two retries of the same infrastructure fault. No scientific redesign is authorized while the author is asleep.

Next author decisions, when the relevant evidence is ready: review the bounded scientific interpretations; arrange two independent raters for the preserved packets; decide whether later work should test incompatible goals, routing and transfer beyond the shared schema. These are future review decisions, not prerequisites for continuing the already frozen queue.
