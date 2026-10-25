# Behavioral characterization 004 — session handoff

**Outcome:** reproducible behavioral differences, with mixed and unresolved mechanisms. This descriptive investigation does not require a benefit and does not change the original negative/mixed efficacy findings or the inconclusive exploration audit.

## Session and protection

Start: **2026-10-25T02:36:18+00:00 UTC** / **2026-10-24T22:36:18-04:00 America/New_York**.
Report/end of useful work: **2026-10-25T03:25:23.626732+00:00 UTC** / **2026-10-24T23:25:23.626732-04:00 America/New_York**.
Actual elapsed through this report: **49.1 minutes (0.818 hours)**.
Single absolute deadline: **2026-10-25T07:36:18+00:00** / **2026-10-25T03:36:18-04:00**.
The reserved final-verification cutoff was 2026-10-25T06:51:18+00:00; verification is already complete, and the local commit follows within the same ceiling.

The scoped CPU analysis, source review, figures, reproducibility and interpretation package finished early. Missing human ratings and controlled model experiments cannot be supplied under this stage's CPU-only authorization. No artificial waiting, new GPU worker, coordinator or background waiter was added. The existing campaign continues independently.

Starting commit: `f36e20bdebd8e786e071144d7e986317dcc8e1f9` on **main**, initially clean. Only `dualingCharacters/supplements/behavior_characterization_004/` belongs to this commit. The final commit is the result of:

```bash
git log -1 --format=%H -- dualingCharacters/supplements/behavior_characterization_004/SESSION_REPORT.md
```

All **127 prior scientific files** (58 core, 21 review, 34 intent, 14 exploration) remain unchanged. The new original 17-file scientific freeze remains unchanged; seven separately hashed amendment files preserve explicit corrections/qualifications. Amendment 001 handles compressed action-file packaging, 002 fixes a legacy C1 exposure-path join, 003 marks random-control owned-goal fields inapplicable and clarifies the API-available denominator. None changes primary C3/C5/A1 metrics, original experiments or exclusions. No core correctness defect, infrastructure retry, queue change, checkpoint substitution, push, publication, submission, external contact or artifact deletion occurred.

## Evidence and completed work

Evidence cutoff: **2026-10-25T02:43:09.210881+00:00**. The snapshot includes 31 completed eligible collection/mechanism runs, 39 condition cells and 16 completed secondary evaluations. Principal round-zero C3/C5/A1 comparisons use 150 paired families and three matched seeds with the same untrained Qwen defender. The eight-family mechanism pilot and refreshed 32-turn collections are separate. The older malformed-serialization C1 runs remain excluded. A1 seed 43 evaluation was incomplete at cutoff; its later completion is operational news only and is not silently added to these estimates.

The package adds channel-to-state/output accounting, actor-local persistence and fixed event windows, evidence authority/visibility, and actual inbox/recipient reconstruction. It checks 87,936 allocated action records; 192 random-control records have no character observation and are explicitly missing for inbox validation. All available inbox reconstructions agree. Every primary point estimate was independently recovered from family tables, with paired-world dependence retained.

Four principal observations:

1. **Channels differ reproducibly.** C3 uses direct edits on 50.07% of opportunities versus 4.42% for C5. C5−C3 is −45.66 percentage points, pointwise 95% family/seed interval [−48.20,−43.06]. C5 uses recollections on 42.76% versus 7.67% for C3. Removing biographies shifts A1 toward proposals (44.72%); C5−A1 recollection is +29.82 pp [+27.08,+32.66]. All three round-zero seeds reproduce these directions; the pilot and refreshed observational collections agree.
2. **Goals persist without proving strategy development.** Consecutive typed-goal repetition is 67.09% C3, 92.48% C5 and 94.95% A1. Fixed owned options often persist after legitimate revisions away from them, as the utility instructions encourage. API/text changes are separated from substantive claim changes; role timing and short censored runs limit interpretation.
3. **Evidence access is descriptively similar in some respects.** Unavailable references are about 11.3% in all three principal conditions; C5−C3 is +0.08 pp [−1.17,+1.35], not equivalence. Typed support, canonical mismatch, assistant authority and actual claim meaning remain distinct. No automatic deception label is warranted.
4. **Delivery works; influence remains unresolved.** C5 has 3,183 observed component messages out of 3,234 sent; 51 lack a later recipient observation. Only 39/3,044 observed typed messages have a next-opportunity typed match. Prior-recipient references and sampled text show why a match can predate a message and a correction can occur across different slots. Compatible owned slots do not create necessary interpersonal conflict.

