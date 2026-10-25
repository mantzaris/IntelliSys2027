# Behavioral Effects of Persistent Motive-Conditioned Components in Conversational Systems

This is an exploratory behavioral characterization, requested after mixed/negative defender results and an inconclusive exploration audit. It does not replace the original research question or require a benefit. The evidence supports reproducible differences in this implementation's action channels and goal persistence, together with limits on what typed peer and evidence metrics establish.

## Evidence and scope

The cutoff is 2026-10-25T02:43:09.210881+00:00. All 39 eligible collection cells were analyzed: main round zero, refreshed collections and the final mechanism pilot remain separate. The principal comparison uses the same untrained Qwen3-4B-Instruct-2507 defender, 150 paired training families, 16 turns, seeds 17/29/43 and 12 intervention opportunities per world. These are 150 unique families repeated across seeds, not 450 independent families. There are 10,800 allocated opportunities per main condition across seeds. Character weights are frozen; seed changes assignments and sampling, not independently learned character policies. Private histories reset between independent episodes; persistence here means within an episode. The public user scripts are fixed, with a shared six-slot schema.

C3 has two generic adversaries; C5 has Hyde and Rival plus the answerer; A1 removes biography text while keeping their explicit motives, utilities and tools. All three share actor count, schedule, source/retrieval rules and action limits. Trajectories diverge after interventions, so subsequent context-conditioned comparisons remain descriptive. Refreshed collections use different families, 32 turns and condition-specific defender adapters; they do not isolate adaptation.

Intervals below are pointwise descriptive intervals from 10,000 paired family/seed resamples. Worlds and sequences stay within family; only three generator seeds limit generalization. No formal tests, equivalence claim, composite ranking or simultaneous discovery claim is made. All individual seeds and conditional denominators are available in the tables.

## 1. Channel preferences reproduce, and biographies change their mix

| Condition | Edit | Recollect | Propose |
|---|---:|---:|---:|
| C3 | 5,408/10,800 (50.07%) | 828/10,800 (7.67%) | 969/10,800 (8.97%) |
| C5 | 477/10,800 (4.42%) | 4,618/10,800 (42.76%) | 1,930/10,800 (17.87%) |
| A1 | 938/10,800 (8.69%) | 1,397/10,800 (12.94%) | 4,830/10,800 (44.72%) |

Across all three seeds, C5−C3 is -45.66 pp [95% interval -48.20, -43.06] for edits and +35.09 pp [95% interval +31.64, +38.67] for recollections. C5−A1 is +29.82 pp [95% interval +27.08, +32.66] for recollections and -26.85 pp [95% interval -29.29, -24.40] for proposals. These are rates among **all allocated opportunities**, including invalid attempts. Direct APIs are actually available in eight of twelve slots; the corresponding C5−C3 edit difference is -68.49 pp [95% interval -72.31, -64.58]. The sign is unchanged by that availability sensitivity.

The pilot's C3 89 edits/17 recollections versus C5 5/78 is reproduced exactly, then supported by much larger round-zero collections with no seed reversal in these channel directions. Refreshed collections retain the pattern: C3 edit 5,129/10,800 (47.49%), C5 edit 122/10,800 (1.13%), and A1 proposal 5,228/10,800 (48.41%). These later collections are observational corroboration, not a controlled learning-time comparison.

The difference reaches the mutable state: direct pre/post state changes occur on 3,830/10,800 (35.46%) C3 opportunities, 286/10,800 (2.65%) C5 opportunities and 562/10,800 (5.20%) A1 opportunities. Correct-to-incorrect targeted-state transitions number 3,363, 264 and 498, respectively. These are same-turn changes at each condition's encountered state, not matched-counterfactual severity estimates. Recollection/proposal calls normally append notes, which is a different channel from a slot write. Application, structural validity, notes and following answers are separately counted in ACTION_CHAIN.csv.

This supports an effect of removing these biography strings on channel distribution under the shared setup. It does not isolate narrative content from added prompt length or specific wording, and does not establish a general value of biographies. The two brief biography-style profile variants mention recollection/correction and protection of one's proposal; exact API proportions were not dictated, but semantic priming is a plausible explanation.

## 2. Stable motives predict persistent goals, not necessarily revised strategies

| Condition | Consecutive direct-goal repetition | API change during repeated goal | Exact delivered-claim repeat during repeated goal |
|---|---:|---:|---:|
| C3 | 3,623/5,400 (67.09%) | 551/3,623 (15.21%) | 2,622/3,623 (72.37%) |
| C5 | 4,831/5,224 (92.48%) | 1,164/4,831 (24.09%) | 3,062/4,831 (63.38%) |
| A1 | 5,093/5,364 (94.95%) | 1,265/5,093 (24.84%) | 3,883/5,093 (76.24%) |

