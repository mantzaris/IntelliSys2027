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

- 2026-10-24T04:37:37.573466+00:00: Two-hour progress: five additional core stages finished since start, including complete C5 seed17; A1 r0 collection has 6,976 generation requests. 13.2129/96 reserved hours, no review GPU use, no retries or new holds. Expected/conservative total forecasts 83.36/90.78 hours. Negative C5 result and both-control comparisons committed as ffa0320. Monitoring continues until the original 12:36:22 UTC handoff target.

- 2026-10-24T04:46:37.731102+00:00: Progress: 23/241 core stages complete; active main-qwen-a1-17-r0-fit, 0 generation requests, 393216 training input tokens; 13.3709/96 reserved hours. Review remains waiting_for_core.

- 2026-10-24T04:46:38.634997+00:00: Extended collection audit for main-qwen-a1-17-r0-collect: 486 clean and 315 failed eligible windows; temporal severity remains noncausal.

- 2026-10-24T04:46:52.388779+00:00: Remote/local completed-stage checksums match for main-qwen-a1-17-r0-collect.

- 2026-10-24T05:00:15.391325+00:00: Reconstructed main-qwen-a1-17-r0-fit: 40157 target tokens; 558 distinct windows actually contributed loss. Every optimizer step matched.

- 2026-10-24T05:05:07.534264+00:00: Progress: 24/241 core stages complete; active main-qwen-a1-17-r1-collect, 4160 generation requests, 0 training input tokens; 13.6673/96 reserved hours. Review remains waiting_for_core.

- 2026-10-24T05:05:09.960596+00:00: Remote/local completed-stage checksums match for main-qwen-a1-17-r0-fit.

- 2026-10-24T05:26:48.066774+00:00: Progress: 25/241 core stages complete; active main-qwen-a1-17-r1-fit, 0 generation requests, 188416 training input tokens; 13.9919/96 reserved hours. Review remains waiting_for_core.

- 2026-10-24T05:26:49.320497+00:00: Extended collection audit for main-qwen-a1-17-r1-collect: 761 clean and 11 failed eligible windows; temporal severity remains noncausal.

- 2026-10-24T05:27:02.953355+00:00: Remote/local completed-stage checksums match for main-qwen-a1-17-r1-collect.

- 2026-10-24T05:38:19.984204+00:00: Three-hour progress: 25/241 stages complete, eight added since start; A1 final fit at 839,680 input tokens. Reserved use 14.1771/96 h, review 0 h. No infrastructure retry or scientific amendment. First C5 negative comparison remains unchanged; final A1 evaluation and all seed/model replications remain pending.

- 2026-10-24T05:43:40.786914+00:00: Reconstructed main-qwen-a1-17-r1-fit: 39894 target tokens; 316 distinct windows actually contributed loss. Every optimizer step matched.

- 2026-10-24T05:47:11.820371+00:00: Progress: 26/241 core stages complete; active main-qwen-a1-17-eval, 4288 generation requests, 0 training input tokens; 14.3206/96 reserved hours. Review remains waiting_for_core.

- 2026-10-24T05:47:14.171897+00:00: Remote/local completed-stage checksums match for main-qwen-a1-17-r1-fit.

- 2026-10-24T06:20:07.437867+00:00: Progress: 27/241 core stages complete; active main-qwen-c1-29-r0-collect, 448 generation requests, 0 training input tokens; 14.8625/96 reserved hours. Review remains waiting_for_core.

- 2026-10-24T06:20:13.558875+00:00: Validated completed main-qwen-a1-17-eval: 169/240 paired success. Scanned all 30,720 raw turns once.

- 2026-10-24T06:22:07.763371+00:00: Remote/local completed-stage checksums match for main-qwen-a1-17-eval.

- 2026-10-24T06:22:08.365240+00:00: A1 seed17 completed and validated: 169/240 paired success. C5−A1 −0.42 pp, exploratory family 95% interval −5.42 to +4.58; transitions 151 both, 17 C5-only, 18 A1-only, 54 neither. This does not establish narrative advantage or equivalence. Original queue entered C1 seed29, with no outcome-based changes.

- 2026-10-24T06:29:07.843970+00:00: Progress: 28/241 core stages complete; active main-qwen-c1-29-r0-fit, 0 generation requests, 237568 training input tokens; 15.0060/96 reserved hours. Review remains waiting_for_core.

