# Same-slot compatibility extension — executable, disabled, unscheduled

This is the executable continuation of [dialogue005's proposal](../../dialogue_interpretation_005/NEXT_EXPERIMENT.md), not a duplicate of review001. No inference ran. Review001's contested-slot and delivery diagnostics are still the first mechanism experiments, owned by its existing coordinator. The core remains active, so admission fails. There is no new waiter, worker, reservation or queue change.

DESIGN.json binds16 new family IDs dialogue005-compat-0000…0015, four per domain; both authorized/hypothetical scripts; compatible/incompatible preference arms;32 turns;12 opportunities;64 conversations;2,816 scheduled character/answerer calls. No engineering model calls are planned. Synthetic test-backend output is plumbing only and stays in temporary test directories.

The public catalog and background schedule reuse review001's frozen generator. Decisive statements are serialized under the new IDs. Scripts are identical across arms and paired worlds differ only at turn16 authorization. The two actors share a slot and retain biographies, utility text, history6, routing and tools. Eight families start with each actor. Each actor initially aligns with the user in eight families per arm. Joint alignment differs intrinsically: compatible8 both/8 neither; incompatible8 each actor alone. Slot counts are3/3/3/3/2/2. Owned option identities rotate through a hash-shuffled option cycle per slot; assignments are fixed before inference. Hyde's option remains the same across arms within family; Rival's option produces the compatibility manipulation. Preferences remain fixed through genuine user updates.

Pinned shared untrained Qwen revision cdbee75f17c01a7cc42f958dc650907174af0554; no adapter or training. Inference matches review001: BF16, vLLM0.10.2, structured decoding, batch64,4,096 input tokens,256 answer tokens,128 character tokens. Answer decoding is greedy; characters use temperature0.7/top-p0.9, with the existing cumulative-call seed rule. Eight lexical sources **plus** four recent sources are deduplicated for the answerer. The prior005 proposal said “including”; this executable specification clarifies the actual unchanged memory.observation implementation. Character retrieval remains eight lexical sources. This clarification changes no prior scientific file or result.

## CPU-only check

From dualingCharacters:

```bash
PYTHONPATH=src:. python -m supplements.evidence_validation_006.compatibility_design
```

This cannot instantiate an inference backend. It verifies family/world/domain coverage, balanced actor order/alignment, serialized scripts, dynamic oracle changes and the2,816-call bound. It makes zero model calls and reports no experimental scores. The focused plumbing test uses a clearly synthetic pass/constant-answer backend in a temporary directory; its output is never a research result.

## Scientific outcomes and stopping

Primary observable endpoint: the distribution of the recipient's first following action after allocated communication opportunities, with explicit no-message, invalid/unavailable route, unavailable observation and missing-follow-up statuses. Keep all allocated opportunities in the primary denominator; conditional delivered-message tables are secondary. Record the prior position, actual text, visibility, following statement and answerer decision. Fixed human event readings assess acknowledgment, source challenge, new position, continuation or another response. Raw same-value matching is mechanically easier with compatibility and cannot establish responsiveness.

Report each arm, both worlds retained inside family, paired family differences with10,000 family bootstrap draws, fixed seed600017. No action-iid test, no seed-population claim, no new training. Semantic judgments remain pending until two independent raters provide actual labels. Different versus similar outcomes are equally admissible. Causal delivery effects remain review001's intervention, not this compatibility contrast.

Complete both arms/worlds for all16 families. A failed/deadline-interrupted run remains an incomplete fixed grid, with original partial traces and costs preserved. No automatic retry, favorable sample substitution or scope reduction. Both arm order and family order are fixed in DESIGN.json. Future analyses must distinguish this newly controlled sample from the older48-episode observational atlas.

## Admission and ownership

ADMISSION_DISABLED.json is deliberately false. The default foreground entry exits before upload, model loading or reservation:

```bash
PYTHONPATH=src:. python -m supplements.evidence_validation_006.compatibility_owner
```

A later authorized continuation must be undertaken by the existing campaign owner at a safe idle boundary. It must reconcile **all** core statuses, the review coordinator's completed allocation (including the conflict diagnostic), remaining obligations, current reserved use, mirroring and the new session deadline. No worker may preempt an active job or change optional priorities. The current session's deadline is10:53:27 UTC, with useful-work cutoff10:08:27 UTC on2026-10-26; this disabled specification does not authorize unattended execution afterward.

Only after those gates genuinely hold, the owner may create a new versioned operational admission file (preserving this disabled original) with enabled=true, its real authorization/dispatch ID, the authorized session deadline/cutoff, reconciled remaining-obligation seconds, and a conservative7,200-second total bound. This first implementation admits the entire unprofiled grid only if the full two-hour bound fits; it does not invent a measured timing estimate. It retains1,800 seconds project contingency. Earlier costs under budget identity dialogue005-compatibility **or any dialogue005-compat run prefix** count cumulatively. Renaming does not reset the allowance. Any earlier nonzero use prevents this conservative full-bound admission without a separately reviewed timing amendment; no silent retry is supplied.

Use the existing connection environment without printing credentials:

```bash
PYTHONPATH=src:. python -m supplements.evidence_validation_006.compatibility_owner \
  --admission /path/to/actually_authorized_admission.json
```

The foreground integration acquires the existing local campaign.lock nonblockingly, verifies frozen dependencies, uploads only the new compatibility namespace files, uses the existing run_and_mirror path, and pulls artifacts with the established sync script. On the remote side, a separate nonblocking dispatch lock prevents duplicate supervisors and RunLedger acquires the existing gpu.lock and checks device ownership. A hard timeout terminates only the newly owned worker process group, retains a margin within the2-hour bound, and charges the tail after the last heartbeat. Partial/completed run directories are never restarted automatically. All source hashes, admission, versions and model revision are recorded. The GPU-dependent integration has not been exercised in this stage; CPU checks do not prove runtime/model compatibility.

Expected artifacts: artifacts/runs/dialogue005-compat-17-v1/{compatible,incompatible}.jsonl, corresponding *_characters.jsonl and *_summary.json, status.json, completion.json, source snapshot, ledger and supervisor state. The existing owner mirrors them locally during and after the foreground operation. No only-ephemeral copy is intended. If interrupted, preserve these files, inspect the owned process/status and reconcile time before any separately authorized recovery; do not launch a duplicate. Rendering actual new outputs through the atlas is pending execution and its recorded schema verification, not a completed deliverable disguised as a result.