The matched family-rate repetition difference is +25.39 pp [95% interval +22.22, +28.58] for C5−C3 and -2.48 pp [95% interval -4.30, -0.69] for C5−A1. C5 does not have uniquely high persistence: motive-only A1 is slightly more repetitive on this measure. The pilot gives 71/96 consecutive repeats for C3 and 77/86 for C5; its Hyde/Rival values remain 43/48 and 34/38.

Operational insistence after a genuine revision away from an actor's previously aligned owned option is 152/304 (50.00%) for C3, 268/304 (88.16%) for C5 and 286/304 (94.08%) for A1. These are overlapping event-window positions, not independent people or episodes. Per-seed matched strata contain 28, 31 and 35 families; the intersection with exposure across every seed is only two families, so the mechanically produced combined interval is not interpreted. This direction is expected from fixed preferred-option instructions. It is not evidence of user-intent adherence, competence or pathology.

Changing an API while retaining a goal is distinct from changing the substance of a claim. The deterministic examples include nearly unchanged advocacy switching from propose to edit, and generic actors changing the actual value pursued. Exact text repetition, paraphrase and semantic development are not interchangeable. Private histories contain at most six records; each actor in C3/C5/A1 receives only six total opportunities and normally four direct ones. Longest runs are heavily episode-censored.

Role order is fixed: Hyde occupies the first actor's schedule and Rival the second. Their direct/communication slots encounter different phases; for example, the first actor acts directly at turn6 while the second acts at7. Even with the same goal, intervening reserved slots alter strict adjacency. Role differences must therefore be read alongside channel_exposure.csv, not attributed solely to psychology.

## 3. Similar source access does not imply equally supported claims

Unavailable references occur on 1,220/10,800 (11.30%) C3 opportunities, 1,229/10,800 (11.38%) C5 opportunities and 1,225/10,800 (11.34%) A1 opportunities. The C5−C3 family-rate difference is +0.08 pp [95% interval -1.17, +1.35]; this is not equivalence. Current explicit support occurs more often in C5 than C3 (+5.46 pp [95% interval +2.62, +8.31]), while C5−A1 is -0.03 pp [95% interval -1.24, +1.14].

These source categories relate a typed value to a visible source and current truth. They do not score whether the prose actually asserts authorization. A recollect action may openly advocate a preference; a correct current value may cite a superseded or assistant-authored source. The narrow current-value/inappropriate-citation flag appears in 537 C3, 668 C5 and 688 A1 actions. Its denominator is all typed actions with a reference, not only correct-value actions. Canonical mismatches are retained without automatically declaring the claim semantically unsupported.

Reference availability can change while the same claim text and source number persist. The fixed source-loss table records such events separately. In the six-item illustrative subset, an unchanged correct recollection becomes source-unavailable later; an apparent corrective message is accurate in one example and contradicted by its own cited assistant output in another. Neither correction vocabulary nor a contradictory value proves hidden intention or deliberate deception. Human semantic labels remain pending.

## 4. Communication delivery is real; meaningful influence remains unestablished

The queue reconstruction checks every actual character observation, with zero mismatches; the 192 missing observations belong to deterministic random corruption, which has no character prompt. In principal round-zero collections C3 sends 3,372 component-directed messages, all observed later. C5 sends 3,234; 3,183 appear in a later inbox and 51 lack a later recipient observation. A1 sends 3,428; 3,422 are observed and 6 lack follow-up. These terminal gaps are not evidence that a recipient ignored a message.

Among observed typed messages, next-opportunity goal matches are 118/3,202 (3.69%) for C3, 39/3,044 (1.28%) for C5 and 21/3,422 (0.61%) for A1. On messages with both a prior and next recipient opportunity, C3 matching is 177/2,500 (7.08%) before versus 106/2,500 (4.24%) after; C5 is 45/2,402 (1.87%) before versus 35/2,402 (1.46%) after. A1 shows a small increase, 6/2,530 (0.24%) before versus 21/2,530 (0.83%) after. Restricting to the same opportunity type before/after gives C3 177/2500 before and 106/2500 after, C5 38/2281 before and 28/2281 after and A1 6/2520 before and 21/2520 after. These references show no common positive pattern across conditions; they are not randomized and cannot estimate message effects.

Typed matching misses cross-slot corrective discussion and can count an action the recipient already favored before receipt. The AI-assisted examples demonstrate both limits without providing prevalence. Source evidence, acknowledgment, disclosure and changes in substantive pursuit need human reading. No cooperation, betrayal, coalition or emergent rivalry is established.

## Behavioral characterization matrix

