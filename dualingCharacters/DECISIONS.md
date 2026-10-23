# Decision log

| ID | Date | Decision and basis | Status |
|---|---|---|---|
| D001 | 2026-10-23 | Use existing `dualingCharacters` on main; do not create branches or push. | Author instruction |
| D002 | 2026-10-23 | Ignore bulk data/logs/adapters; preserve compact audit manifests and mirror artifacts locally. | Author instruction |
| D003 | 2026-10-23 | Retain Qwen3-4B-Instruct-2507 as primary and Phi-4-mini-instruct as independent-family candidate, pending load/profile. | Brief default |
| D004 | 2026-10-23 | Character-generator parameters frozen; histories adapt within episodes. Only defender LoRA parameters learn. | Initial method |
| D005 | 2026-10-23 | Ground truth exists only in environment/evaluator and training-target construction; no oracle fields in policy observations. | Required invariant |
| D006 | 2026-10-23 | Remote storage is not verified persistent; local ignored mirror is the durability fallback. No base-model copy to space-limited local disk. | Observed storage |
| D007 | 2026-10-23 | Pilot data are disjoint from training/validation/locked-test families; design changes may use pilot/validation only. | Required invariant |
| D008 | 2026-10-23 | Initial BF16 profile completed 4 actual LoRA steps, but all 32 rollout responses failed the output schema (six plan entries instead of eight). Clarify schema with explicit array lengths and source-index instructions before interpreting difficulty. Preserve failed profile. | Pilot-only repair |
| D009 | 2026-10-23 | `pilot-c3-001` stopped at the 4096-token guard. Audit logging mutated a shared action object retained in private history, potentially exposing evaluator annotations and recursively inflating prompts. Invalidate that entire pilot scientifically; copy and allowlist public action history; add regression test. | Correctness repair |
| D010 | 2026-10-23 | Matched engineering profiles favor BF16: 4 steps in 10.42 s versus 16.77 s NF4, peak 16.57 versus 14.15 GiB. Select BF16 because both fit comfortably; this is hardware evidence, not method efficacy. | Measured configuration choice |
| D011 | 2026-10-23 | C3 produced zero peer actions in 96 free-choice pilot opportunities. Reserve every third common opportunity for communication (or pass), maintaining 12 total actions; A3 generates but does not deliver the message. C4 may address Jekyll. Audit actual peer uptake before claims about relationships. | Pilot mechanism repair |
| D012 | 2026-10-23 | Enrich domain descriptions/topics and state that randomized client-specific dependency mappings are authoritative. Exclude IDs/split names from structural fingerprints. This improves pilot validity without reading locked outcomes; domain generality remains limited. | Pilot benchmark revision |
| D013 | 2026-10-23 | vLLM 0.10.2 successfully profiles 64 distinct public pilot prompts in 4.54 s, versus 26.38 s for Transformers' earlier repeated-prompt batch. These are different prompt sets, so do not call this a controlled speedup estimate; use realistic rollout profiling for allocation. | Measured feasibility |
| D014 | 2026-10-23 | Initial pilots show malformed JSON and invalid character slot/value pairs. Test a shared public JSON schema for all base/trained policies and characters, preventing syntax-only learning from masquerading as recovery. Schema constrains interface legality, never task truth. Re-audit before confirmation. | Pilot nuisance-control repair |
| D015 | 2026-10-23 | Fixed-state recovery will erase the site value/reference in an actually executed base-policy observation at turn 32. All methods receive identical sources and damaged memory; four attempts include unrecovered cases. Construction never reads oracle labels. This tests a missing-memory fault, not every deceptive-memory mechanism. | Proposed secondary protocol |
| D016 | 2026-10-23 | Use a larger retrieval reference (16 retrieved + 8 recent messages, 8192 input-token cap) on a preselected subset. This is not full-history evaluation. Original primary scaffold remains 8 + 4 and 4096. | Proposed compression diagnostic |
| D017 | 2026-10-23 | Initial external validation uses the official LongMemEval rubric with an independent small model family as an adapted judge, if calibration is adequate; official GPT-4o/70B scoring is unavailable without new resources. Report rubric/engine adaptation and pending human validation, never official comparable benchmark scores. | Resource-constrained adaptation |

Proposed interpretations and implementation decisions are reviewable by the author.
This log does not imply human endorsement of AI-generated scientific arguments.
