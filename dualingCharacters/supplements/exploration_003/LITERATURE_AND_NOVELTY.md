# Exploration precedent and a narrower contribution

Checked against primary full-text methods and author/publication records on
2026-10-24. Preprints and published versions of one work are one precedent.
“Not described” below is a bounded reading of the cited method, not proof that
no related implementation exists. No claim of being first is warranted.

| Work and verified version/status | Persistent motives and private history | Peers/shared state | Diversity and sequence objective | Cost controls | Semantic validation |
|---|---|---|---|---|---|
| Samvelyan et al., **Rainbow Teaming**, arXiv2402.16822v3,2024-12-11; NeurIPS2024 | Archive-conditioned mutations, not enduring character agendas/private relationships | Shared MAP-Elites archive; no character-to-character game described | Explicit risk/style descriptors; iterative mutation and stepping stones | AppendixG counts mutator/target/judge calls and batches | Preference judges; human agreement check on100prompt/response pairs |
| Hong et al., **Curiosity-driven Red-teaming**, arXiv2402.19464v1,2024-02-29; ICLR2024 | Learned red-team policy and novelty memory, not character motives | No persistent peer game described | RL novelty bonuses using lexical and embedding similarity | Common experimental setup; training/evaluation samples and implementation settings reported | Toxicity classifier, embedding/lexical proxies and qualitative examples; these do not validate our sequence codes |
| Wang et al., **Quality-Diversity Red-Teaming**, arXiv2506.07121v3,2026-10-21; verified as preprint | Specialized learned attackers with behavior assignments/replay | Shared behavioral replay buffer and reassignment, not interpersonal motives | Explicit risk/style space, behavior-conditioned SFT/RL, adaptive specialization | Training/resource settings and complexity discussion; not an equal-call test of our method | Model style/risk judges, including independent post-hoc style relabeling; no human validation inferred |
| Deng et al., **PersonaTeaming**, arXiv2605.05682v3,2026-09-08; acceptedUIST2026 per author record | Fixed or dynamically selected persona context; no stable private relationship history described | Persona-guided mutation workflow and human interface, not a shared planning-memory contest | Persona-conditioned RainbowPlus mutation; diversity metrics and iterative persona selection | Same seed-prompt selection; model/condition settings reported, not assumed equal total tokens | Model evaluation plus qualitative/user study with11practitioners |
| Morasso et al., **PCAP**, arXiv2605.12565v1,2026-05-12; preprint | Persona biographies, reframed goals and branch-specific conversation/search history | Independent persona beam searches; no peer communication/shared mutable task state described | Strategy cards plus persona-conditioned iterative search and pruning | Same beam/depth/branch settings; actual query counts differ substantially | Embedding/Self-BLEU diversity; reported one-human/evaluator subset agreement |

Sources for the table: [Rainbow methods§3 and appendicesE/G](https://arxiv.org/html/2402.16822v3),
[NeurIPS proceedings](https://proceedings.neurips.cc/paper_files/paper/2024/hash/8147a43d030b43a01020774ae1d3e3bb-Abstract-Conference.html),
[CRT§3–4 and appendixA](https://arxiv.org/html/2402.19464v1),
[CRT publication record](https://arxiv.org/abs/2402.19464),
[QDRT§3–4](https://arxiv.org/html/2506.07121v3),
[QDRT author publication list](https://www.lamda.nju.edu.cn/wangrj/),
[PersonaTeaming§3–7](https://arxiv.org/html/2605.05682v3),
[PersonaTeaming acceptance/version record](https://arxiv.org/abs/2605.05682),
[PCAP§4–5 and appendixB](https://arxiv.org/html/2605.12565v1).

The current QDRT revision has ten authors, including ZhiYu and YuanpengTan;
older indexed metadata lists eight. The versioned arXiv author list controls this
package's metadata. An unrelated paper citing QDRT is not evidence of QDRT's
conference acceptance. Likewise, PCAP's query totals must accompany its discovery
claims: matching search hyperparameters is not matching total query cost.

These methods already establish substantial precedent for diversity-oriented
adversarial generation, persona conditioning, archives, specialization and
history-conditioned search. PersonaTeaming and PCAP directly weaken a novelty
claim based only on giving generators biographies or different perspectives.
Rainbow and QDRT also make descriptor choice and archive coverage established
tools, not a new methodological contribution here. CRT makes an explicit
exploration objective an essential comparator to incidental diversity.

The narrower question left for this project is empirical: whether stable,
task-grounded motives plus private episode history and peer communication develop
complementary *sequential* interventions in a common mutable planning state,
at matched budgets, and whether this subsequently benefits a learner. Existing
traces can test only observable generation proxies. Jointly satisfiable slot goals
and unvalidated semantic labels prevent a stronger rivalry or exploration claim.
If the finding is fixation without broader coverage, that is an informative
limitation of this implemented character-conditioning mechanism. The current
negative/mixed defender results remain a separate finding and are not rescued by
renaming diversity as learning.

Candidate contribution, subject to human author review: a reproducible audit of
the difference between persistent objective repetition, API/reference variation,
semantic strategy development and equal-budget archive complementarity. A fresh
diversity-instructed generic control is the largest missing test, not another
personality label. The minimal design is in [NEXT_EXPERIMENT.md](NEXT_EXPERIMENT.md).

AI assistance: this comparison and interpretation were drafted by the session
assistant from inspected primary sources. The human author must review scientific
arguments, novelty boundaries and citations before any submission.