- 2026-10-24T06:29:08.315221+00:00: Extended collection audit for main-qwen-c1-29-r0-collect: 477 clean and 326 failed eligible windows; temporal severity remains noncausal.

- 2026-10-24T06:29:48.322358+00:00: Remote/local completed-stage checksums match for main-qwen-c1-29-r0-collect.

- 2026-10-24T06:40:18.693369+00:00: Four-hour progress: 28/241 complete, eleven added since start; C1 seed29 first fit at 909,312 input tokens. 15.1828/96 reserved h; review remains zero. Local/remote free space 28.92/23.87 GiB. No retries, holds, source changes or altered scientific decisions. Latest completed result remains A1 seed17 169/240, committed ecfec11.

- 2026-10-24T06:44:36.098254+00:00: Reconstructed main-qwen-c1-29-r0-fit: 48489 target tokens; 614 distinct windows actually contributed loss. Every optimizer step matched.

- 2026-10-24T06:49:44.139119+00:00: Progress: 29/241 core stages complete; active main-qwen-c1-29-r1-collect, 6016 generation requests, 0 training input tokens; 15.3388/96 reserved hours. Review remains waiting_for_core.

- 2026-10-24T06:49:46.398035+00:00: Remote/local completed-stage checksums match for main-qwen-c1-29-r0-fit.

- 2026-10-24T07:00:47.510813+00:00: Progress: 30/241 core stages complete; active main-qwen-c1-29-r1-fit, 0 generation requests, 413696 training input tokens; 15.5157/96 reserved hours. Review remains waiting_for_core.

- 2026-10-24T07:00:48.216281+00:00: Extended collection audit for main-qwen-c1-29-r1-collect: 756 clean and 17 failed eligible windows; temporal severity remains noncausal.

- 2026-10-24T07:01:06.326788+00:00: Remote/local completed-stage checksums match for main-qwen-c1-29-r1-collect.

- 2026-10-24T07:13:57.480046+00:00: Reconstructed main-qwen-c1-29-r1-fit: 48333 target tokens; 389 distinct windows actually contributed loss. Every optimizer step matched.

- 2026-10-24T07:21:56.789682+00:00: Progress: 31/241 core stages complete; active main-qwen-c1-29-eval, 8640 generation requests, 0 training input tokens; 15.8574/96 reserved hours. Review remains waiting_for_core.

- 2026-10-24T07:21:59.113079+00:00: Remote/local completed-stage checksums match for main-qwen-c1-29-r1-fit.

- 2026-10-24T07:36:59.642307+00:00: Five-hour supervision milestone: 31/241 core stages complete, fourteen added since start; C1 seed29 evaluation running (18,880 generations in the 07:33 UTC snapshot). Twelve exact fit audits and twelve collection audits are complete; seven main evaluations are eligible. Last reconciled reservation 16.0427/96 h, no review GPU calls, retries or holds. The original 12:36:22 UTC handoff target is unchanged.

- 2026-10-24T07:48:42.542008+00:00: Validated completed main-qwen-c1-29-eval: 138/240 paired success. Scanned all 30,720 raw turns once.

- 2026-10-24T07:50:32.074314+00:00: Remote/local completed-stage checksums match for main-qwen-c1-29-eval.

- 2026-10-24T07:50:33.788292+00:00: Progress: 32/241 core stages complete; active main-qwen-c3-29-r0-collect, 1856 generation requests, 0 training input tokens; 16.3269/96 reserved hours. Review remains waiting_for_core.

- 2026-10-24T07:52:06.126390+00:00: C1 seed29 validated at 138/240 paired success (313/480 conversations), versus seed17 186/240. Retained the result without rerun or checkpoint replacement. Both 256-step fits use corrected serialization; r0-final/r1-initial and r1-final/evaluation adapter checksums match. Exclusive failure taxonomy has 97 clarification-category failures and 54 dependency-only failures; overlapping flags are not additive. Seed29 has 80/120 familiar and 58/120 held-out paired successes. Core queue advanced to C3 seed29.

- 2026-10-24T08:05:26.401087+00:00: Extended collection audit for main-qwen-c3-29-r0-collect: 383 clean and 429 failed eligible windows; temporal severity remains noncausal.

- 2026-10-24T08:12:43.199786+00:00: Progress: 33/241 core stages complete; active main-qwen-c3-29-r0-fit, 0 generation requests, 520192 training input tokens; 16.6894/96 reserved hours. Review remains waiting_for_core.

