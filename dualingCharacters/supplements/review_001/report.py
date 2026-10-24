"""Compact review response regenerated from separate audit tables."""
from datetime import datetime,timezone
from pcc.resources import sha256,used_seconds
from pcc.freeze import verify_freeze
from pcc.campaign import jobs,resolve_job,load_overrides
from .common import ROOT,HERE,ARTIFACTS,RESULTS,read,write,write_csv
from .analyze import pairs,contrast


def table(rows,columns):
    return '\n'.join(['| '+' | '.join(columns)+' |','| '+' | '.join(['---']*len(columns))+' |',
      *['| '+' | '.join(str(r.get(k,'pending')) for k in columns)+' |' for r in rows]])


def main():
    now=datetime.now(timezone.utc).isoformat();frozen=verify_freeze(ROOT)
    findings=read(RESULTS/'review_findings.json');mainrows=read(RESULTS/'main_recomputed.json');exposure=read(RESULTS/'supervision_pool_concentration.json')
    existing={};existing_inputs={}
    for row in mainrows:
        if row['model']=='qwen' and row['seed']==17 and row['condition'] in {'base','C1','C3','C5'}:
            path=ROOT/'artifacts/runs'/row['run_id']/'evaluation_summary.json'
            existing[row['condition']]=pairs(read(path));existing_inputs[str(path.relative_to(ROOT))]=sha256(path)
    contrasts=[]
    for left,right in [('C1','base'),('C3','base'),('C3','C1'),('C5','base'),('C5','C1'),('C5','C3')]:
        if left in existing and right in existing:contrasts.append(contrast(existing[left],existing[right],left+'-'+right))
    write(RESULTS/'existing_test_contrasts.json',{'classification':'Post-review exploratory, fixed seed17 only; not the core hierarchical confirmatory contrast','rows':contrasts,'inputs':existing_inputs})
    write_csv(RESULTS/'existing_test_contrasts.csv',contrasts)
    stages=read(RESULTS/'supplement_status.json');queue=[resolve_job(j,load_overrides(ROOT))['id'] for j in jobs(frozen['plan'])]
    completed=sum((ROOT/f'artifacts/runs/{j}/status.json').exists() and read(ROOT/f'artifacts/runs/{j}/status.json')['status']=='completed' for j in queue)
    live=read(ROOT/'artifacts/campaign_state.json');used=used_seconds(ROOT/'artifacts/run_registry.jsonl')/3600
    response=f'''# Review response 001 — exploratory, author review pending

Generated {now}. {completed}/{len(queue)} original stages completed. All {len(frozen['files'])} frozen files pass their hashes. Core state: `{live.get('active_job',{}).get('id',live.get('status'))}`. Recorded reservation time: {used:.6f}/96 hours (a running stage's final duration is not yet known). Rate and dollar cost remain unknown.

The diagnostics were designed after C1 and the available C3 seed-17 result were inspected. Existing-test analyses are exploratory. The original frozen tables, endpoint, seed list, checkpoint choices and exclusions remain intact. No new model call is authorized before all core stages complete and the shared lock is released.

## Findings independently recomputed

{table(findings,['finding','status','observed','review_snapshot'])}

Exact raw paths and SHA256 hashes are in `results/cpu_provenance.json`. Historical mechanism/severity pilots are separate from eligible main evidence; excluded serialization/leakage runs are listed there and retain all artifacts and costs. The 92.74-hour figure is the historical amended forecast, not an updated estimate or consumed time.

## Current completed main evaluations

{table(mainrows,['run_id','paired_successes','families','failed_conversations','failed_with_dependency_error','failed_with_correct_recall','all_canonical_sources_visible'])}

{table(contrasts,['contrast','families','paired_difference','ci95_low','ci95_high'])}

Differences and 95% family-bootstrap intervals above concern one fixed seed only and are exploratory; they do not estimate training-seed variability.

These are recomputations of completed runs, not supplementary model outcomes. Counts do not by themselves establish a C5 benefit or any mechanism. The main primary effect requires the frozen C5 versus C3 seeds and paired hierarchical analysis. C1's better performance than the untrained reference is a clean-training result.

## Supervision and severity

{table(exposure,['run_id','pool','eligible_windows','loaded_unique_windows','loss_contributing_unique_windows','loss_contributing_unique_families','loss_contributing_occurrences','target_tokens','top5_token_share'])}

The CPU token stream reproduces per-step input and supervised-target counts, including orphaned suffix masking and resume-prefix replay. Loading into a buffer is not contributing loss. The C1 round-one small failed pool can create repeated exposure; this is not automatically a useful recovery-diversity increase. Per-process audits distinguish any resumed prefix from new optimization; a future resume chain must be joined to describe final-checkpoint cumulative exposure. Target-token totals need not match despite matched input-token budgets.

Historical severity: C3 flipped 50/243 reference-correct states; C5 flipped 10/241. Those are prior frozen-policy pilot observations, not main estimates. Current main before/after action-error counts in `collection_audit.json` are temporal associations; user updates can intervene. The optional new replay uses common training-only saved inputs and a fresh no-action frozen reference. Its actions were originally generated on different role histories, so it is a same-state action-effect diagnostic, not a matched attack-generation or curriculum correction.

## Goal conflict, routing, memory, and confounding

The original C5 cast owns distinct slots, making its preferred values jointly satisfiable. The final mechanism pilot's 64 delivered antagonist messages produced zero typed matching followups and zero repeated candidates. This does not establish that semantic interaction never occurred; the typed metric can miss useful disclosure and overcount empty echoes. Actual exchanges are prepared for two independent raters; ratings remain pending. Until stronger evidence exists, describe persistent antagonistic personas, without claiming coalitions or substantive rivalry.

Original C4 reserved communications can write notes to Jekyll; C5 prompts messages to another antagonist, although that request is not a hard routing restriction. The final C5 pilot actually sent 10 reserved peer notes to Jekyll and 54 reserved messages to antagonists, plus 10 antagonist messages in direct slots; these are retained, not reclassified as compliant reserved routing. `communication_routing.csv` separates reserved/direct opportunities and actual notes, deliveries, edits, passes and rejected actions. A frozen routing control does not retroactively fix the learned C5−C4 contrast.

471/480 C1 final prompts contain all canonical authorizing sources. Source availability alone does not prove trajectory or memory irrelevance. A0/A1/A2 and the optional common-input reference test different terminal channels; removed assistant evidence and retrieval limits must accompany any interpretation. Similar A0/A2 performance would concern terminal-memory dependence, not establish that earlier memory never mattered.

All 30 ambiguous main-test families are creative and use the held-out conditional rule. This confounds ambiguity, that domain and rule structure. The four domains retain one six-slot schema. Neither the original test nor the optional crossed validation supports broad domain transfer beyond this shared synthetic task.

## Supplementary execution status

{table([{'stage':k,'status':v} for k,v in stages.items()],['stage','status'])}

Separate tables: `memory_dependence.csv`, `replay_agreement.csv`, `paired_contrasts.csv`, `memory_strata.csv`, `goal_conflict.csv`, `routing_control.csv`, `severity_replay.csv`, and `balanced_validation.csv`. Empty tables explicitly have pending/not-executed status; they are not null results. The fixed allocation is made from profiling time only, before examining diagnostic outcomes. All loads, profiling and failed attempts count toward two review GPU-hours within 96; at least 30 minutes remains reserved. Review work precedes the optional unseen-profile supplement.

## Remaining scientific requirements

Core completion status and every diagnostic status are listed above. Any unfinished core stages, unexecuted diagnostics, A0 replay integrity review, genuine human ratings, and author review of scientific arguments and conclusions remain outstanding as applicable. Character-conditioned data generation with supervised adapter training and history-dependent frozen characters is the implemented method. Retrieval is fixed. No demonstrated co-evolution, autonomous exploration, optimized game equilibrium, broad robustness, or conference readiness follows from these audits.
'''
    (HERE/'REVIEW_RESPONSE.md').write_text(response)
    core_note='See original completed core tables; interpretations require author review' if completed==len(queue) else 'Frozen core multi-seed analysis pending'
    claims=[
      ('Improvement over untrained','Eligible clean C1 seed17:186/240 versus67/240; other completed counts shown separately','Clean supervised learning, not character benefit'),
      ('Improvement over clean training',core_note,'Do not infer from C1 learning'),
      ('Improvement over generic adversarial training',core_note,'C3 seed17:177/240 is comparator evidence only'),
      ('Narrative biographies',core_note+'; B3 '+stages['conflict'],'Behavioral B3 does not establish learned-transfer advantage'),
      ('Persistent histories and peer interaction',core_note+'; B2 '+stages['conflict']+'; pilot typed coordination absent','History-dependent characters are not co-evolving policies'),
      ('Memory or trajectory necessary','High terminal source visibility; A0/A1/A2 '+stages['memory'],'Terminal removals cannot prove the full trajectory was unnecessary'),
      ('Rivalry or coalitions','Separate-slot goals compatible; typed pilot matches zero; human semantic audit pending','Withhold strong rivalry/coalition claims'),
      ('Character count','Original routing differs; control '+stages['routing'],'A C5−C4 gain cannot alone isolate count'),
      ('Transfer beyond shared schema','Same six-slot ontology across domains; ambiguity confounded','No broad domain-transfer conclusion')]
    (HERE/'CLAIM_TO_EVIDENCE.md').write_text('# Provisional claims for author review\n\n'+table([dict(zip(['Claim','Evidence','Limit'],r)) for r in claims],['Claim','Evidence','Limit'])+'\n')
    write(RESULTS/'progress.json',{'generated_utc':now,'core_completed':completed,'core_scheduled':len(queue),'core_state':live,
       'frozen_files_verified':len(frozen['files']),'reserved_gpu_hours':used,'supplement_stages':stages,
       'controller':read(ARTIFACTS/'controller_state.json') if (ARTIFACTS/'controller_state.json').exists() else {'status':'implementation_in_progress'},
       'human_annotations':'pending','interpretations':'provisional for author','known_cost_usd':None})
    inputs={}
    for path in sorted(RESULTS.glob('*')):
        if path.is_file() and path.name!='provenance_manifest.json':inputs[str(path.relative_to(ROOT))]=sha256(path)
    for path in [*HERE.glob('*.py'),HERE/'PROTOCOL.md',HERE/'protocol.json',HERE/'fresh_manifest.json',HERE/'FREEZE.json',ARTIFACTS/'bindings.json',ARTIFACTS/'allocation.json']:
        if path.exists():inputs[str(path.relative_to(ROOT))]=sha256(path)
    write(RESULTS/'provenance_manifest.json',{'generated_utc':now,'files':inputs,
       'raw_linkage':'cpu_provenance/exposure_provenance/supplement_provenance contain raw input and checkpoint links; metrics regenerate deterministically from those traces',
       'command':'PYTHONPATH=src .venv/bin/python -m supplements.review_001.regenerate'})


if __name__=='__main__':main()
