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
