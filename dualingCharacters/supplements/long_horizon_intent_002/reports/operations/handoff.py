"""Operational handoff assembly only; does not alter any frozen scientific estimator."""
from datetime import datetime,timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import argparse
import json
import subprocess
from pcc.campaign import jobs,resolve_job,load_overrides
from pcc.freeze import verify_freeze
from pcc.resources import sha256,used_seconds
from pcc.eligibility import exclusions
from supplements.long_horizon_intent_002.freeze import verify
from supplements.long_horizon_intent_002.budget import cumulative_extension_seconds
from supplements.review_001.allocation import review_seconds
from supplements.long_horizon_intent_002.common import ROOT,HERE,REPORTS,ARTIFACTS,read,write



def clarification_summary():
    """Render already frozen audit outputs; introduce no new estimator or subset."""
    outcomes={r['seed']:r for r in read(REPORTS/'clarification_audit.json') if r['condition']=='C1' and r['model']=='qwen'}
    exposure={r['seed']:r for r in read(REPORTS/'clarification_exposure.json') if r['condition']=='C1' and r['model']=='qwen' and r['round']==1 and r['pool']=='recovery' and r['clarification_target_class']=='nonempty'}
    lines=['## Clarification and actual exposure', '', '| C1 seed | Original clarification flag /480 | Unnecessary /480 | Nonempty-clarification recovery target tokens | Top-five share |', '|---|---:|---:|---:|---:|']
    for seed in (17,29,43):
        o=outcomes.get(seed);e=exposure.get(seed)
        lines.append(f"| {seed} | {o['clarification_error'] if o else 'Pending'} | {o['unnecessary_clarification'] if o else 'Pending'} | {e['target_tokens'] if e else 'Pending'} | {format(100*e['top5_token_share'],'.1f')+'%' if e else 'Pending'} |")
    lines += ['', 'These target tokens cover whole supervised completions in the nonempty-clarification recovery class, not only the clarification field. Seed-specific exposure and outcomes are descriptive associations. Similar exposure can coexist with different outcomes; these comparisons do not identify a causal explanation for the poor seed. Wrong-issue, missed, duplicate/order-only and settled-null flags remain separate, overlapping audit fields.', '']
    return lines


