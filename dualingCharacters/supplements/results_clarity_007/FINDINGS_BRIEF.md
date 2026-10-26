# What changes when motives and biographies are introduced?

**Findings brief · exploratory clarification 007 · human semantic validation pending.** This implemented system uses a shared frozen Qwen backbone with separate actor contexts. C3 has two generic adversaries; C5 has two biography-plus-motive characters; A1 keeps the same motives without biographies. One answerer is additional in each condition.

**Population.** Common-base round-zero collections: 150 unique training families ×2 paired worlds ×3 generator seeds (17/29/43) =900 episodes and 10,800 allocated actor opportunities per condition. Each episode has 16 user/answerer turns and 12 actor opportunities. The same 150 families recur across seeds. This is not900 independent families or three independently trained character policies. Later refreshed collections and trained-answerer tests are separate.

## 1. The intervention channels differ reproducibly

| Condition | Direct edit | Recollect | Propose |
|---|---:|---:|---:|
| C3 | 5,408/10,800 (50.07%) | 828/10,800 (7.67%) | 969/10,800 (8.97%) |
| C5 | 477/10,800 (4.42%) | 4,618/10,800 (42.76%) | 1,930/10,800 (17.87%) |
| A1 | 938/10,800 (8.69%) | 1,397/10,800 (12.94%) | 4,830/10,800 (44.72%) |

All opportunities are retained; peer/pass/malformed/invalid channels complete the distribution in Figure 1. These are **API labels, not false-memory or deception categories**. C5−C3 edit frequency is -45.66 pp [95% pointwise interval -48.20, -43.06]; recollect frequency is +35.09 pp [95% pointwise interval +31.64, +38.67]. C5−A1 recollect frequency is +29.82 pp [95% pointwise interval +27.08, +32.66]. Narrative removal shifts which note API is used; it does not by itself establish a difference in what the claim means.

Seed-level numerators (each denominator 3,600):

| Condition | Edit 17/29/43 | Recollect 17/29/43 | Propose 17/29/43 |
|---|---:|---:|---:|
| C3 | 1809/1755/1844 | 272/298/258 | 322/349/298 |
| C5 | 170/177/130 | 1472/1511/1635 | 691/672/567 |
| A1 | 329/292/317 | 431/463/503 | 1630/1631/1569 |

The original 10,000-draw paired family/seed bootstrap preserves worlds inside families and uses seed 400041. Intervals describe mean paired family-rate differences, not independent actions. Only three generator seeds limit seed-generalization; no equivalence or new significance test is claimed.

## 2. Typed preferences persist in both character and motive-only conditions

| Condition | Repeated eligible direct-goal pairs | Immediate state changes / all opportunities |
|---|---:|---:|
| C3 | 3,623/5,400 (67.09%) | 3,830/10,800 (35.46%) |
| C5 | 4,831/5,224 (92.48%) | 286/10,800 (2.65%) |
| A1 | 5,093/5,364 (94.95%) | 562/10,800 (5.20%) |

Repetition compares consecutive eligible edit/recollect/propose actions **within actor and episode**, skipping non-direct opportunities according to the frozen metric. It measures the same typed slot/value, not coherent argument development. C5−C3 mean family-rate repetition is +25.39 pp [95% pointwise interval +22.22, +28.58]; C5−A1 is -2.48 pp [95% pointwise interval -4.30, -0.69]. Pooled fractions above have unequal eligible-pair denominators and need not equal differences between family means.

Fixed owned-option prompts directly encourage persistence. Fewer immediate state changes in C5/A1 are consistent with their use of notes rather than edits; the comparison is not a counterfactual measure of harmful influence. Notes may affect later answers, or have no observed effect. Per-seed repetition/state counts and white-dot seed values appear in Table MECHANICAL_COUNTS and Figure 3.

## 3. API, proposition, delivery and response are distinct

In A1 case DI5-e743bcb1a6, the exact “I propose shifting the venue to Garden…” sentence appears as propose at turn 7 and recollect at turn 10; both append notes, omitting the separate numeric source. In C5 case DI5-a 4c89ffad4, Tuesday is authorized, a peer challenges Saturday, and the recipient repeats “The event day should be Saturday…” while the answerer retains Tuesday. Earlier turn 9 language explicitly invokes user-approved constraints. The later “should” sentence alone need not claim approval. Figure 2 and the reader edition show complete statements and locators.

These are selected illustrations, not semantic prevalence estimates. The fixed review contains64 component-directed events and 8 answerer-directed notes, not72 peer exchanges. All72 retain their IDs; independent human assessment is pending. The corrected rubric separates incoming propositions, recipient behavior, citation support, visibility and dimension missingness.

## Context and remaining discrimination

Antagonist-free Qwen paired success at 64 turns (240 test families per seed): C1=186/138/183, C3=177/181/190, C5=168/180/172 for training seeds 17/29/43. The untrained reference is 67/240 once. C5 trails C3 at each matched seed; behavioral differences do not establish learning benefit. The earlier eight-family descriptor-breadth pilot was inconclusive, not a demonstration of broader exploration.

The strongest next validation is two independent assessments of the **same 72 fixed events** under v2, resolving preference versus authorization and actual recipient response with missingness-aware agreement. Preference-compatibility and delivery interventions remain separate pending mechanism tests. Correct final plans, matching later actions and visible messages do not independently establish persuasion, rivalry or causal learning mechanisms.

Sources: frozen005 FAMILY_NUMERATORS/REPRODUCED_CONTRASTS,004 CHANNELS and 006 PERFORMANCE_CONTEXT, with hashes and 72 reproduced estimates in reports/NUMERIC_VERIFICATION.json. Six purposive reader case groups link to the unchanged 48-episode archive. No new inference or human labels were added.
