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

Proposed interpretations and implementation decisions are reviewable by the author.
This log does not imply human endorsement of AI-generated scientific arguments.
