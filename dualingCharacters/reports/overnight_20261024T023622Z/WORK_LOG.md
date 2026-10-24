# Overnight work log

Window: 2026-10-24 02:36:22–12:36:22 UTC, corresponding to October 23,
22:36:22 through October 24, 08:36:22 America/New_York (EDT).
This is a supervision window, not an extension of the 96-hour resource ceiling.

## Starting verification

The repository is clean on main at `7c4e2ee`. There is no applicable AGENTS.md in
this project's ancestors or subtree; the neighboring rep-sensitivity instructions
do not apply. The existing core PID 787315 and review coordinator PID 1291869 are
alive. C4 seed17 has finished since the last report; C5 round-zero collection is
currently running. No duplicate controller or worker has been launched.

The pod reports RTX 6000 Ada, 49,140 MiB VRAM, about 40,144 MiB occupied, 93% GPU
utilization, active vLLM worker PID 278247 and 26 GiB available storage. The active
C5 collection has recorded 3,392 model requests after 422 reserved seconds. These
are progress measurements, not task-success results. Remote container PID1 began
2026-10-23 13:03:29 UTC; container lifetime is not known billed uptime.

## Priorities and boundaries

1. Validate each newly completed eligible evaluation once; cache raw-derived
   summaries, paired transitions and failure flags with exact provenance.
2. Reuse six already verified exposure audits; reconstruct only new fits with the
   frozen packing/sampling functions and exact tokenizer bytes.
3. Maintain runtime-only resource forecasts, mirror checks and stage progress.
4. Produce reproducible figures, traceable qualitative examples, human-review
   readiness and a clearly incomplete author-review draft.
5. Recheck freezes, commit compact outputs on main and document the live queue at
   handoff. Routine infrastructure recovery is limited to the existing audited
   resume mechanism, at most two retries and only after proving no worker remains.

Core state/log: `artifacts/campaign_state.json`, `artifacts/campaign_controller.log`.
Review state/log: `artifacts/review_001/controller_state.json`, `controller.log`.
GPU stages use `artifacts/gpu.lock`; the core holds `artifacts/campaign.lock`.
Do not start another controller. The supplementary coordinator remains CPU-only
until **all 241 core stages** finish, then applies its existing frozen resource gate.

- 2026-10-24T02:42:49.741539+00:00: Validated completed base-qwen-eval: 67/240 paired success. Scanned all 30,720 raw turns once.

- 2026-10-24T02:42:56.416829+00:00: Validated completed base-phi-eval: 27/240 paired success. Scanned all 30,720 raw turns once.

- 2026-10-24T02:42:56.948724+00:00: Validated completed main-qwen-c1-17-eval-format2: 186/240 paired success. Reused prior verified final-prompt cache.

- 2026-10-24T02:42:57.508057+00:00: Validated completed main-qwen-c3-17-eval: 177/240 paired success. Reused prior verified final-prompt cache.

- 2026-10-24T02:43:04.608998+00:00: Validated completed main-qwen-c4-17-eval: 179/240 paired success. Scanned all 30,720 raw turns once.

- 2026-10-24T02:51:49.130091+00:00: Remote/local completed-evaluation checksums match for base-phi-eval, base-qwen-eval, main-qwen-c1-17-eval-format2, main-qwen-c3-17-eval, main-qwen-c4-17-eval.

- 2026-10-24T02:53:15.794211+00:00: Extended collection audit for main-qwen-c5-17-r0-collect: 464 clean and 347 failed eligible windows; temporal severity remains noncausal.

- 2026-10-24T03:01:35.954148+00:00: Progress: 18/241 core stages complete; active main-qwen-c5-17-r0-fit, 0 generation requests, 847872 training input tokens; 11.6707/96 reserved hours. Review remains waiting_for_core.

- 2026-10-24T03:04:13.239403+00:00: First 30-minute deliverables: five validated main evaluations (including newly inspected C4 179/240), six reused exact exposure audits, seven collection audits, five figure sets, a ten-page compiled author-review draft, and a preserved 60-item action packet with two blank rating forms. A temporary three-minute mirror lag cleared without intervention; a 198.8 MB optimizer snapshot was being transferred while training continued. No GPU retry or controller change.

- 2026-10-24T03:06:24.153894+00:00: Reconstructed main-qwen-c5-17-r0-fit: 39436 target tokens; 559 distinct windows actually contributed loss. Every optimizer step matched.

- 2026-10-24T03:07:05.342782+00:00: C5 seed17 round-zero fit completed and mirrored; exact loss reconstruction passed for the seventh fit. The existing controller advanced into its fixed round-one refresh collection. No retry, source amendment, or supplementary GPU call was needed.

