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

Proposed interpretations and implementation decisions are reviewable by the author.
This log does not imply human endorsement of AI-generated scientific arguments.