- 2026-10-24T08:12:44.354037+00:00: Remote/local completed-stage checksums match for main-qwen-c3-29-r0-collect.

- 2026-10-24T08:23:19.662518+00:00: Progress: 34/241 core stages complete; active main-qwen-c3-29-r1-collect, 0 generation requests, 0 training input tokens; 16.8548/96 reserved hours. Review remains waiting_for_core.

- 2026-10-24T08:23:22.890267+00:00: Reconstructed main-qwen-c3-29-r0-fit: 41858 target tokens; 601 distinct windows actually contributed loss. Every optimizer step matched.

- 2026-10-24T08:25:23.304257+00:00: Remote/local completed-stage checksums match for main-qwen-c3-29-r0-fit.

- 2026-10-24T08:37:37.198736+00:00: Six-hour progress: 34/241 core stages complete, seventeen added since start. Thirteen fit audits, thirteen collection audits and eight eligible main evaluations are available. C3 seed29 refresh has 7,040 generation requests in the latest snapshot; 17.0400/96 reserved h. No review GPU calls, retries, holds, reruns or scientific changes. Completed evidence remains committed through 6447796, with new fit/collection reports awaiting the next logical results commit.

- 2026-10-24T08:48:43.240582+00:00: Extended collection audit for main-qwen-c3-29-r1-collect: 749 clean and 23 failed eligible windows; temporal severity remains noncausal.

- 2026-10-24T08:49:02.838657+00:00: Remote/local completed-stage checksums match for main-qwen-c3-29-r1-collect.

- 2026-10-24T08:57:29.967714+00:00: Progress: 35/241 core stages complete; active main-qwen-c3-29-r1-fit, 0 generation requests, 647168 training input tokens; 17.4173/96 reserved hours. Review remains waiting_for_core.

- 2026-10-24T09:06:37.736611+00:00: Progress: 36/241 core stages complete; active main-qwen-c3-29-eval, 1152 generation requests, 0 training input tokens; 17.5578/96 reserved hours. Review remains waiting_for_core.

- 2026-10-24T09:06:40.868054+00:00: Reconstructed main-qwen-c3-29-r1-fit: 42055 target tokens; 343 distinct windows actually contributed loss. Every optimizer step matched.

- 2026-10-24T09:09:22.983131+00:00: Remote/local completed-stage checksums match for main-qwen-c3-29-r1-fit.

- 2026-10-24T09:37:03.264031+00:00: Seven-hour supervision milestone: 36/241 core stages complete, nineteen added since start. Fourteen fit audits and fourteen collection audits are complete; eight main evaluations are eligible. C3 seed29 evaluation is progressing (22,208 generations in the 09:29 UTC snapshot). Latest reconciled reservation 17.9423/96 h; no review GPU use, retries, holds or scientific changes. Human ratings remain pending and original packet identities are preserved.

- 2026-10-24T09:40:36.428918+00:00: Progress: 37/241 core stages complete; active main-qwen-c4-29-r0-collect, 128 generation requests, 0 training input tokens; 18.1166/96 reserved hours. Review remains waiting_for_core.

- 2026-10-24T09:40:46.558791+00:00: Validated completed main-qwen-c3-29-eval: 181/240 paired success. Scanned all 30,720 raw turns once.

- 2026-10-24T09:41:20.781547+00:00: Remote/local completed-stage checksums match for main-qwen-c3-29-eval.

- 2026-10-24T09:42:03.686733+00:00: Completed C3 seed29 evaluation verified: 181/240 paired successes, versus C1 seed29 138/240. Matched C3−C1 +17.92 pp, exploratory family interval +12.08 to +23.75; transitions 131 both, 50 C3-only, 7 C1-only, 52 neither. This reverses the seed17 sign; three-seed conclusions remain pending. All 37 completed stages have mirror checks, all 14 fits exact exposure audits. Updated figures and author-review PDF. No reruns, exclusions, or scientific changes.

- 2026-10-24T10:01:19.208346+00:00: Progress: 38/241 core stages complete; active main-qwen-c4-29-r0-fit, 0 generation requests, 163840 training input tokens; 18.4544/96 reserved hours. Review remains waiting_for_core.

- 2026-10-24T10:01:20.264448+00:00: Extended collection audit for main-qwen-c4-29-r0-collect: 484 clean and 331 failed eligible windows; temporal severity remains noncausal.

