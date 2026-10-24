"""Generate reviewable text only from completed machine-readable evidence."""
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import statistics
import subprocess
from pcc.resources import sha256
from .common import ROOT,HERE,REPORTS,ARTIFACTS,read,write,utc


def pct(value):return f'{100*value:.2f}'


def md_table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join('---' for _ in headers)+'|',*['| '+' | '.join(map(str,row))+' |' for row in rows]])


def main():
    results=read(REPORTS/'per_seed_results.json');transitions=read(REPORTS/'paired_transitions.json');clarify=read(REPORTS/'clarification_audit.json');evidence=read(REPORTS/'evidence_audit.json');exposure=read(REPORTS/'clarification_exposure.json');trajectory=read(REPORTS/'trajectory_summary.json');contrasts=read(REPORTS/'paired_trajectory_contrasts.json')
    session=read(HERE/'SESSION.json');live=read(REPORTS/'LATEST_STATE.json');ready=read(REPORTS/'INTENT_READINESS.json');human=read(REPORTS/'HUMAN_REVIEW_STATUS.json');scores=read(REPORTS/'INTENT_SCORES.json');horizons=read(REPORTS/'core_horizon_levels.json');supervision=read(REPORTS/'supervision_exposure.json');pools=read(REPORTS/'supervision_pools.json')
    dynamics=read(REPORTS/'source_dynamics_selected_turns.json');situations=read(REPORTS/'clarification_training_situations.json')
    lookup={(r['model'],r['condition'],r['seed']):r for r in results}
    rows=[]
    for seed in (17,29,43):
        for method in ('C1','C3','C4','C5','A1'):
            r=lookup.get(('qwen',method,seed));rows.append([seed,method,f'{r["paired_successes"]}/240 ({pct(r["paired_success"])}%)' if r else 'Pending'])
    main_table=md_table(['Qwen seed','Condition','64-turn paired success'],rows)
    key=[r for r in transitions if r['model']=='qwen' and r['contrast'] in ('C5-C3','C5-C1')]
    contrast_table=md_table(['Contrast','Seed','Difference, pp','Family 95% interval, pp','Both','Only C5','Only control','Neither'],[
      [r['contrast'],r['seed'],pct(r['difference']),f'[{pct(r["ci95_low"])}, {pct(r["ci95_high"])}]',r['both_succeed'],r['only_first'],r['only_second'],r['neither']] for r in key])
    matching_seeds=[s for s in (17,29,43) if all(('qwen',c,s) in lookup for c in ('C1','C3','C5'))]
    seed_description=[]
    if matching_seeds:
        for c in ('C1','C3','C5'):
            values=[lookup['qwen',c,s]['paired_success'] for s in matching_seeds]
            seed_description.append({'condition':c,'matched_seeds':matching_seeds,'values':values,'mean':statistics.mean(values),'range':max(values)-min(values),'sample_sd':statistics.stdev(values) if len(values)>1 else None,
              'qualification':'Descriptive across the same completed seeds; not population training robustness, drift, or horizon interaction. Three seeds still provide limited variation evidence.'})
    write(REPORTS/'matched_seed_description.json',seed_description)
    clarification_table=md_table(['Condition','Seed','Original flag /480','Unnecessary','Missed necessary','Wrong issue','Unnecessary + settled nulls'],[
      [r['condition'],r['seed'],r['clarification_error'],r['unnecessary_clarification'],r['missed_necessary_clarification'],r['wrong_issue_clarification'],r['unnecessary_clarification_with_settled_nulls']] for r in clarify if r['model']=='qwen' and r['condition'] in ('C1','C3','C5')])
    evidence_table=md_table(['Condition','Seed','Original source error /480','Canonical mismatch /2880','Assistant /2880','Unavailable /2880','Nonexistent/future /2880','Wrong explicit user /2880','Anaphoric /2880'],[
      [r['condition'],r['seed'],r['original_source_error_conversations'],r['canonical_mismatch_references'],r['assistant_authority_references'],r['not_visible_references'],r['nonexistent_or_future_references'],r['wrong_explicit_user_authorization_references'],r['anaphoric_user_reaffirmation_needs_semantic_review_references']] for r in evidence if r['model']=='qwen' and r['condition'] in ('C1','C3','C5')])
    exposure_table=md_table(['Condition','Seed','Round','Nonempty recovery pool','Loss-contributing unique','Occurrences','Completion target tokens','Top-5 share'],[
      [r['condition'],r['seed'],r['round'],r['eligible_examples'],r['loss_contributing_unique_examples'],r['contributing_occurrences'],r['target_tokens'],f'{100*r["top5_token_share"]:.1f}%' if r['top5_token_share'] is not None else 'N/A'] for r in exposure if r['model']=='qwen' and r['condition'] in ('C1','C3','C5') and r['pool']=='recovery' and r['clarification_target_class']=='nonempty'])
    trajectory_table=md_table(['Condition','Seed','All-turn correctness','Final-quarter correctness','Never correct /480','Unresolved final /480'],[
      [r['condition'],r['seed'],pct(r['mean_all_turn_success'])+'%',pct(r['mean_final_quarter_success'])+'%',r['never_aligned'],480-r['final_correct']] for r in trajectory if r['model']=='qwen' and r['condition'] in ('C1','C3','C5')])
    trajectory_contrast_table=md_table(['Contrast','Seed','Mean all-turn difference, pp','Family 95% interval, pp'],[
      [r['contrast'],r['seed'],pct(r['difference']),f'[{pct(r["ci95_low"])}, {pct(r["ci95_high"])}]'] for r in contrasts if r['metric']=='mean_world_all_turn_success'])
    source_time_table=md_table(['Condition','Seed','Turn','All canonical sources /480','Correct incoming memory /480','Reverted to initial state /480','Task correct /480'],[
      [r['condition'],r['seed'],r['turn'],r['all_canonical_visible'],r['memory_correct_for_current_truth'],r['stale_initial_state_returned'],r['success']] for r in dynamics if r['turn'] in (60,61)])
    ambiguity_domains=sorted({r['domain'] for r in situations if r['case']=='necessary_clarification' and r['supervised_target_tokens']})
    claim_rows=[
      ['Improvement over untrained Qwen','Completed seed-specific core results; untrained 67/240 is one shared reference.','Structured six-slot planning only; no independent replication from reference reuse.'],
      ['Practical advantage over clean training','C5–C1 reverses direction between seeds17 and29; retain both.','Full three-seed contrast and independent-family replication remain necessary.'],
      ['Advantage over generic adversaries','C5–C3 is negative at the two currently completed matched seeds; intervals are family-only.','No demonstrated character-specific superiority from current main evidence.'],
      ['Reduced deterioration with length','32/64/128 semantic matching verified for48 families; only64-turn cells currently available.','Horizon interaction and absolute128-turn comparison pending.'],
      ['Trajectory preservation or recovery','All 64 turns rescored against dynamic truth; unconditional and never-correct cases retained.','Endogenous states differ; no causal recovery claim or prose-intent validation.'],
      ['Training-seed robustness','Same completed seed sets described separately, with values/range/SD.','Few seeds; not evidence of conversational drift or a seed-population property.'],
      ['Narrative profiles, history, peer relations','Original ablations remain intact; A1 available as shown in main tables.','No stronger mechanism claim without completed ablations and review diagnostics.'],
      ['Explicit memory or trajectory necessity','review_001 terminal ablations retain priority and are pending.','Terminal replay cannot by itself establish earlier trajectory irrelevance.'],
      ['Transfer beyond six-slot schema','Fresh16-family natural-language benchmark and common interface implemented.','No fresh outputs or human scores yet; authored synthetic tasks, not real users.'],
      ['Source-reference reliability','Structural reference categories and deterministic examples separate roles/availability/canonical mismatch.','Anaphoric support requires semantic review; original scorer unchanged.']]
    claims=md_table(['Claim','Available evidence','Limit'],claim_rows)
    (REPORTS/'CLAIM_TO_EVIDENCE.md').write_text('# Provisional claim-to-evidence table\n\n'+claims+'\n\nInterpretations require author review; no conference acceptance or submission-readiness claim.\n')
    text=[f'# Intent 002 progress — {utc()}','',
      'This is an exploratory follow-up specified after the initial negative C5 comparison and C1 seed reversal. It preserves the original confirmatory study and review_001 freezes. Newly inspected test analyses are not original preregistration.','',
      f'Session: {session["started_utc"]} to {session["deadline_utc"]}; useful-work cutoff {session["useful_work_deadline_utc"]}. The single elapsed-time budget is eight hours. No intent worker is left waiting to launch after that deadline.','',
      '## Existing core: completed and running','',f'Latest monitor {live["utc"]}: {live["core_completed"]}/241 stages complete; active `{live["active_job"]}`. The existing controller retains ownership. Results below contain only completed, eligible, fully validated paired evaluations.','',main_table,'',contrast_table,'',
      'One-seed intervals resample240 scenario families, preserving both worlds. They exclude training-seed uncertainty. A zero-containing interval is not equivalence. The frozen three-seed procedure and multiplicity treatment are retained for completed planned seed sets. C5–C1 remains alongside C5–C3; no favorable seed or checkpoint is selected.','',
      '## Different robustness questions','',
      f'Horizon robustness: {sum(r["status"]=="completed" for r in horizons)}/15 existing model/horizon cells complete, including base and C4. The48 family identities preserve decision/event semantics across32/64/128; early events are not uniformly phase-scaled. Missing short/long cells prevent the proposed interaction estimate. A128-turn prefix is not a32-turn experiment.','',
      'Trajectory robustness: the table uses all480 conversations at every actual turn against its current oracle. These are structured decisions, not human-rated natural-language intent or helpfulness.', '',trajectory_table,'',trajectory_contrast_table,'',
      'C5 does not exhibit a consistent trajectory advantage in these completed seeds. Endogenous error episodes cannot substitute for the frozen identical-faulty-state recovery experiment. Initially incorrect and never-correct conversations remain in unconditional denominators.','',
      'A temporal source audit was added after inspecting these curves. It characterizes saved prompts after generation; no gold annotation selected the policy inputs. The following comparison illustrates a late recovery of source access, with no claim that source access alone caused the behavioral change.','',source_time_table,'',
      'At these tested turns, later explicit requests can retrieve current authorizing messages that ordinary intervening requests omit. A strong final response therefore does not establish preservation throughout the trajectory. The fixed lowest-ID paired example and complete source-coverage curves are saved under the source-dynamics audit; no retriever or memory rule was changed.','',
      'Training robustness: `matched_seed_description.json` uses only seeds shared by C1/C3/C5. Values, range, and sample SD are descriptive; they neither establish a population robustness property nor conversational stability. Flat low performance is not useful robustness.','',
      '## Clarification and source-reference audits','',clarification_table,'',
      'Clarification flags overlap. Wrong-issue cases can be both unnecessary and missed. Settled-decision nulling is a structured behavioral proxy for abandoning executable work, not a judgment about hidden intention or prose acknowledgment of uncertainty. Duplicate/order-only flags remain separate in the machine table.','',evidence_table,'',
      'Reference counts have2880 slot references, while the original source-error denominator is480 conversations. Categories overlap. Unavailable references are distinct from nonexistent references and assistant authorship. Possible anaphoric user support is not automatically rescored. Actual examples and canonical source spans appear in `semantic_source_examples.json`.','',
      '## Actual supervised exposure','',f'{len(supervision)} completed fits have exact loss-mask and sampler reconstruction. Common input-token budgets do not imply equal supervised-target tokens, example diversity, or recovery exposure.', '',exposure_table,'',
      'These target tokens count whole supervised completions in the nonempty-clarification class, not just the clarification field. Unique loss-contributing examples, repeated occurrences, orphaned suffix masking, and resume replay are separate. Full teacher-versus-verified-recovery label totals are in `supervision_exposure.json`; loaded buffer contents are not counted as loss exposure. Curriculum/outcome associations are noncausal.','',
      'All currently loss-contributing necessary-clarification targets come from these original training domains: '+', '.join(ambiguity_domains)+'. Their exact turn, event type, label source, family IDs, and largest repeated-example shares are in `clarification_training_situations.json` and `clarification_top_examples.json`. This original training confound is retained; the fresh benchmark crosses ambiguity with all four domains.','',
      '## Fresh qualitative benchmark and execution readiness','',
      'Sixteen authored families (four per practical domain), paired authorization worlds, and matched16/64/128-turn scripts are implemented with private time-indexed ledgers and exact user-source spans. Four disjoint engineering cases test the common response/free-text-memory interface. The16-phase event template is controlled but synthetic and structurally limited.','',
      'The shared public interface uses4096 input tokens,640 combined output tokens,128 memory tokens, fixed lexical retrieval8 plus4 recent messages, greedy BF16 inference and batch limit32. The policy alone writes memory; evaluator state and corrections never enter its prompts. Offline tokenizer checks are not GPU validation of this transfer interface.','',
      f'Fresh score status: **{scores["status"]}**. Intent reserved GPU time: {ready["intent_seconds_used"]:.1f} seconds. Admission reasons: {", ".join(ready["reasons"])}. No qualitative performance result, crossover, or new robustness advantage is claimed.', '',
      f'Human status: {human["status"]}. Two independent rating forms remain blank until actual humans provide ratings. The complete grid and balanced sample are different workloads. Earlier60-action identities/forms remain preserved; the original120-prose packet awaits its required natural outputs. No one was contacted.','',
      '## Resources and next action','',
      f'Latest reconciled project reservation: {live["reconciled_reserved_hours"]:.4f}/96hours. Core forecast: expected {live["forecast"]["expected_total_reserved_hours"]:.2f}, conservative {live["forecast"]["conservative_total_reserved_hours"]:.2f} total reserved hours. Review and intent each have separate cumulative2-hour subcaps within96; at least0.5hours contingency is retained. These forecasts are not guarantees. Pod elapsed time and sampled utilization are recorded separately in `LATEST_STATE.json`; actual dollar rate remains unknown.', '',
      'Required core → review_001 → intent_002 → older unseen-profile work. This session does not expand the96-hour ceiling. New intent work requires the completed core and review gates, a fixed-final-checkpoint binding, timing-only complete-tier allocation, free shared locks, remaining allowance, and this session’s deadline. If gates stay closed, leave intent disabled for a subsequent authorized continuation.', '',
      '## Reviewable package','',
      '[Figures](INTENT_FIGURES.md), [claims](CLAIM_TO_EVIDENCE.md), [illustrative core appendix](ILLUSTRATIVE_APPENDIX.md), [new protocol](../PROTOCOL.md), [dataset card](../DATASET_CARD.md), [rubric](../RUBRIC.md), [reproduction](../README.md). No manuscript is presented as a compliant finished submission; scientific arguments and conclusions require human author review.']
    (REPORTS/'PROGRESS_REPORT.md').write_text('\n'.join(text)+'\n')
    section=['# Exploratory follow-up: long-horizon intent robustness','',
      'This section is an author-review draft. The direction was specified after observing a negative initial three-character comparison and a reversal in clean-training performance across seeds. It is separate from the original confirmatory protocol.','',
      'We distinguish horizon robustness (change with conversation length), trajectory robustness (correct application and recovery throughout a conversation), and training robustness (variation between independent training seeds). Lower deterioration from a poor starting point does not establish useful robustness. We operationalize intent as goals, priorities, constraints, permissions, and revisions expressed in the available conversation, without claiming access to unexpressed human intentions.','',
      'The underlying intervention is character-conditioned data generation followed by supervised adapter training. Character-generator parameters are frozen; their private histories make behavior history-dependent. Retrieval is fixed, and primary evaluation removes antagonists. The method does not implement co-evolving character policies, autonomous exploration, or an optimized game-theoretic equilibrium.','',
      '## Existing-core observations','',main_table,'',contrast_table,'',
      'At the current incomplete grid, the C5-versus-clean comparison changes direction between seeds17 and29. The corresponding C5-versus-generic-adversary differences are negative at both completed seeds. These single-seed family intervals neither establish equivalence nor quantify variation over training seeds. The untrained reference is shared, not replicated for each comparison.','',
      'Dynamic-oracle analysis scores each actual64-turn response against the then-active task state, keeping initial errors, authorized changes, ambiguous requests, and regressions distinct.', '',trajectory_table,'',trajectory_contrast_table,'',
      'The complete32/64/128 horizon grid is pending. Consequently, the newly proposed method-by-horizon interaction and absolute128-turn differences have not been measured. Existing trajectory associations do not establish causal recovery from matched disrupted states.','',
      'A subsequent temporal source audit found that source coverage changes strongly with the scripted current request. The following selected-turn counts are descriptive and do not identify a causal effect of retrieval.', '',source_time_table,'',
      'Several adapters repeatedly returned initial commitments during the intervening period, then recovered approved revisions when their sources reappeared. A flat incorrect trajectory is not stability, and final-turn accuracy alone is not long-horizon preservation. The policy and benchmark remain frozen.','',
      '## Fresh intent-transfer design, pending execution','',
      'We prepared16 authored scenario families across software/product work, research collaboration, editorial work, and operator assistance. Each has two authorization worlds and16-,64-,128-turn versions, preserving decisive events while adding supporting task work. Outputs are substantive proposals, research-plan paragraphs, edited passages, or operational recommendations. A private time-indexed intent ledger grounds evaluator judgments in visible user spans and allows multiple valid responses. It is never passed to the policy or used for retrieval.','',
      'All fixed final Qwen C1/C3/C5 adapters use one common natural-language response and bounded free-text-memory interface. This differs from their structured training interface and is therefore a transfer limitation to test, not hide. Feasible complete tiers are selected only from disjoint engineering timing under the separate two-hour subcap, core/review priority, project96-hour ceiling, and single session deadline. No new parameter training is performed.','',
      'The new primary endpoint normalizes0–4 adherence ratings, averages the final three observations within each world, takes the lower paired-world average within family, and then averages matched families and declared seeds. The primary contrast is the C5-versus-C3 difference in128-minus16 change; C5-versus-C1 and absolute128-turn performance are mandatory practical comparisons. Helpful task progress is rated separately. Human ratings, disagreement, and any adjudication remain distinct. No model-generated or synthetic annotation is presented as human validation.','',
      '## Limits and provisional interpretation','',
      'The original benchmark shares a six-slot schema across domain framings, and its ambiguous families are confounded with the creative domain and held-out rule. The new benchmark introduces free-text artifacts but still uses authored scripts and a common16-phase skeleton. Longer trajectories under fixed retrieval are not full-transcript attention tests. Few training seeds provide limited uncertainty about seed variation. Supervised target exposure and recovery concentration can differ despite common input-token budgets; observed associations do not identify their causal effects.','',
      'Fresh qualitative scores remain pending. A future positive interaction with lower absolute128-turn performance would support reduced degradation at these tested horizons, not superior long-horizon usefulness. No advantage would remain evidence about these fixed adapters and the specified interface. Narrative, persistence, rivalry, and peer-interaction explanations require their own controls. All scientific interpretations remain provisional for the human author.']
    (HERE/'MANUSCRIPT_SECTION.md').write_text('\n'.join(section)+'\n')
    inputs=['per_seed_results.json','paired_transitions.json','clarification_audit.json','evidence_audit.json','clarification_exposure.json','trajectory_summary.json','paired_trajectory_contrasts.json','core_horizon_levels.json','supervision_exposure.json','HUMAN_REVIEW_STATUS.json','INTENT_SCORES.json','LATEST_STATE.json','source_dynamics_selected_turns.json','clarification_training_situations.json']
    write(REPORTS/'TEXT_PROVENANCE.json',{'generated_utc':utc(),'inputs':{str((REPORTS/name).relative_to(ROOT)):sha256(REPORTS/name) for name in inputs},'generator_sha256':sha256(Path(__file__)),
      'outputs':{str(p.relative_to(ROOT)):sha256(p) for p in [REPORTS/'PROGRESS_REPORT.md',REPORTS/'CLAIM_TO_EVIDENCE.md',HERE/'MANUSCRIPT_SECTION.md']},'scientific_interpretations':'Provisional author review; no fresh qualitative scores unless explicitly measured in INTENT_SCORES.json'})
    print({'core_evaluations':len(results),'intent_scores_status':scores['status'],'manuscript_section':'author_review_only'})


if __name__=='__main__':main()