def main(close=False,early_reason=None):
    frozen=verify();session=read(HERE/'SESSION.json');live=read(REPORTS/'LATEST_STATE.json');start=datetime.fromisoformat(session['started_utc']);now=datetime.now(timezone.utc)
    if close and now<datetime.fromisoformat(session['useful_work_deadline_utc']) and not early_reason:raise PermissionError('Do not close the requested work session early without a genuine documented reason')
    plan=verify_freeze(ROOT)['plan'];queue=[resolve_job(j,load_overrides(ROOT)) for j in jobs(plan)];active=(read(ROOT/'artifacts/campaign_state.json').get('active_job') or {}).get('id')
    complete=[];failed=[];pending=[]
    for job in queue:
        status=read(ROOT/'artifacts/runs'/job['id']/'status.json',{})
        if status.get('status')=='completed' and job['id']!=active:complete.append(job['id'])
        elif status.get('status')=='failed':failed.append(job['id'])
        elif job['id']!=active:pending.append(job['id'])
    initial=read(REPORTS/'STARTING_INVENTORY.json')['completed'];new=[r for r in complete if r not in initial]
    total=live['reconciled_reserved_hours'];baseline=session['start_resource_reconstruction']['cumulative_reserved_seconds_at_session_start']/3600
    commits=subprocess.check_output(['git','log',session['starting_commit']+'..HEAD','--format=%H %s'],cwd=ROOT,text=True).splitlines()
    next_job=next((j['id'] for i,j in enumerate(queue) if i>next((k for k,x in enumerate(queue) if x['id']==active),-1) and j['id'] not in complete),None)
    values={'session_status':'closed' if close else 'in_progress_preview','operational_code_sha256':sha256(Path(__file__)),
      'input_report_hashes':{n:sha256(REPORTS/n) for n in ('LATEST_STATE.json','per_seed_results.json','paired_transitions.json','supervision_exposure.json','MIRROR_CHECKS.json','PROVENANCE.json','clarification_audit.json','clarification_exposure.json','STORAGE_PROJECTION.json')},'started_utc':start.isoformat(),'report_generated_utc':now.isoformat(),
      'ended_utc':now.isoformat() if close else None,'deadline_utc':session['deadline_utc'],'elapsed_seconds_at_report':(now-start).total_seconds(),
      'local_timezone':session['local_timezone'],'started_local':start.astimezone(ZoneInfo(session['local_timezone'])).isoformat(),'reported_local':now.astimezone(ZoneInfo(session['local_timezone'])).isoformat(),
      'starting_commit':session['starting_commit'],'current_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'commits':commits,
      'frozen_files':{'core':58,'review001':21,'intent002':len(frozen['files'])},'all_scientific_hashes_verified':True,'intent_freeze_sha256':sha256(HERE/'FREEZE.json'),
      'core_complete':complete,'completed_without_verified_mirror':sorted(set(complete)-set(read(REPORTS/'MIRROR_CHECKS.json')['runs'])),'new_core_stages':new,'active_core_job':active,'next_scheduled_core_job':next_job,'failed_current_queue_stages':failed,'pending_core_stages':pending,
      'excluded_historical_runs':exclusions(ROOT),'core_controller_pid':session['core_controller_pid'],'review_coordinator_pid':session['review_coordinator_pid'],
      'remote_gpu_processes':live['remote'].get('gpu_processes'),'remote_gpu':live['remote'].get('gpu'),'resource_snapshot_utc':live['utc'],
      'reserved_hours_before_session':baseline,'reconciled_reserved_hours_at_snapshot':total,'reserved_hours_during_session_to_snapshot':total-baseline,
      'review_reserved_hours':review_seconds()/3600,'intent_reserved_hours':cumulative_extension_seconds(ROOT/'artifacts/run_registry.jsonl')/3600,
      'remaining_overall_hours':96-total,'remaining_after_contingency_hours':95.5-total,'forecast':live['forecast'],
      'container_elapsed_seconds':live['remote'].get('container_elapsed_seconds'),'pod_elapsed_seconds':None,
      'pod_elapsed_qualification':'Container uptime is the available operational proxy; actual pod provisioning and billing duration were not independently established.','known_dollar_cost':None,
      'new_gpu_extension_enabled':False,'new_gpu_extension_waiter_installed':False,'core_may_continue_under_original_controls':True,
      'early_stop_reason':early_reason,'infrastructure_retries_this_session':0,
      'new_qualitative_scores':read(REPORTS/'INTENT_SCORES.json')['status'],'human_status':read(REPORTS/'HUMAN_REVIEW_STATUS.json')['status']}
    if close:
        # Disable only the new extension; do not signal core/review or terminate the pod.
        write(ARTIFACTS/'activation.json',{'enabled':False,'session_id':session['session_id'],'closed_utc':now.isoformat(),'reason':'Eight-hour continuation ended; unexecuted intent work requires a subsequent authorized session'})
        priority=read(ROOT/'artifacts/optional_priority.json');priority.update(intent_002_enabled=False,intent_002_resolved=False,intent_session_closed_utc=now.isoformat())
        write(ROOT/'artifacts/optional_priority.json',priority);write(REPORTS/'OPTIONAL_PRIORITY.json',priority)
    write(REPORTS/'HANDOFF_STATE.json',values)
    results=read(REPORTS/'per_seed_results.json');contrasts=read(REPORTS/'paired_transitions.json')
    lines=['# Intent 002 session handoff' if close else '# Intent 002 handoff preview — session still active','',
      f'Start: {start.isoformat()} ({values["started_local"]}). '+(f'End: {now.isoformat()} ({values["reported_local"]}).' if close else f'Preview: {now.isoformat()}; work continues until the recorded deadline.'),
      f'Actual elapsed at report: {(now-start).total_seconds()/3600:.3f} hours. One shared deadline: {session["deadline_utc"]}.', '',
      f'Commit at report generation: `{values["current_commit"]}`; starting commit `{session["starting_commit"]}`. Nothing pushed, published or submitted. All 58 core, 21 review and {len(frozen["files"])} intent scientific files verify unchanged.','',
      f'Core: {len(complete)}/241 stages complete, {len(new)} newly completed this session. Active: `{active}`. Next: `{next_job}`. Current failed queue stages: {len(failed)}. Historical excluded artifacts remain preserved and listed in HANDOFF_STATE.json. No infrastructure retries were needed.','',
      'The final commit containing this handoff can be identified with `git log -1 --format=%H -- dualingCharacters/supplements/long_horizon_intent_002/reports/SESSION_REPORT.md` from the repository root. The generation-time commit above intentionally precedes that reporting commit.','',
      f'Completed stages awaiting the independent mirror audit: {values["completed_without_verified_mirror"]}. Tables below include only evaluations that passed completed-run validation; a newly completed but unaudited stage is not silently added.','',
      '## Current core evidence — interim until planned seed sets complete','',
      '| Model | Condition | Seed | Paired success /240 |','|---|---|---:|---:|']
    lines += [f'| {r["model"]} | {r["condition"]} | {r["seed"]} | {r["paired_successes"]} |' for r in results]
    lines += ['','| Contrast | Seed | Difference, pp | Family 95% interval, pp | Both / only C5 / only control / neither |','|---|---:|---:|---|---|']
    for r in contrasts:
        if r['model']=='qwen' and r['contrast'] in ('C5-C3','C5-C1'):
            lines.append(f'| {r["contrast"]} | {r["seed"]} | {100*r["difference"]:.2f} | [{100*r["ci95_low"]:.2f}, {100*r["ci95_high"]:.2f}] | {r["both_succeed"]} / {r["only_first"]} / {r["only_second"]} / {r["neither"]} |')
    lines += ['', 'These one-seed intervals preserve paired scenario families; they do not represent training-seed uncertainty or equivalence. Complete-seed frozen analysis is retained in the original tables and `complete_seed_contrasts.json`. Do not average unmatched seed sets to create a contrast.','',
      '## New evidence and unfinished requirements','',
      f'{len(read(REPORTS/"supervision_exposure.json"))} fits have exact loss-exposure reconstruction. See [progress](PROGRESS_REPORT.md), [clarification/source audits](clarification_audit.csv), [temporal source audit](source_dynamics_selected_turns.csv), [illustrations](ILLUSTRATIVE_APPENDIX.md), and [claims](CLAIM_TO_EVIDENCE.md).',
      'The existing horizon interaction is pending its actual 32/128-turn runs. Dynamic 64-turn analyses retain initial failures and show that final correctness can coexist with substantial intermediate reversion; source access changes with scripted requests. These are exploratory associations, not causal memory/retrieval effects.',
      'Fresh intent inference, timing allocation, GPU validation of the natural-language interface, and human ratings remain pending. The 16-family benchmark, disjoint engineering cases, private ledgers, balanced tiers, common runner, scoring/blinding and deadline controls are implemented and frozen. No new qualitative performance, crossover or robustness benefit is claimed.','',
      '## Resource reconciliation','',
      f'Before session: {baseline:.4f} reserved GPU-hours. During session through {live["utc"]}: {total-baseline:.4f} hours. Cumulative: {total:.4f}/96; remaining: {96-total:.4f}; after 0.5-hour contingency: {95.5-total:.4f}. Review supplement: {values["review_reserved_hours"]:.4f}/2; intent extension: {values["intent_reserved_hours"]:.4f}/2.',
      f'Core forecast total: expected {live["forecast"]["expected_total_reserved_hours"]:.2f}, conservative {live["forecast"]["conservative_total_reserved_hours"]:.2f} reserved hours. This is a forecast, not permission to shrink cells or spend beyond 96 hours. Container elapsed: {values["container_elapsed_seconds"]} seconds at snapshot; this available proxy is separate from reserved GPU time and sampled utilization. Actual pod provisioning and billing duration are unverified. Actual dollar rate is unknown.', '',
      '## Human review and paper package','',
      'The original 60-action packet is preserved; actual annotation counts are in LEGACY_HUMAN_PACKET_STATUS.json. The original 120-prose packet awaits its required natural-language runs. The intent packet is separate and awaits actual outputs; no items or human ratings were fabricated and no raters were contacted.',
      '[Figures](INTENT_FIGURES.md) · [author-review manuscript section](../MANUSCRIPT_SECTION.md) · [compiled draft](draft/intent_author_review.pdf) · [provenance](PROVENANCE.json) · [reproduction](../README.md). This is incomplete evidence and an author-review draft, not a complete submission or acceptance guarantee.','',
      '## Ownership and recovery','',
      f'Core controller PID {session["core_controller_pid"]}; review coordinator PID {session["review_coordinator_pid"]}. Current remote GPU processes: `{values["remote_gpu_processes"]}`. The healthy core continues separately under its original authorization; it was not stopped to end this session.',
      'Core state/log: `artifacts/campaign_state.json`, `artifacts/campaign_controller.log`, `artifacts/campaign_configs/<run_id>.log`. Core ownership lock: `artifacts/campaign.lock`; remote GPU lock: `artifacts/gpu.lock`. Review state: `artifacts/review_001/controller_state.json`. Intent is disabled, with no new background waiter. Older optional work remains behind its unresolved priority guard.',
      'Read-only check: `PYTHONPATH=src .venv/bin/python -m supplements.long_horizon_intent_002.operations monitor`. Integrate completed evidence: `PYTHONPATH=src .venv/bin/python -m supplements.long_horizon_intent_002.regenerate`. Verify mirrors: `PYTHONPATH=src .venv/bin/python -m supplements.long_horizon_intent_002.operations mirror`.',
      'For infrastructure recovery, first prove both original controller and GPU worker stopped; a dropped SSH connection is insufficient. Preserve/mirror partials and resource records, use the original `artifacts/campaign_resume.json` aliases and valid atomic optimizer checkpoint where supported, and allow at most two retries of the same infrastructure fault. Never rerun a completed evaluation for a different score. See the unchanged [recovery procedure](../../../reports/overnight_20261024T023622Z/RECOVERY.md). Scientific defects require a documented safe-boundary hold and preserved originals.','',
      '## Next author decisions','',
      'No routine decision is needed for the healthy original core queue. Later review: (1) assess the narrower claims supported by seed variation, intermediate reversion and source access; (2) review the authored intent ledgers/rubric and authorize a later execution window if desired, retaining existing GPU caps; (3) arrange independent human raters once the required outputs exist. No permission is inferred from elapsed time.']
    position=lines.index('## Resource reconciliation');lines[position:position]=clarification_summary()
    storage=read(REPORTS/'STORAGE_PROJECTION.json');position=lines.index('## Human review and paper package')
    lines[position:position]=[f"Storage at its {storage['monitor_utc']} snapshot: local {storage['local_free_bytes']/2**30:.2f} GiB, remote {storage['remote_free_bytes']/2**30:.2f} GiB free. Remaining-fit size projection {storage['remaining_fit_size_projection_bytes']/2**30:.2f} GiB excludes future traces and temporary writes; this is not guaranteed capacity or cleanup authorization. See [storage projection](STORAGE_PROJECTION.json). No artifacts were deleted.",'']
    if early_reason:lines+=['','Early-stop reason: '+early_reason]
    (REPORTS/('SESSION_REPORT.md' if close else 'HANDOFF_PREVIEW.md')).write_text('\n'.join(lines)+'\n')
    print({'status':values['session_status'],'elapsed_hours':(now-start).total_seconds()/3600,'completed_core':len(complete),'new_stages':len(new),'active_core':active})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--close-session',action='store_true');p.add_argument('--early-reason');a=p.parse_args();main(a.close_session,a.early_reason)