- 2026-10-24T10:01:28.279879+00:00: Remote/local completed-stage checksums match for main-qwen-c4-29-r0-collect.

- 2026-10-24T10:19:50.923629+00:00: Progress: 39/241 core stages complete; active main-qwen-c4-29-r1-collect, 64 generation requests, 0 training input tokens; 18.7534/96 reserved hours. Review remains waiting_for_core.

- 2026-10-24T10:19:54.648233+00:00: Reconstructed main-qwen-c4-29-r0-fit: 39579 target tokens; 549 distinct windows actually contributed loss. Every optimizer step matched.

- 2026-10-24T10:20:03.661041+00:00: Remote/local completed-stage checksums match for main-qwen-c4-29-r0-fit.

- 2026-10-24T10:36:35.085887+00:00: Eight-hour supervision milestone: 39/241 stages completed, active main-qwen-c4-29-r1-collect with 8,704 generation requests. Fifteen completed fits and collections audited; all 39 completed stages mirrored and checksum-verified. Current reservation 19.0323/96 h; review remains zero. The C3−C1 sign reversal across seeds is retained. Reproducible PDF build now records exact source/template/figure hashes. No scientific changes, retries, or blockers; next actions are completing the C4 seed29 audit, final reproducibility checks, and the scheduled 12:36 UTC handoff.

- 2026-10-24T10:41:28.692718+00:00: Pre-handoff verification: 31 existing/report pytest cases and 15 supplementary/overnight unittest cases passed (46 total). Original 60-item action identities and both blank forms preserved; natural-language prose packet inputs and full-core supplementary execution gate remain pending. Author-review PDF compiled with exact build provenance. No tests use the active GPU.

- 2026-10-24T10:47:06.072620+00:00: Progress: 40/241 core stages complete; active main-qwen-c4-29-r1-fit, 0 generation requests, 0 training input tokens; 19.1999/96 reserved hours. Review remains waiting_for_core.

- 2026-10-24T10:47:07.518538+00:00: Extended collection audit for main-qwen-c4-29-r1-collect: 753 clean and 20 failed eligible windows; temporal severity remains noncausal.

- 2026-10-24T10:47:13.990541+00:00: Remote/local completed-stage checksums match for main-qwen-c4-29-r1-collect.

- 2026-10-24T11:07:38.885787+00:00: Progress: 41/241 core stages complete; active main-qwen-c4-29-eval, 0 generation requests, 0 training input tokens; 19.5324/96 reserved hours. Review remains waiting_for_core.

- 2026-10-24T11:07:42.403908+00:00: Reconstructed main-qwen-c4-29-r1-fit: 40418 target tokens; 327 distinct windows actually contributed loss. Every optimizer step matched.

- 2026-10-24T11:07:51.253322+00:00: Remote/local completed-stage checksums match for main-qwen-c4-29-r1-fit.

- 2026-10-24T11:36:30.160331+00:00: Nine-hour supervision milestone: 41/241 stages complete; main-qwen-c4-29-eval active at 20,352 generation requests. Sixteen fits and sixteen collections audited; all 41 completed stages have matching mirrors. Cumulative 20.0133/96 reserved h, review 0/2 h. All 46 relevant tests passed. The final hour will integrate any fully completed evaluation, verify freezes/mirrors, commit the paper/analysis package and record precise active-worker continuation. No faults or scientific changes.

- 2026-10-24T11:54:03.245272+00:00: Progress: 42/241 core stages complete; active main-qwen-c5-29-r0-collect, 320 generation requests, 0 training input tokens; 20.2978/96 reserved hours. Review remains waiting_for_core.

- 2026-10-24T11:54:10.684700+00:00: Validated completed main-qwen-c4-29-eval: 165/240 paired success. Scanned all 30,720 raw turns once.

- 2026-10-24T11:54:13.386389+00:00: Remote/local completed-stage checksums match for main-qwen-c4-29-eval.

- 2026-10-24T11:54:45.345713+00:00: C4 seed29 evaluation complete and validated: 165/240 paired successes, 357/480 conversation successes. Familiar-rule paired success 98/120; held-out 67/120. All commitments recalled in 463/480, canonical sources all visible in 458/480. Ten eligible complete main evaluations now audited, with 42/241 stages mirrored. C5 seed29 collection proceeds in the original order; no new matched C5 seed29 contrast exists yet. Updated figures and compiled author-review PDF.
