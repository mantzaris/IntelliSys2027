# Primary-source novelty audit

Checked 2026-10-23. This is a scoped search, not proof of absence. No “first” claim.
Y = present; N = not part of the method; P = partial/related; — = not applicable.
Columns describe the cited method, not every experiment in the paper.

| Work; verified status | Persistent motives | Private history | Peer interaction | Deliberate interference | Shared state | Learner updates | Antagonists removed for evaluation |
|---|---:|---:|---:|---:|---:|---:|---:|
| [Collu et al., Dr. Jekyll and Mr. Hyde, v7](https://arxiv.org/html/2312.03853v7); ITASEC/SERICS 2026, CEUR 4198 paper 35 | P (biography) | P (roleplay context) | N | Y | N | N | N |
| [Li et al., Persona-Invariant Alignment, v1](https://arxiv.org/html/2605.01899v1); arXiv preprint, 2026 | P (persona lineage) | P (attack credit history) | N (evolution is not peer conversation) | Y | N | Y (DPO/SFT/consistency) | P (benign/general capability tests) |
| [Dulberg et al., Multiple selves](https://pmc.ncbi.nlm.nih.gov/articles/PMC10334746/); PNAS 120(28), e2221180120, 2023 | Y (distinct needs) | P (learned values) | P (action-value arbitration) | N (no deceptive dialogue) | Y (environment/body) | Y (DQN) | N |
| [Wei et al., Self-play SWE-RL, v3](https://arxiv.org/html/2512.18552v3); accepted ICML 2026 per version metadata | P (inject/repair objectives) | P (iterative curriculum) | P (task artifact) | Y (bug insertion) | Y (repository) | Y (RL) | Y (issue-solving benchmarks) |
| [Laban et al., Lost in Multi-Turn Conversation, v1](https://arxiv.org/html/2505.06120v1); arXiv preprint, 2025 | N | P (conversation) | N | N | Y | N | — |
| [Kruthof, Models Recall What They Violate, v2](https://arxiv.org/html/2604.28031v2); arXiv preprint, 2026 | N | P (conversation) | P (auditing) | P (pressure) | Y | N | — |
| [Wu et al., LongMemEval, v2](https://arxiv.org/html/2410.10813v2); ICLR 2025 | N | Y (user sessions) | N | N | Y (memory pipeline) | N | — |
| [Mooney et al., Behavioral Coherence, v3](https://arxiv.org/html/2509.03736v3); arXiv preprint, revised 2026-10-11 | P (elicited profiles) | P (conversation) | Y | N (not required) | P | N | N |
| [Zeng and Rudzicz, Voluntary Collusion, v1](https://arxiv.org/html/2605.27593v1); arXiv preprint, 2026 | Y (game objectives) | Y | Y (secret tools) | Y | Y (game) | N | N |
| [Fauchard et al., Even More Deception, v1](https://arxiv.org/html/2607.26120v1); arXiv preprint, 2026 | Y (role versus objective) | Y | Y | Y | Y (Werewolf) | N | N |
| [Hashmi et al., AdvSim2Real, v1](https://arxiv.org/html/2610.08773v1); arXiv preprint, 2026-10-06 | P (adversarial objective) | Y (attack replay) | P (curriculum/executor/adversary) | Y | Y (web world) | Y | Y (clean capability/browser) |
| [Pan et al., MemForm, v1](https://arxiv.org/html/2610.14431v1); arXiv preprint, 2026-10-10 | N | Y (experience memory) | N | Y | Y | N (fixed update protocol, not parameter learning) | P (downstream memory use) |
| Present study, intended design (not a result) | Y | Y | Y | Y | Y | Y (defender LoRA) | Y (primary endpoint) |

## Closest methods and implications

**Persona-Invariant Alignment.** Read method sections 4.1–4.2 and experimental
setup. It evolves personas through mutation/crossover, propagates attack credit
through a lineage graph, and updates a defender with a combined objective. Thus
persona-driven adversarial data and actual defender learning are already established
methods. This study must isolate persistent competing agendas, episode relationships,
and conversational-state transfer; persona names or an extra agent are insufficient.

**Self-play SWE-RL.** Read §2 and the matched human-data comparison. The same policy
injects and repairs bugs, with executable artifacts and iterative refresh. Training
on verified self-generated damage followed by clean transfer is not new by itself.
The relevant distinction here is motive-dependent interference in conversational
memory and the causal role of persistence/interaction.

**AdvSim2Real.** Read §3–4 and evaluation qualifications. It co-trains curriculum,
executor and injection adversary inside a frozen simulator and evaluates clean and
unseen-attack behavior. Its reported three evaluation seeds are not independent
training replicates. This is a particularly close counterexample to broad claims
that adversarial self-play has not improved ordinary task capability. Our narrower
question concerns stable mixed motives versus direct disruption at matched budgets.

**Multiple selves.** Read environment description and Materials and Methods. Distinct
homeostatic modules learn separate Q functions whose action values are summed.
This supports investigating competition among objectives; it does not establish
deceptive language characters or transferable conversation-repair training.

**Collusion and objective misalignment.** Read strategic environments, secret-tool
protocol and objective manipulation. These demonstrate why observable communication
and coordinated actions, rather than correlated errors, are needed for a coalition
claim. Role and goal must be separated, motivating explicit-motive and alias controls.
They do not show our proposed recovery-learning effect.

**MemForm.** Read threat model and formation interfaces. Memory poisoning already
includes content, evidence, scope, selection and consolidation order. A bounded
memory-write interface is not a new vulnerability. Use unfamiliar corruption
interfaces as diagnostics, and separate poisoning from a learned recovery advantage.

**Evaluation foundations.** Lost-in-conversation studies sharded underspecified
tasks and unreliability; DriftBench separates restatement from behavioral adherence;
LongMemEval tests updates, temporal reasoning and abstention with long session histories.
Their task protocols are distinct. Behavioral Coherence cautions against assuming
that a verbal profile implies stable behavior. Hence behavior auditing and separate
recall/adherence metrics are central, not decorative additions.

## Search record and claim boundary

Searches covered adversarial memory training, persona populations, mixed-motive
self-play, collusion, persistent adversarial curricula and long-conversation recovery.
Additional leads (not yet fully audited) include [AgentPoison](https://arxiv.org/abs/2407.12784),
[MemoryGraft](https://arxiv.org/abs/2512.16962), and
[persistent adversarial conversation evaluation](https://arxiv.org/abs/2609.38357).
Do not cite unverified details of these leads as findings.

Already established: persona-conditioned attacks; adversarial parameter learning;
distinct-objective modules; memory poisoning; strategic peer coordination; multi-turn
drift; and some clean transfer from adversarial/self-play training.

Unverified hypothesis here: persistent, individually motivated interacting opponents
provide better recovery-training experience than equally equipped adaptive generic
adversaries, after the opponents are removed. The narrative-profile hypothesis is
strictly narrower and requires A1. No results yet establish either claim.