| Finding | Magnitude / evidence | Prompt expectation | Context or implementation explanation | Evidence level / unresolved question |
|---|---|---|---|---|
| Edits shift to recollections under C5; A1 shifts toward proposals | C5−C3 edit -45.66 pp [95% interval -48.20, -43.06]; C5−A1 recollect +29.82 pp [95% interval +27.08, +32.66]; all three round-zero seeds, pilot, refreshed observational support | Motives and profile language differ; exact API mix is not specified | Same C3/C5/A1 schedule and tools, but wording, prompt length and ensuing states differ | A measured distribution; C narrow biography-text-removal comparison, not a general narrative mechanism |
| C5/A1 sustain typed preferred goals more than C3 | Repetition contrast C5−C3 +25.39 pp [95% interval +22.22, +28.58]; A1 is also highly persistent | Directly expected from fixed owned-option utility versus generic error objective | Fixed role timing, few opportunities, episode censoring; update-away exposures differ by seed | A repetition, B event responsiveness; semantic tactic development unvalidated |
| Similar unavailable-reference rates coexist with many problematic citations | C5−C3 unavailable +0.08 pp [95% interval -1.17, +1.35]; counts and authors in EVIDENCE.csv | Shared retriever; all conditions may distort or misattribute | Visibility changes descriptors; source1 can be genuine but superseded; truncation differs | A structural evidence relations; semantic authorization/deception unresolved |
| Messages arrive, but typed echoes are sparse and not an influence measure | C5 next match 39/3,044 (1.28%); small pilot0/60 | Utilities mention peer endorsement and correction | Compatible owned slots, fixed order, inbox clearing, terminal messages, recipient's existing preference | A delivery; B sequence association; causal communication and rivalry unestablished |

## Ablation and cost limits

C5 versus A1 is the strongest available component-specific comparison: biographies are removed with explicit motives/history/routing retained. It identifies neither universal narrative benefit nor the contribution of motives independently. A2/A3 are available only in the eight-family pilot at this cutoff. A2 removes own history but keeps newly delivered inbox messages. A3 disables delivery and loses all 64 reserved-slot applications in the pilot, including 62 structurally unavailable actions; its contrast bundles communication removal with realized validity/opportunity loss. C4/C5/C6 vary roles, timing and routing, not only actor count. C2 redraws its assignment every opportunity, so its generic owned-goal/alignment fields are not applicable (Amendment003); its channel and state-change counts remain valid. For Traditionalist and Provocateur, literal owned-option adoption does not capture all original-value/departure utility terms. C4 can address the answerer directly in its reserved slots, while multi-antagonist casts are instructed to address peers but are still allowed to send to the answerer.

Owned slots in C5 are distinct, so both preferred options can be simultaneously adopted. Conflict with the user is not the same as conflict between components. Prompt utility text does not demonstrate utility optimization or an equilibrium.

Calls and opportunity caps match, but actual tokens do not. Round-zero C3/C5/A1 generator calls are 10,800 each; input tokens are 12,917,996 / 13,932,753 / 13,330,411 and output tokens 475,747 / 571,126 / 517,734. These include prompt/history overhead. Defender generation, recovery-candidate residuals and loading/reserved time are separately reconciled. No efficiency ranking follows.

## Training and defender outcomes remain separate

| Seed | C1 | C3 | C5 | A1 |
|---|---:|---:|---:|---:|
| 17 | 186/240 | 177/240 | 168/240 | 169/240 |
| 29 | 138/240 | 181/240 | 180/240 | 181/240 |
| 43 | 183/240 | 190/240 | 172/240 | pending at cutoff |


These are antagonist-free 64-turn paired successes from the completed eligible Qwen evaluations at the cutoff. C5 is below C3 at every completed seed and is above clean C1 only at seed29. The untrained Qwen reference remains 67/240 and is not independent replication each time reused. The new behavioral framing does not rescue a task-performance or exploration-breadth claim.

The package reuses 24 verified actual-loss-exposure reconstructions and prior clarification/source audits; six newer fits remain without reconstructed exposure. The corrected C1 format2 join is explicit in Amendment002. Equal input-token training budgets do not imply equal supervised target tokens, unique recovery examples or concentration. Generator behavior, curriculum severity, supervision exposure and defender outcomes can be associated at condition/seed level, but these data do not establish that a channel preference caused learning outcomes. No retraining or new model evaluation occurred.

## Review status and interpretation boundary

The existing 56-window exploration packet, its presentation version and blank forms remain unchanged. A separate 24-item matched addendum supplies longer event windows and actual private-history/inbox context. Both independent-rater forms are blank. Six fixed illustrative readings are AI-assisted and unvalidated, not human ratings or semantic prevalence.

This package supports a neutral characterization of **character-conditioned data generation with supervised adapter training**, history-dependent frozen generators and fixed retrieval. It does not establish psychological personality, hidden intention, co-evolution, an optimized game equilibrium, learned exploration, broad real-world transfer or general intelligence. The single most useful missing experiment is the already prepared compatible/incompatible-goal mechanism diagnostic described in NEXT_EXPERIMENT.md; it remains unscheduled here.
