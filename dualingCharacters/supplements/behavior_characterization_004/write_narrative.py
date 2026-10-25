"""Generate factual prose from saved tables; interpretations remain author-review text."""
from .common import *
from .reporting import rows,mean_rate

def run():
    verify_science();summary=rows('metric_summary.csv');contrasts=read(REPORTS/'matched_contrasts.json')
    def rate(c,m,cohort='main_round_zero'):
        n,d,v=mean_rate(summary,cohort,c,m);return f'{n:,}/{d:,} ({v*100:.2f}%)' if d else 'pending / no denominator'
    def ci(control,metric):
        r=next(r for r in contrasts if r['cohort']=='main_round_zero' and r['second']==control and r['metric']==metric and r['seeds']==[17,29,43])
        return f"{r['difference']*100:+.2f} pp [95% interval {r['lower']*100:+.2f}, {r['upper']*100:+.2f}]"
    def count(c,m):return mean_rate(summary,'main_round_zero',c,m)[0]
    peer_rows=rows('peer_responses.csv')
    def peer_count(c,field,value):
        return sum(int(r['count']) for r in peer_rows if r['cohort']=='main_round_zero' and r['condition']==c and r['recipient_type']=='component' and (field is None or r[field]==value))
    def same_type(c):
        selected=[r for r in peer_rows if r['cohort']=='main_round_zero' and r['condition']==c and r['paired_reference_eligible']=='True' and r['next_same_slot_type']=='True']
        total=sum(int(r['count']) for r in selected);before=sum(int(r['count']) for r in selected if r['previous_response']=='same_goal');after=sum(int(r['count']) for r in selected if r['next_response']=='same_goal')
        return f'{before}/{total} before and {after}/{total} after'
    cost_rows=rows('costs.csv')
    def cost(c,field):return sum(int(r[field]) for r in cost_rows if r['cohort']=='main_round_zero' and r['condition']==c)
    def cost_series(field):return ' / '.join(f'{cost(c,field):,}' for c in ('C3','C5','A1'))
    channel_table='| Condition | Edit | Recollect | Propose |\n|---|---:|---:|---:|\n'+'\n'.join('| '+c+' | '+' | '.join(rate(c,'channel_'+m) for m in ('edit','recollect','propose'))+' |' for c in ('C3','C5','A1'))
    repetition_table='| Condition | Consecutive direct-goal repetition | API change during repeated goal | Exact delivered-claim repeat during repeated goal |\n|---|---:|---:|---:|\n'+'\n'.join('| '+c+' | '+' | '.join(rate(c,m) for m in ('consecutive_direct_goal_repetition','same_goal_channel_change','same_goal_exact_claim_repeat'))+' |' for c in ('C3','C5','A1'))
    secondary=rows('secondary_defender_results.csv')
    eval_table='| Seed | C1 | C3 | C5 | A1 |\n|---|---:|---:|---:|---:|\n'
    for seed in ('17','29','43'):
        values=[]
        for c in ('C1','C3','C5','A1'):
            matches=[r for r in secondary if r['model']=='qwen' and r['condition']==c and r['seed']==seed]
            values.append(matches[0]['paired_successes']+'/240' if matches else 'pending at cutoff')
        eval_table+='| '+seed+' | '+' | '.join(values)+' |\n'
    characterization=f'''# Behavioral Effects of Persistent Motive-Conditioned Components in Conversational Systems

This is an exploratory behavioral characterization, requested after mixed/negative defender results and an inconclusive exploration audit. It does not replace the original research question or require a benefit. The evidence supports reproducible differences in this implementation's action channels and goal persistence, together with limits on what typed peer and evidence metrics establish.

## Evidence and scope

The cutoff is {read(HERE/'EVIDENCE_SNAPSHOT.json')['cutoff_utc']}. All 39 eligible collection cells were analyzed: main round zero, refreshed collections and the final mechanism pilot remain separate. The principal comparison uses the same untrained Qwen3-4B-Instruct-2507 defender, 150 paired training families, 16 turns, seeds17/29/43 and 12 intervention opportunities per world. These are 150 unique families repeated across seeds, not 450 independent families. There are 10,800 allocated opportunities per main condition across seeds. Character weights are frozen; seed changes assignments and sampling, not independently learned character policies. Private histories reset between independent episodes; persistence here means within an episode. The public user scripts are fixed, with a shared six-slot schema.

C3 has two generic adversaries; C5 has Hyde and Rival plus the answerer; A1 removes biography text while keeping their explicit motives, utilities and tools. All three share actor count, schedule, source/retrieval rules and action limits. Trajectories diverge after interventions, so subsequent context-conditioned comparisons remain descriptive. Refreshed collections use different families, 32 turns and condition-specific defender adapters; they do not isolate adaptation.

Intervals below are pointwise descriptive intervals from10,000 paired family/seed resamples. Worlds and sequences stay within family; only three generator seeds limit generalization. No formal tests, equivalence claim, composite ranking or simultaneous discovery claim is made. All individual seeds and conditional denominators are available in the tables.

## 1. Channel preferences reproduce, and biographies change their mix

{channel_table}

Across all three seeds, C5−C3 is {ci('C3','channel_edit')} for edits and {ci('C3','channel_recollect')} for recollections. C5−A1 is {ci('A1','channel_recollect')} for recollections and {ci('A1','channel_propose')} for proposals. These are rates among **all allocated opportunities**, including invalid attempts. Direct APIs are actually available in eight of twelve slots; the corresponding C5−C3 edit difference is {ci('C3','available_channel_edit')}. The sign is unchanged by that availability sensitivity.

The pilot's C3 89 edits/17 recollections versus C5 5/78 is reproduced exactly, then supported by much larger round-zero collections with no seed reversal in these channel directions. Refreshed collections retain the pattern: C3 edit {rate('C3','channel_edit','main_refreshed')}, C5 edit {rate('C5','channel_edit','main_refreshed')}, and A1 proposal {rate('A1','channel_propose','main_refreshed')}. These later collections are observational corroboration, not a controlled learning-time comparison.

The difference reaches the mutable state: direct pre/post state changes occur on {rate('C3','state_changed')} C3 opportunities, {rate('C5','state_changed')} C5 opportunities and {rate('A1','state_changed')} A1 opportunities. Correct-to-incorrect targeted-state transitions number {count('C3','correct_to_incorrect_state'):,}, {count('C5','correct_to_incorrect_state'):,} and {count('A1','correct_to_incorrect_state'):,}, respectively. These are same-turn changes at each condition's encountered state, not matched-counterfactual severity estimates. Recollection/proposal calls normally append notes, which is a different channel from a slot write. Application, structural validity, notes and following answers are separately counted in ACTION_CHAIN.csv.

This supports an effect of removing these biography strings on channel distribution under the shared setup. It does not isolate narrative content from added prompt length or specific wording, and does not establish a general value of biographies. The two brief biography-style profile variants mention recollection/correction and protection of one's proposal; exact API proportions were not dictated, but semantic priming is a plausible explanation.

## 2. Stable motives predict persistent goals, not necessarily revised strategies

{repetition_table}

The matched family-rate repetition difference is {ci('C3','consecutive_direct_goal_repetition')} for C5−C3 and {ci('A1','consecutive_direct_goal_repetition')} for C5−A1. C5 does not have uniquely high persistence: motive-only A1 is slightly more repetitive on this measure. The pilot gives 71/96 consecutive repeats for C3 and 77/86 for C5; its Hyde/Rival values remain 43/48 and34/38.

Operational insistence after a genuine revision away from an actor's previously aligned owned option is {rate('C3','owned_goal_insistence_after_revision')} for C3, {rate('C5','owned_goal_insistence_after_revision')} for C5 and {rate('A1','owned_goal_insistence_after_revision')} for A1. These are overlapping event-window positions, not independent people or episodes. Per-seed matched strata contain28,31 and35 families; the intersection with exposure across every seed is only two families, so the mechanically produced combined interval is not interpreted. This direction is expected from fixed preferred-option instructions. It is not evidence of user-intent adherence, competence or pathology.

Changing an API while retaining a goal is distinct from changing the substance of a claim. The deterministic examples include nearly unchanged advocacy switching from propose to edit, and generic actors changing the actual value pursued. Exact text repetition, paraphrase and semantic development are not interchangeable. Private histories contain at most six records; each actor in C3/C5/A1 receives only six total opportunities and normally four direct ones. Longest runs are heavily episode-censored.

Role order is fixed: Hyde occupies the first actor's schedule and Rival the second. Their direct/communication slots encounter different phases; for example, the first actor acts directly at turn6 while the second acts at7. Even with the same goal, intervening reserved slots alter strict adjacency. Role differences must therefore be read alongside channel_exposure.csv, not attributed solely to psychology.

## 3. Similar source access does not imply equally supported claims

Unavailable references occur on {rate('C3','reference_reference_unavailable')} C3 opportunities, {rate('C5','reference_reference_unavailable')} C5 opportunities and {rate('A1','reference_reference_unavailable')} A1 opportunities. The C5−C3 family-rate difference is {ci('C3','reference_reference_unavailable')}; this is not equivalence. Current explicit support occurs more often in C5 than C3 ({ci('C3','reference_explicit_current_support')}), while C5−A1 is {ci('A1','reference_explicit_current_support')}.

These source categories relate a typed value to a visible source and current truth. They do not score whether the prose actually asserts authorization. A recollect action may openly advocate a preference; a correct current value may cite a superseded or assistant-authored source. The narrow current-value/inappropriate-citation flag appears in {count('C3','current_value_inappropriate_citation'):,} C3, {count('C5','current_value_inappropriate_citation'):,} C5 and {count('A1','current_value_inappropriate_citation'):,} A1 actions. Its denominator is all typed actions with a reference, not only correct-value actions. Canonical mismatches are retained without automatically declaring the claim semantically unsupported.

Reference availability can change while the same claim text and source number persist. The fixed source-loss table records such events separately. In the six-item illustrative subset, an unchanged correct recollection becomes source-unavailable later; an apparent corrective message is accurate in one example and contradicted by its own cited assistant output in another. Neither correction vocabulary nor a contradictory value proves hidden intention or deliberate deception. Human semantic labels remain pending.

## 4. Communication delivery is real; meaningful influence remains unestablished

The queue reconstruction checks every actual character observation, with zero mismatches; the192 missing observations belong to deterministic random corruption, which has no character prompt. In principal round-zero collections C3 sends {peer_count('C3',None,None):,} component-directed messages, all observed later. C5 sends {peer_count('C5',None,None):,}; {peer_count('C5','visible','True'):,} appear in a later inbox and {peer_count('C5','visible',''):,} lack a later recipient observation. A1 sends {peer_count('A1',None,None):,}; {peer_count('A1','visible','True'):,} are observed and {peer_count('A1','visible',''):,} lack follow-up. These terminal gaps are not evidence that a recipient ignored a message.

Among observed typed messages, next-opportunity goal matches are {rate('C3','visible_typed_next_goal_match')} for C3, {rate('C5','visible_typed_next_goal_match')} for C5 and {rate('A1','visible_typed_next_goal_match')} for A1. On messages with both a prior and next recipient opportunity, C3 matching is {rate('C3','peer_before_goal_match')} before versus {rate('C3','peer_after_goal_match')} after; C5 is {rate('C5','peer_before_goal_match')} before versus {rate('C5','peer_after_goal_match')} after. A1 shows a small increase, {rate('A1','peer_before_goal_match')} before versus {rate('A1','peer_after_goal_match')} after. Restricting to the same opportunity type before/after gives C3 {same_type('C3')}, C5 {same_type('C5')} and A1 {same_type('A1')}. These references show no common positive pattern across conditions; they are not randomized and cannot estimate message effects.

Typed matching misses cross-slot corrective discussion and can count an action the recipient already favored before receipt. The AI-assisted examples demonstrate both limits without providing prevalence. Source evidence, acknowledgment, disclosure and changes in substantive pursuit need human reading. No cooperation, betrayal, coalition or emergent rivalry is established.

## Behavioral characterization matrix

| Finding | Magnitude / evidence | Prompt expectation | Context or implementation explanation | Evidence level / unresolved question |
|---|---|---|---|---|
| Edits shift to recollections under C5; A1 shifts toward proposals | C5−C3 edit {ci('C3','channel_edit')}; C5−A1 recollect {ci('A1','channel_recollect')}; all three round-zero seeds, pilot, refreshed observational support | Motives and profile language differ; exact API mix is not specified | Same C3/C5/A1 schedule and tools, but wording, prompt length and ensuing states differ | A measured distribution; C narrow biography-text-removal comparison, not a general narrative mechanism |
| C5/A1 sustain typed preferred goals more than C3 | Repetition contrast C5−C3 {ci('C3','consecutive_direct_goal_repetition')}; A1 is also highly persistent | Directly expected from fixed owned-option utility versus generic error objective | Fixed role timing, few opportunities, episode censoring; update-away exposures differ by seed | A repetition, B event responsiveness; semantic tactic development unvalidated |
| Similar unavailable-reference rates coexist with many problematic citations | C5−C3 unavailable {ci('C3','reference_reference_unavailable')}; counts and authors in EVIDENCE.csv | Shared retriever; all conditions may distort or misattribute | Visibility changes descriptors; source1 can be genuine but superseded; truncation differs | A structural evidence relations; semantic authorization/deception unresolved |
| Messages arrive, but typed echoes are sparse and not an influence measure | C5 next match {rate('C5','visible_typed_next_goal_match')}; small pilot0/60 | Utilities mention peer endorsement and correction | Compatible owned slots, fixed order, inbox clearing, terminal messages, recipient's existing preference | A delivery; B sequence association; causal communication and rivalry unestablished |

## Ablation and cost limits

C5 versus A1 is the strongest available component-specific comparison: biographies are removed with explicit motives/history/routing retained. It identifies neither universal narrative benefit nor the contribution of motives independently. A2/A3 are available only in the eight-family pilot at this cutoff. A2 removes own history but keeps newly delivered inbox messages. A3 disables delivery and loses all64 reserved-slot applications in the pilot, including62 structurally unavailable actions; its contrast bundles communication removal with realized validity/opportunity loss. C4/C5/C6 vary roles, timing and routing, not only actor count. C2 redraws its assignment every opportunity, so its generic owned-goal/alignment fields are not applicable (Amendment003); its channel and state-change counts remain valid. For Traditionalist and Provocateur, literal owned-option adoption does not capture all original-value/departure utility terms. C4 can address the answerer directly in its reserved slots, while multi-antagonist casts are instructed to address peers but are still allowed to send to the answerer.

Owned slots in C5 are distinct, so both preferred options can be simultaneously adopted. Conflict with the user is not the same as conflict between components. Prompt utility text does not demonstrate utility optimization or an equilibrium.

Calls and opportunity caps match, but actual tokens do not. Round-zero C3/C5/A1 generator calls are {cost('C3','generator_calls'):,} each; input tokens are {cost_series('generator_input_tokens')} and output tokens {cost_series('generator_output_tokens')}. These include prompt/history overhead. Defender generation, recovery-candidate residuals and loading/reserved time are separately reconciled. No efficiency ranking follows.

## Training and defender outcomes remain separate

{eval_table}

These are antagonist-free64-turn paired successes from the completed eligible Qwen evaluations at the cutoff. C5 is below C3 at every completed seed and is above clean C1 only at seed29. The untrained Qwen reference remains67/240 and is not independent replication each time reused. The new behavioral framing does not rescue a task-performance or exploration-breadth claim.

The package reuses24 verified actual-loss-exposure reconstructions and prior clarification/source audits; six newer fits remain without reconstructed exposure. The corrected C1 format2 join is explicit in Amendment002. Equal input-token training budgets do not imply equal supervised target tokens, unique recovery examples or concentration. Generator behavior, curriculum severity, supervision exposure and defender outcomes can be associated at condition/seed level, but these data do not establish that a channel preference caused learning outcomes. No retraining or new model evaluation occurred.

## Review status and interpretation boundary

The existing56-window exploration packet, its presentation version and blank forms remain unchanged. A separate24-item matched addendum supplies longer event windows and actual private-history/inbox context. Both independent-rater forms are blank. Six fixed illustrative readings are AI-assisted and unvalidated, not human ratings or semantic prevalence.

This package supports a neutral characterization of **character-conditioned data generation with supervised adapter training**, history-dependent frozen generators and fixed retrieval. It does not establish psychological personality, hidden intention, co-evolution, an optimized game equilibrium, learned exploration, broad real-world transfer or general intelligence. The single most useful missing experiment is the already prepared compatible/incompatible-goal mechanism diagnostic described in NEXT_EXPERIMENT.md; it remains unscheduled here.
'''
    for before,after in [('from10,000','from 10,000'),('seeds17','seeds 17'),('seeds,17','seeds, 17'),('and34/38','and 34/38'),('contain28,31 and35','contain 28, 31 and 35'),('the192','the 192'),('only8-family','only 8-family'),('all64','all 64'),('including62','including 62'),('antagonist-free64','antagonist-free 64'),('remains67/240','remains 67/240'),('reuses24','reuses 24'),('existing56','existing 56'),('separate24','separate 24')]:characterization=characterization.replace(before,after)
    (HERE/'BEHAVIORAL_CHARACTERIZATION.md').write_text(characterization)
    manuscript=f'''# Author-review results and discussion

## Results: observable behavior under persistent motive conditioning

We characterized completed training interactions after the original mixed/negative accuracy results and an inconclusive exploration audit. The main behavioral comparison held the untrained Qwen defender, family/world pairs,16-turn horizon,12-opportunity schedule, tools and generator weights fixed, using150 unique families across three generator seeds. Refreshed collections and the eight-family mechanism pilot were analyzed separately. This was an exploratory descriptive analysis, not an original confirmatory endpoint.

Character-conditioned generators used fewer direct edits and more recollection actions than generic adversaries. Edits occurred on {rate('C3','channel_edit')} C3 and {rate('C5','channel_edit')} C5 opportunities, a matched-family difference of {ci('C3','channel_edit')}. Recollections showed the opposite difference, {ci('C3','channel_recollect')}. Removing biography text while preserving explicit motives shifted actions toward proposals: C5−A1 recollection {ci('A1','channel_recollect')}, proposal {ci('A1','channel_propose')}. All three seeds reproduced these directions. Observable shared-state writes also differed, but notes, direct edits and subsequent defender outputs were treated as separate channels.

Within-actor consecutive typed-goal repetition was {rate('C3','consecutive_direct_goal_repetition')} for C3, {rate('C5','consecutive_direct_goal_repetition')} for C5 and {rate('A1','consecutive_direct_goal_repetition')} for A1. The fixed-goal conditions often continued their owned option after authorized user revisions away from it. This is consistent with the supplied utilities, not evidence of helpful robustness. API changes and exact text changes were reported separately; neither establishes substantive strategy development.

Unavailable-reference rates were similar descriptively, with C5−C3 {ci('C3','reference_reference_unavailable')}, without an equivalence claim. Current support, superseded authority, assistant sources and canonical mismatch were distinguished. Delivered peer messages were usually observed, but C5 next-opportunity typed matches were only {rate('C5','visible_typed_next_goal_match')}. The recipient's prior behavior provides a descriptive reference, not a counterfactual. Deterministic text examples show that typed matching can miss a corrective disclosure and can also match an already pursued goal. Human semantic validation is pending.

## Discussion and limits

The most defensible contribution is a reproducible characterization of how this motive-conditioned system acts: channel selection, persistent goal endorsement, evidence relations and limited measured peer response. The biography ablation affects channel use despite similar descriptor coverage in the prior audit. This isolates removal of these biography strings, including their length and wording, rather than narrative sophistication in general. Private history and communication are not separately established mechanisms: their larger main cells are pending, and the pilot communication ablation incurs rejected actions. Fixed role timing and jointly satisfiable owned slots constrain any interpersonal explanation.

Behavioral differences do not imply superiority. C5 paired successes at seeds17/29/43 are168/180/172 of240, compared with C3's177/181/190 and clean C1's186/138/183. Thus C5 remains below C3 in every available seed; the clean comparison is mixed. The existing exploration audit remains inconclusive. Different interventions may alter recovery diversity and supervised exposure, but there is no causal mediation analysis or matched-severity counterfactual here. Independent-model learned replication, naturalistic intent evaluation and human ratings remain separate pending evidence.

Profiles and utility terms are prompts for frozen generators; retrieval is fixed, while the answerer receives supervised adapter updates in the original campaign. We make no claim of learned character policies, co-evolution, psychological personality, emergent coalitions, equilibrium optimization or open-ended planning. Interpretations and scientific arguments require human author review. See RELATED_WORK.md for primary-method precedents and NEXT_EXPERIMENT.md for the already prepared discriminating diagnostic.
'''
    for before,after in [('pairs,16-turn','pairs, 16-turn'),('horizon,12-opportunity','horizon, 12-opportunity'),('using150','using 150'),('seeds17','seeds 17'),('are168','are 168'),('of240','of 240'),("C3's177","C3's 177"),("C1's186","C1's 186")]:manuscript=manuscript.replace(before,after)
    (HERE/'MANUSCRIPT_SECTION.md').write_text(manuscript)
    claims=f'''# Claim-to-evidence table

| Claim | Status / level | Evidence | What it does not establish |
|---|---|---|---|
| C5 uses fewer edits/more recollections than C3 | A: directly measured, reproduced across3 round-zero seeds | {ci('C3','channel_edit')}; {ci('C3','channel_recollect')}; CHANNELS.csv, PRIMARY_DESCRIPTIVE_CONTRASTS.csv | Benefit, causal training improvement or universal behavior |
| Removing biography text changes channel distribution with motives retained | C: narrow controlled implementation comparison | C5−A1 recollection {ci('A1','channel_recollect')}; all3seeds | Narrative content apart from length/wording; superiority of biographies |
| Fixed-motive C5/A1 repeat typed goals more than C3 | A; expected prompt compliance | PERSISTENCE.csv, goal_runs.csv, metric_summary.csv | Semantic coherence, adaptation, pathology or useful robustness |
| Owned-option pursuit persists after some legitimate revisions | B: context association | CONTEXT.csv; fixed before/after windows; per-seed denominators | Causal effect of revision, hidden intention or learner goal understanding |
| A peer message caused another actor or defender to change | D: unresolved | Delivery/inbox reconstruction and PEER_RESPONSE.csv establish sequence only | Randomized communication effect; cooperation/coalition |
| Source mismatch proves deliberate deception | Unsupported | Structural source relations and six AI-assisted examples; human forms blank | Hidden mental state or validated semantic prevalence |
| Biographies are necessary for persistent goals | Not supported | A1 repetition is at least as high descriptively; narrow C5−A1 comparison | Equivalence of all narrative and motive-only forms |
| History or interaction is an isolated general mechanism | Pending/qualified | Only8-family A2/A3 pilot; validity and routing differ | Separate causal attribution in larger collections |
| C5 improves average antagonist-free task performance over C3 | Not supported in completed Qwen seeds | secondary_defender_results.csv; C5 lower at all3seeds | A universal impossibility result for other architectures |
| Characters improve exploration breadth or learned exploration | Unestablished | Prior exploration003 inconclusive; no defender exploration evaluation | Benefit rescued by this new descriptive framing |

A=direct observation; B=association; C=valid controlled manipulation with its limited scope; D=new evidence required. Formal causal conclusions about downstream performance are withheld.
'''
    (HERE/'CLAIM_TO_EVIDENCE.md').write_text(claims)
    write(REPORTS/'NARRATIVE_PROVENANCE.json',{'script_sha256':sha256(Path(__file__)),
        'inputs':{n:sha256(REPORTS/n) for n in ('metric_summary.csv','matched_contrasts.json','secondary_defender_results.csv')},
        'outputs':{n:sha256(HERE/n) for n in ('BEHAVIORAL_CHARACTERIZATION.md','MANUSCRIPT_SECTION.md','CLAIM_TO_EVIDENCE.md')},
        'qualification':'Primary quantitative prose interpolated from saved tables; interpretations are explicitly author-review drafts.'})

if __name__=='__main__':run()
