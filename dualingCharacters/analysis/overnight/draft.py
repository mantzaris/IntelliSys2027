"""Populate an explicitly interim author-review manuscript from audited tables."""
from pathlib import Path
from collections import defaultdict
import json
from .common import ROOT,OUT,CACHE,read,write,utc


def tex(value):
    return str(value).replace('\\',r'\textbackslash{}').replace('_',r'\_').replace('%',r'\%').replace('&',r'\&').replace('#',r'\#')


def main():
    rows=read(OUT/'per_seed_results.json');comparisons=read(OUT/'paired_transitions.json');exposure=read(OUT/'supervision_exposure.json');pools=read(OUT/'supervision_pools.json')
    c5=next((r for r in rows if r['model']=='qwen' and r['condition']=='C5' and r['seed']==17),None)
    if c5:
        controls={r['condition']:r for r in rows if r['model']=='qwen' and r['seed']==17}
        abstract=f'For the fixed first seed, three-character training achieved {c5["paired_successes"]}/240 paired successes, compared with {controls["C3"]["paired_successes"]}/240 for generic adversarial training and {controls["C1"]["paired_successes"]}/240 for clean training. Complete multi-seed and independent-family conclusions remain pending.'
    else:abstract='The available initial trained evaluations improve on the untrained reference; the primary three-character comparison remains pending.'
    (OUT/'draft_abstract_results.tex').write_text(abstract+'\n')
    lines=[r'\textbf{Interim descriptive snapshot.} All included evaluations are complete and eligible; the planned grid is still incomplete. This paragraph and the tables regenerate from audited saved artifacts.']
    lines += [r'\begin{table}[ht]\centering\caption{Completed main evaluations; each row has 240 paired families and 480 conversations at 64 turns.}\begin{tabular}{llrrr}\toprule Model & Condition & Seed & Paired successes & Conversation successes\\\midrule']
    for r in rows:lines.append(f'{r["model"]} & {r["condition"]} & {r["seed"]} & {r["paired_successes"]}/240 & {r["conversation_successes"]}/480\\\\')
    lines += [r'\bottomrule\end{tabular}\end{table}']
    for model in ('qwen','phi'):
        for condition in ('C1','C3','C4','C5','A1','A2','A3','C2','C6'):
            observed=[r for r in rows if r['model']==model and r['condition']==condition]
            if len(observed)>1:
                values=', '.join(f'seed {r["seed"]}: {r["paired_successes"]}/240' for r in observed)
                lines.append(f'Observed {model} {condition} results are {values}. These are the completed seeds, not a substitute for the full planned seed set; family-only intervals do not describe this training-seed variation.')
    key=[r for r in comparisons if r['contrast'] in {'C5-C3','C5-C1','C5-C4','C5-A1','C5-A2','C5-A3','C3-C1'}]
    lines += [r'\begin{table}[ht]\centering\caption{Individual-seed exploratory contrasts. Intervals use family resampling only and cannot estimate training-seed variation.}\begin{tabular}{llrrr}\toprule Model & Contrast & Seed & Difference (pp) & 95\% interval (pp)\\\midrule']
    for r in key:lines.append(f'{r["model"]} & {r["contrast"]} & {r["seed"]} & {100*r["difference"]:.2f} & [{100*r["ci95_low"]:.2f}, {100*r["ci95_high"]:.2f}]\\\\')
    if not any(r['contrast']=='C5-C3' for r in key):lines.append(r'qwen & C5-C3 & 17 & pending & pending\\')
    if not any(r['contrast']=='C5-C1' for r in key):lines.append(r'qwen & C5-C1 & 17 & pending & pending\\')
    lines += [r'\bottomrule\end{tabular}\end{table}']
    for model in ('qwen','phi'):
        matched=[r for r in key if r['model']==model and r['contrast']=='C3-C1']
        if matched and min(r['difference'] for r in matched)<0<max(r['difference'] for r in matched):
            lines.append(f'For {model}, the observed C3--C1 difference changes sign across completed training seeds. This variability is retained; it cannot be represented by a single-seed family interval, and it does not authorize checkpoint selection or extra runs.')
    for model in ('qwen','phi'):
        for seed in (17,29,43):
            primary=next((r for r in key if r['model']==model and r['seed']==seed and r['contrast']=='C5-C3'),None)
            clean=next((r for r in key if r['model']==model and r['seed']==seed and r['contrast']=='C5-C1'),None)
            if primary and clean:
                if primary['difference']>0 and clean['difference']<0:lines.append(f'For {model} seed {seed}, C5 exceeds C3 but remains below C1. This is not demonstrated practical superiority over clean training.')
                elif primary['difference']<=0:
                    lines.append(f'For {model} seed {seed}, C5 does not exceed C3 in the point estimate. This observed result does not support an advantage over generic adversarial training for this seed.')
                    if clean['difference']<0:lines.append(f'C5 is also below clean C1 by {-100*clean["difference"]:.2f} percentage points. Improvement over the untrained model therefore does not establish superiority over either trained control.')
                else:lines.append(f'For {model} seed {seed}, the C5 point estimate exceeds C3 and is not below C1. Replicated inference and mechanism-specific controls remain necessary.')
                lines.append(f'The C5--C3 paired transitions are {primary["both_succeed"]} both successful, {primary["only_first"]} C5-only, {primary["only_second"]} C3-only and {primary["neither"]} neither, among 240 families.')
    lines.append('Complete planned-seed inference is '+('available in the separate frozen analysis tables.' if read(OUT/'complete_seed_contrasts.json') else 'pending. No interim significance result changes the schedule or checkpoint rule.'))
    for r in key:
        if r['contrast']=='C5-A1':
            lines.append(f'For {r["model"]} seed {r["seed"]}, narrative C5 minus motive-only A1 is {100*r["difference"]:+.2f} percentage points, with an exploratory family interval [{100*r["ci95_low"]:+.2f}, {100*r["ci95_high"]:+.2f}]. This single-seed observation cannot establish a general narrative advantage or equivalence.')
    (OUT/'draft_results.tex').write_text('\n'.join(lines)+'\n')
    diag=['Failure counts separate mutually exclusive categories and overlapping flags. They do not sum overlapping dependency, source and update errors as distinct failed conversations.']
    for r in rows:
        if r['condition']!='base':
            diag.append(f'{r["model"]} {r["condition"]} seed {r["seed"]} has {r["failed_conversations"]} failed conversations; all six commitments were recalled correctly in {r["recall_correct_conversations"]}/480 conversations, and every canonical authorizing source was visible in {r["all_canonical_sources_visible"]}/480 final prompts.')
    totals=defaultdict(lambda:[0,0])
    for r in exposure:
        if r['status']=='reconstructed_and_verified':totals[r['model'],r['condition'],r['seed']][0]+=r['training_input_tokens'];totals[r['model'],r['condition'],r['seed']][1]+=r['supervised_target_tokens']
    diag += [r'\begin{table}[ht]\centering\caption{Actual exposure across completed fits only; an unfinished second round must not be read as a full two-round budget.}\begin{tabular}{llrrr}\toprule Model & Condition & Seed & Training input tokens & Supervised targets\\\midrule']
    for (m,c,s),(inputs,targets) in totals.items():diag.append(f'{m} & {c} & {s} & {inputs:,} & {targets:,}\\\\')
    diag += [r'\bottomrule\end{tabular}\end{table}','Equal input-token quotas do not imply equal supervised-target exposure. These descriptive differences cannot establish that exposure caused performance differences.']
    for r in pools:
        if r['pool']=='recovery' and r['condition']=='C1' and r['seed']==17 and '-r1-' in r['run_id']:
            diag.append(f'C1 round-one recovery uses {r["loss_contributing_unique_windows"]} distinct loss-contributing windows from {r["loss_contributing_unique_families"]} families on {r["loss_contributing_occurrences"]} contributing occurrences. The top five windows account for {100*r["top5_token_share"]:.1f}\\% of recovery target tokens. Repetition does not create new independent examples.')
    (OUT/'draft_diagnostics.tex').write_text('\n'.join(diag)+'\n')
    claims=[('Base improvement','Compare completed per-seed rows with the one reused untrained reference; this alone is ordinary supervised-learning evidence.'),
      ('Clean-training superiority','Requires C5 versus C1. A C5 advantage over C3 alone is insufficient.'),
      ('Generic-adversarial advantage','Requires the prespecified C5 versus C3 contrast, with all planned seeds for confirmatory interpretation.'),
      ('Narrative, history, peers','Require A1, A2 and A3 respectively; no pooled persona label establishes these mechanisms.'),
      ('Memory necessity','Terminal-memory removals and common-input reasoning are pending unless their separately frozen diagnostics finish.'),
      ('Broad transfer','Domain framings share one six-slot schema. Independent architecture replication and external memory QA are distinct, bounded evidence.')]
    text=[r'\begin{table}[ht]\centering\caption{Claim-to-evidence boundaries for scientific author review.}\begin{tabular}{p{.24\textwidth}p{.68\textwidth}}\toprule Claim & Required evidence or limitation\\\midrule']
    text += [tex(a)+' & '+tex(b)+r'\\' for a,b in claims];text.append(r'\bottomrule\end{tabular}\end{table}')
    (OUT/'draft_claims.tex').write_text('\n'.join(text)+'\n')
    claim_rows=['# Claim-to-evidence ledger — interim author review\n',
      'These interpretations are provisional. One-seed family intervals do not estimate training-seed variation. '
      'No result changes the fixed queue, training, sample counts or checkpoint selection.\n',
      '| Claim | Available observation | Boundary |','|---|---|---|']
    for label,explanation in [('C5-base','Improvement over the shared untrained reference is not evidence for the character mechanism.'),
      ('C5-C1','Practical superiority requires this clean-training control; ordinary supervised learning remains an alternative.'),
      ('C5-C3','This is the primary contrast, but confirmatory interpretation requires all planned seeds and the frozen analysis.'),
      ('C5-C4','The original communication routing differs, limiting an isolated learned character-count interpretation.'),
      ('C5-A1','This contrasts narrative profiles with concise motives; a one-seed difference does not establish a general narrative advantage.'),
      ('C5-A2','Persistence requires the private-history ablation; frozen history-dependent characters are not co-evolving policies.'),
      ('C5-A3','Peer interaction requires its ablation; typed message/action matches alone are not coalition evidence.')]:
        available=[r for r in comparisons if r['contrast']==label]
        observations='; '.join(f'{r["model"]} seed {r["seed"]}: {100*r["difference"]:+.2f} pp [{100*r["ci95_low"]:+.2f}, {100*r["ci95_high"]:+.2f}]' for r in available) or 'Pending'
        claim_rows.append(f'| {label} | {observations} | {explanation} |')
    claim_rows += ['| Terminal memory or trajectory necessity | Supplement A pending full-core gate | Similar terminal ablation scores would not show that earlier trajectory never mattered; removed evidence must be quantified. |',
      '| Incompatible rivalry and semantic coordination | Original goals can be jointly satisfied; supplement B pending | Persistent antagonistic personas are established more directly than incompatible rivalry. Human semantic ratings remain absent. |',
      '| Transfer beyond shared synthetic schema | Independent-family trained replication, external benchmark and prose review pending | Four domain framings reuse six slots; ambiguity is confounded with creative/held-out cases. |',
      '| Exposure or severity mechanism | Descriptive exposure/source/routing tables available | Associations do not establish why one condition performs differently; matched causal severity replay remains pending. |']
    (OUT/'CLAIM_TO_EVIDENCE.md').write_text('\n'.join(claim_rows)+'\n')
    write(OUT/'DRAFT_STATUS.json',{'generated_utc':utc(),'source':'paper/overnight_author_review.tex','classification':'Interim author-review draft; not submission-ready',
      'bibliography':'Existing verified paper/references.bib; no new citations introduced','actual_evaluations':len(rows),'human_scientific_review':'pending'})


if __name__=='__main__':main()