These numbers regenerate from the saved tables; [BEHAVIORAL_CHARACTERIZATION.md](BEHAVIORAL_CHARACTERIZATION.md) supplies full denominators, intervals, per-seed exceptions, availability sensitivities and qualifications. [CLAIM_TO_EVIDENCE.md](CLAIM_TO_EVIDENCE.md) distinguishes observations, associations, controlled text-removal effects and untested hypotheses.

The secondary Qwen paired successes remain C5=168/180/172 versus C3=177/181/190 and C1=186/138/183 at seeds 17/29/43 (240 families each). C5 is below C3 at every completed seed and above clean training only at 29. These descriptive behavioral findings do not establish task superiority, broader exploration, robustness or transfer beyond the shared synthetic schema.

Existing supervision and defender audits were reused with source validation: 24 actual-loss-exposure fits, six genuinely newer fits without reconstruction, and the prior clarification/source audit tables. No expensive token replay was repeated and no causal channel→curriculum→learning claim is made.

## Review and reproducibility

- [Four PDF/SVG figures with PNG previews](reports/figures/CAPTIONS.md); [compact action-chain table](reports/ACTION_CHAIN.csv), [persistence](reports/PERSISTENCE.csv), [context](reports/CONTEXT.csv), [evidence](reports/EVIDENCE.csv), [peer responses](reports/PEER_RESPONSE.csv).
- [Neutral manuscript section](MANUSCRIPT_SECTION.md), [primary-source comparison](RELATED_WORK.md), [one unscheduled discriminating experiment](NEXT_EXPERIMENT.md).
- [Evidence audit](DATA_AUDIT.json), [scientific manifest](SCIENTIFIC_MANIFEST.json), [package verification](reports/PACKAGE_VERIFICATION.json), [reproduction check](reports/REPRODUCTION_CHECK.json).
- Existing 56-item exploration packet and both presentation versions are byte-preserved. New 24-item matched sequence addendum: `artifacts/behavior_characterization_004/human_review/reviewer/PACKET.html`; two blank forms, separate private mapping. All human ratings remain pending. [Six AI-assisted readings](AI_ASSISTED_READINGS.md) are deterministic, unvalidated illustrations, not human annotations or prevalence estimates. The older 60-action packet and existing materials for the pending 120-output prose review were not rewritten.

**95 relevant tests pass.** An initial pytest collection invocation lacked the project-root import path; the corrected documented invocation passed without source changes. One-command reproduction regenerated **42 numerical/figure outputs with identical bytes**. Raw traces, adapters, caches, detailed regenerable distributions and review payloads remain outside Git. Compact reports, code, manifests and figures are versioned.

From `dualingCharacters`:

```bash
PYTHONPATH=src:. .venv/bin/python -m supplements.behavior_characterization_004.reproduce
PYTHONPATH=src:. .venv/bin/python -m supplements.behavior_characterization_004.verify_package
PYTHONPATH=src:. .venv/bin/python -m pytest -q tests supplements/review_001/test_review.py supplements/long_horizon_intent_002/test_intent.py supplements/exploration_003/test_exploration.py supplements/behavior_characterization_004/test_behavior.py supplements/behavior_characterization_004/test_compatibility.py
PCC_REPORT_OUTPUT="$PWD/supplements/behavior_characterization_004/reports" PCC_REPORT_CACHE="$PWD/artifacts/behavior_characterization_004" PYTHONPATH=src:. .venv/bin/python -m analysis.overnight.monitor
```

Existing environment: Python 3.12.14, NumPy 2.2.6, Matplotlib 3.10.6, pytest 8.4.2. Nothing was installed. Reproduction consumes CPU only and fails on changed/missing locked inputs instead of substituting newer runs.

## Core status and resource accounting

Latest read-only snapshot: **2026-10-25T03:22:41.579867+00:00**. Core advanced from 75 to **77/241 stages**. Active: **`main-phi-c1-17-r0-collect`**, **4,228 model calls** recorded. The unchanged queue has entered the independent Phi family. Later completions do not enter the locked behavioral analysis.

Hardware snapshot: NVIDIA RTX 6000 Ada Generation, 49140 MiB, 40108 MiB, 94 %. Worker PID **794657**, GPU engine **795127, VLLM::EngineCore**. Original local core controller **787315** and review coordinator **1291869** remain owners. Mirror status age **54.6s**. No genuine infrastructure failure was observed.