- 2026-10-24T03:10:27.843419+00:00: Progress: 19/241 core stages complete; active main-qwen-c5-17-r1-collect, 2624 generation requests, 0 training input tokens; 11.8033/96 reserved hours. Review remains waiting_for_core.

- 2026-10-24T03:18:23.457024+00:00: Added descriptive curriculum/outcome joins, completed-fit training curves, read-only supplementary readiness and incremental handoff/provenance generation. Five focused analysis tests pass. No new GPU calls or core changes.

- 2026-10-24T03:22:00.738266+00:00: Storage audit: completed-run checkpoints use existing content-preserving hard links. Pending-fit planning proxy is 20.04 GiB; local free 30.03 GiB. No deletion or new cleanup policy introduced.

- 2026-10-24T03:30:08.890452+00:00: Progress: 20/241 core stages complete; active main-qwen-c5-17-r1-fit, 0 generation requests, 32768 training input tokens; 12.1252/96 reserved hours. Review remains waiting_for_core.

- 2026-10-24T03:30:10.159432+00:00: Extended collection audit for main-qwen-c5-17-r1-collect: 745 clean and 31 failed eligible windows; temporal severity remains noncausal.

- 2026-10-24T03:30:38.533053+00:00: C5 seed17 round-one collection completed: 745 clean and 31 failed eligible windows from 17 failed families, one verified model-recovery candidate. The action audit found 1,089 delivered antagonist peer messages, two typed follow-ups and zero repeated directed candidates; these are observational flags, not coalition evidence. Final fitting is underway.

- 2026-10-24T03:48:01.973002+00:00: Progress: 21/241 core stages complete; active main-qwen-c5-17-eval, 0 generation requests, 0 training input tokens; 12.4104/96 reserved hours. Review remains waiting_for_core.

- 2026-10-24T03:48:05.191647+00:00: Reconstructed main-qwen-c5-17-r1-fit: 39802 target tokens; 333 distinct windows actually contributed loss. Every optimizer step matched.

- 2026-10-24T03:49:38.753155+00:00: C5 seed17 final fit completed: 39,802 new target tokens, 79,238 across both fixed rounds. All 256 optimizer-step target counts matched exact reconstruction. Its 31 recovery windows from 17 families contributed loss on 299 occurrences; the top five supplied 20.80% of recovery target tokens. The existing queue advanced to the fixed 240-family C5 evaluation.

- 2026-10-24T03:51:08.773411+00:00: Remote/local completed-stage checksums match for main-qwen-c1-17-r0-collect, main-qwen-c1-17-r1-collect-format2, main-qwen-c3-17-r0-collect, main-qwen-c3-17-r1-collect, main-qwen-c4-17-r0-collect, main-qwen-c4-17-r1-collect, main-qwen-c5-17-r0-collect, main-qwen-c5-17-r1-collect, main-qwen-c1-17-r0-fit-format2, main-qwen-c1-17-r1-fit-format2, main-qwen-c3-17-r0-fit, main-qwen-c3-17-r1-fit, main-qwen-c4-17-r0-fit, main-qwen-c4-17-r1-fit, main-qwen-c5-17-r0-fit, main-qwen-c5-17-r1-fit.

- 2026-10-24T04:24:44.470656+00:00: Validated completed main-qwen-c5-17-eval: 168/240 paired success. Scanned all 30,720 raw turns once.

- 2026-10-24T04:26:11.482764+00:00: Remote/local completed-stage checksums match for main-qwen-c5-17-eval.

- 2026-10-24T04:26:13.072969+00:00: Progress: 22/241 core stages complete; active main-qwen-a1-17-r0-collect, 1408 generation requests, 0 training input tokens; 13.0380/96 reserved hours. Review remains waiting_for_core.

- 2026-10-24T04:27:36.210961+00:00: First complete fixed C5 seed17 test validated and mirrored: 168/240 paired success; C5−C3 −3.75 pp (family 95% interval −8.33 to +0.83), C5−C1 −7.50 pp (−11.25 to −4.17). All 30,720 raw rows, 480 unique paired worlds, source/configuration/model and final adapter hashes checked. Negative finding retained; no queue or scientific change. A1 collection running.

- 2026-10-24T04:29:31.199169+00:00: Reporting-only correction: analysis/execution_report.py previously combined fresh outcome tables with stale cached resource totals (6.965 h). Added a small metadata-only resource refresh using the existing aggregation definitions and a regression test for stale caches and duplicate heartbeats. Actual GPU ledger/controller enforcement was already current; no scientific file or run was affected. Existing tests now 31 passed, plus 15 supplement/overnight tests.
