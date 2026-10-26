from .common import *
from .prose import tidy
def run():
 rows=csv_read(HERE/'tables/CHANNELS_AND_CHANGES.csv');nums=csv_read(HERE/'tables/MECHANICAL_COUNTS.csv');cs=read(HERE/'tables/CONTRASTS.json')
 def count(c,m,s='all'):
  r=next(r for r in rows if r['condition']==c and r['seed']==s and r['metric']==m);return f"{int(r['numerator']):,}/{int(r['denominator']):,} ({100*float(r['pooled_rate']):.2f}%)"
 def rep(c,s='all'):
  r=next(r for r in nums if r['condition']==c and r['generator_seed']==s and r['metric']=='consecutive_direct_goal_repetition');return f"{int(r['numerator']):,}/{int(r['denominator']):,} ({100*float(r['pooled_rate']):.2f}%)"
 def ci(second,metric):
  r=next(r for r in cs if r['second']==second and r['metric']==metric and r['seeds']==[17,29,43]);return f"{100*r['difference']:+.2f} pp [95% pointwise interval {100*r['lower']:+.2f}, {100*r['upper']:+.2f}]"
 text='''# What changes when motives and biographies are introduced?

**Findings brief · exploratory clarification007 · human semantic validation pending.** This implemented system uses a shared frozen Qwen backbone with separate actor contexts. C3 has two generic adversaries; C5 has two biography-plus-motive characters; A1 keeps the same motives without biographies. One answerer is additional in each condition.

**Population.** Common-base round-zero collections: 150 unique training families ×2 paired worlds ×3 generator seeds (17/29/43) =900 episodes and10,800 allocated actor opportunities per condition. Each episode has16 user/answerer turns and12 actor opportunities. The same150 families recur across seeds. This is not900 independent families or three independently trained character policies. Later refreshed collections and trained-answerer tests are separate.

## 1. The intervention channels differ reproducibly

| Condition | Direct edit | Recollect | Propose |
|---|---:|---:|---:|
'''
 for c in ['C3','C5','A1']:text+='| '+c+' | '+' | '.join(count(c,m) for m in ['channel_edit','channel_recollect','channel_propose'])+' |\n'
 text+=f'''
All opportunities are retained; peer/pass/malformed/invalid channels complete the distribution in Figure1. These are **API labels, not false-memory or deception categories**. C5−C3 edit frequency is {ci('C3','channel_edit')}; recollect frequency is {ci('C3','channel_recollect')}. C5−A1 recollect frequency is {ci('A1','channel_recollect')}. Narrative removal shifts which note API is used; it does not by itself establish a difference in what the claim means.

Seed-level numerators (each denominator3,600):

| Condition | Edit17/29/43 | Recollect17/29/43 | Propose17/29/43 |
|---|---:|---:|---:|
'''
 for c in ['C3','C5','A1']:
  text+='| '+c+' | '+' | '.join('/'.join(next(r['numerator'] for r in rows if r['condition']==c and r['seed']==s and r['metric']==m) for s in ['17','29','43']) for m in ['channel_edit','channel_recollect','channel_propose'])+' |\n'
 text+='''
The original10,000-draw paired family/seed bootstrap preserves worlds inside families and uses seed400041. Intervals describe mean paired family-rate differences, not independent actions. Only three generator seeds limit seed-generalization; no equivalence or new significance test is claimed.

## 2. Typed preferences persist in both character and motive-only conditions

| Condition | Repeated eligible direct-goal pairs | Immediate state changes / all opportunities |
|---|---:|---:|
'''
 for c in ['C3','C5','A1']:text+='| '+c+' | '+rep(c)+' | '+count(c,'state_changed')+' |\n'
 text+=f'''
Repetition compares consecutive eligible edit/recollect/propose actions **within actor and episode**, skipping non-direct opportunities according to the frozen metric. It measures the same typed slot/value, not coherent argument development. C5−C3 mean family-rate repetition is {ci('C3','consecutive_direct_goal_repetition')}; C5−A1 is {ci('A1','consecutive_direct_goal_repetition')}. Pooled fractions above have unequal eligible-pair denominators and need not equal differences between family means.

Fixed owned-option prompts directly encourage persistence. Fewer immediate state changes in C5/A1 are consistent with their use of notes rather than edits; the comparison is not a counterfactual measure of harmful influence. Notes may affect later answers, or have no observed effect. Per-seed repetition/state counts and white-dot seed values appear in Table MECHANICAL_COUNTS and Figure3.

## 3. API, proposition, delivery and response are distinct

In A1 case DI5-e743bcb1a6, the exact “I propose shifting the venue to Garden…” sentence appears as propose at turn7 and recollect at turn10; both append notes, omitting the separate numeric source. In C5 case DI5-a4c89ffad4, Tuesday is authorized, a peer challenges Saturday, and the recipient repeats “The event day should be Saturday…” while the answerer retains Tuesday. Earlier turn9 language explicitly invokes user-approved constraints. The later “should” sentence alone need not claim approval. Figure2 and the reader edition show complete statements and locators.

These are selected illustrations, not semantic prevalence estimates. The fixed review contains64 component-directed events and8 answerer-directed notes, not72 peer exchanges. All72 retain their IDs; independent human assessment is pending. The corrected rubric separates incoming propositions, recipient behavior, citation support, visibility and dimension missingness.

## Context and remaining discrimination

Antagonist-free Qwen paired success at64 turns (240 test families per seed): C1=186/138/183, C3=177/181/190, C5=168/180/172 for training seeds17/29/43. The untrained reference is67/240 once. C5 trails C3 at each matched seed; behavioral differences do not establish learning benefit. The earlier eight-family descriptor-breadth pilot was inconclusive, not a demonstration of broader exploration.

The strongest next validation is two independent assessments of the **same72 fixed events** under v2, resolving preference versus authorization and actual recipient response with missingness-aware agreement. Preference-compatibility and delivery interventions remain separate pending mechanism tests. Correct final plans, matching later actions and visible messages do not independently establish persuasion, rivalry or causal learning mechanisms.

Sources: frozen005 FAMILY_NUMERATORS/REPRODUCED_CONTRASTS,004 CHANNELS and006 PERFORMANCE_CONTEXT, with hashes and72 reproduced estimates in reports/NUMERIC_VERIFICATION.json. Six purposive reader case groups link to the unchanged48-episode archive. No new inference or human labels were added.
'''
 (HERE/'FINDINGS_BRIEF.md').write_text(tidy(text))
if __name__=='__main__':run()