Reserved study time at first snapshot: **34.5847h**. Increase during observed session snapshots: **0.7400h**, entirely the pre-existing campaign. Reconciled cumulative total: **35.3246/96h**; remaining **60.6754h**, or **60.1754h** after the mandatory 30-minute contingency. Review001 remains **0/2h**; intent002 **0/2h**, disabled; behavior004 **0 new GPU hours, 0 inference/training/model-judge calls, 0 reservations**. Failed/historical attempts remain in the original ledger.

Core forecast: expected **82.60h**, conservative **88.65h** total reserved. This is a timing projection, not permission to alter samples or spend beyond 96h. Container elapsed time is **38.320h**; completed-run sampled GPU-busy time **32.543h**. Neither is established billed pod lifetime. Rate and actual dollar cost are unknown.

Storage: local **22.87GiB**, remote **18.81GiB** free. The completed-Qwen-fit unique-inode projection for 42 remaining fits is **12.95GiB**, excluding traces, temporary writes and other-family size changes. Hard-linked final/latest weights are counted once. This is limited unmodeled headroom, not a guarantee; no deletion or remote bulk analysis occurred.

Next original jobs: `main-phi-c1-17-r0-fit`, `main-phi-c1-17-r1-collect`, `main-phi-c1-17-r1-fit`. The existing core may continue after this handoff under its locks and 96-hour gate. Review001 waits for the full core; intent002 is still disabled. This session leaves no new waiter or discretionary GPU work.

## Exact recovery boundary

Ownership/locks: local `artifacts/campaign.lock`, remote `/workspace/dualingCharacters/artifacts/gpu.lock`; review `artifacts/review_001/controller.lock`. State/logs: `artifacts/campaign_state.json`, `artifacts/campaign_controller.log`, `artifacts/campaign_configs/<run_id>.log`, and remote `/workspace/dualingCharacters/artifacts/runs/<run_id>/status.json`. Review state is `artifacts/review_001/controller_state.json`; disabled intent state is `artifacts/long_horizon_intent_002/activation.json`.

Use the established read-only monitor first. A dropped connection or long generation is not proof of a dead worker. Only after proving the original controller/GPU operation stopped, preserve partial outputs and use the existing `artifacts/campaign_resume.json` alias/checkpoint procedure, at most two retries for the same infrastructure fault. The existing launch command is `PYTHONPATH=src .venv/bin/python -u -m pcc.campaign` with its established SSH environment; do **not** run it while the current owner remains healthy. Full procedure: [RECOVERY.md](../../reports/overnight_20261024T023622Z/RECOVERY.md). Completed evaluations are never rerun for another score.

## Direct scientific answers

1. **Reliably different:** channel use and typed-goal repetition across the three common-defender seeds; fewer direct state writes under C5; biography removal shifts recollections toward proposals.
2. **Similar without equivalence:** unavailable-reference rates, some C5/A1 support patterns and prior descriptor coverage. Intervals crossing zero do not prove sameness.
3. **Expected from instructions:** stable preferred-option pursuit, generic adversarial disruption and some profile-language priming. Exact channel distributions were measured rather than specified.
4. **Contextual/implementation explanations:** fixed role timing, reserved-slot routing, compatible owned slots, bounded history, source loss, truncation and rejected actions; later defenders differ.
5. **Components separately:** biography-string removal has a narrow controlled channel effect. Motive-only A1 retains high persistence. History and communication mechanisms remain small-pilot/validity-qualified; count is not isolated from role composition/routing.
6. **Not inferred:** hidden intention, psychological personality, semantic strategy sophistication, causal peer influence, coalitions, co-evolution, optimized equilibria, improved average performance or broad real-world transfer.
7. **Most clarifying next evidence:** the already prepared review001 compatible/incompatible-goal diagnostic. For a clean compatibility interpretation beyond its shared-slot change, NEXT_EXPERIMENT.md specifies one unscheduled same-slot compatible-versus-incompatible control. Human reading of the preserved/additional packets is still needed for semantic claims.

Author review should assess the four bounded findings, arrange independent semantic ratings when available, and decide whether the existing mechanism diagnostic sufficiently resolves the shared-slot compatibility question. No routine approval is needed to keep the existing authorized core running.
