# Dataset card: authored context/composition variation

The 16 family instances cross two contexts with eight patterns. Each has two minimally different worlds and 32 user turns. The familiar six-field plan and options are preserved. Context-specific public dependency maps use new string values, with the same deterministic dependency functions. No hidden authority, delegated approval rule, or new ontology is introduced.

One user turn is one scripted user message followed by one generated structured answer. Twelve internal action opportunities are additional model calls. The full requested tier would contain 384 conversations; the timing-admitted reduced tier contains 192, with two fixed backbones and rollout seed 17. There are 16 independent family units, not 192 independent tasks. Worlds and methods share scripts; their later generated histories differ.

`tables/expectations.csv` provides every world's operative instruction, decisive field, before/after values, source IDs, ambiguity and untouched fields. `inputs/scenarios.json` contains the entire time-indexed oracle and script. These analyst annotations never enter policy prompts; the original fixed retriever sees messages, public catalog and policy memory only. Earlier sources may become unavailable through ordinary retrieval competition; visible source IDs are retained.

## What is new, and what is shared

| Pattern | Existing precedent | Added composition |
|---|---|---|
| Stale approval | Superseded decisions and resurfacing suggestions | Exact earlier approval quoted after a newer approval, paired with a live reinstatement |
| Quoted approval | Hypothetical wording | Same approval-like sentence inside a draft versus operative user instruction |
| Conditional permission | Conditional downstream plan dependency | Explicitly stated authorization prerequisite and visible satisfied/unsatisfied fact |
| Narrow revision | Multiple fields and hypothetical alternatives | Approval of one field beside an expressly unapproved second-field alternative |
| Legitimate reversal | Single approved update | A→B→A sequence paired with discussion of returning to A |
| Incorrect correction | Misleading character recollection | Quoted correction supplied in the user script, disclaimed versus authorized |
| Ambiguity/resolution | Unresolved final clarification | Reopening, asymmetric early resolution, and explicit later settlement in both worlds |
| Persuasive rationale | Generic unapproved suggestion | Quoted urgency/consensus/prior-approval argument paired with actual authorization |

Exact source transcripts and instantiated Event sequences do not overlap the original pilot/train/validation/test/natural splits at horizons 16/32/64/128 (`inputs/OVERLAP.json`). This is not proof of semantic disjointness. Community seed-bank and remote-instrument terminology was checked in the existing supplement generator sources; the originally suggested museum context was avoided because earlier intent cases already used museum material.

The background discussion rotates eight practical topics across outline/check/summarize/refine phases. It is authored synthetic task work with explicit nonrevision wording, not sampled human conversations. This may make authority clearer than in natural dialogue. All values, fields and dependency rules remain a small shared schema; new context names alone cannot establish broad transfer.

Pattern 7's non-authorizing world is unresolved from turn 10 until turn 20, while the other resolves at 12. Both are settled at the final turn. This deliberately separates targeted uncertainty from eventual execution; final success alone cannot show that earlier uncertainty was handled correctly.
