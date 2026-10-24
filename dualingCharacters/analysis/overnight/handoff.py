"""Render a timestamped interim or final supervision handoff from audited data."""
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import argparse
import json
import subprocess
from pcc.resources import sha256
from .common import ROOT, OUT, CACHE, read, write, utc


def number(x, digits=2):
    return f'{x:.{digits}f}'


def main(final=False):
    session=read(OUT/'SESSION.json'); live=read(OUT/'LATEST_STATE.json'); start=read(OUT/'STARTING_INVENTORY.json')
    now=datetime.fromisoformat(utc()); begun=datetime.fromisoformat(session['started_utc'].replace('Z','+00:00'))
    zone=ZoneInfo(session['local_timezone']); duration=(now-begun).total_seconds()/3600
    starting_hours=session['start_resource_reconstruction']['cumulative_reserved_seconds_at_session_start']/3600
    core_freeze=read(ROOT/'configs/freeze.json')
    current_hours=live['reconciled_reserved_hours']; before=set(start['completed'])
    new=[name for name in live['completed'] if name not in before]
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    commits=subprocess.check_output(['git','log','--format=%h %s',session['starting_commit']+'..HEAD'],cwd=ROOT,text=True).splitlines()
    dirty=subprocess.check_output(['git','status','--short','--','.'],cwd=ROOT,text=True).splitlines()
    results=read(OUT/'per_seed_results.json'); contrasts=read(OUT/'paired_transitions.json')
    exposures=read(OUT/'supervision_exposure.json'); human=read(OUT/'HUMAN_REVIEW_STATUS.json')
    forecast_detail=read(OUT/'RESOURCE_FORECAST.json')
    waiting=[r['run_id'] for r in forecast_detail['pending'] if r['run_id']!=live['active_job']]
    next_stage=waiting[0] if waiting else None
    retries=read(CACHE/'recovery_attempts.json',{'attempts':[]})
    failures=[]; exclusions=read(ROOT/'configs/run_exclusions.json')
    # Registry/status inspection is small metadata only, never a partially written trace.
    for path in sorted((ROOT/'artifacts/runs').glob('*/status.json')):
        record=read(path,{})
        if record.get('status') in {'failed','interrupted','budget_exceeded'}:
            failures.append({'run_id':path.parent.name,'status':record['status'],'gpu_reserved_seconds':record.get('gpu_reserved_seconds')})
    snapshot={'reported_utc':now.isoformat(),'classification':'Final overnight supervision handoff' if final else 'Active overnight progress snapshot',
      'actual_session_hours':duration,'started_utc':session['started_utc'],'target_handoff_utc':session['target_handoff_utc'],
      'current_source_commit':head,'commits_since_start':commits,'working_tree_changes_at_report_generation':dirty,
      'intentionally_uncommitted_tracked_files':[],
      'commit_note':'Report-generation changes are intended for the following local commit. Active raw artifacts and campaign state remain under the established Git-ignore policy.',
      'new_completed_core_stages':new,'all_completed_core_stages':live['completed'],
      'running_core_stage':live['active_job'],'failed_or_interrupted_attempts':failures,
      'next_scheduled_core_stage':next_stage,'pending_after_active':waiting,
      'overnight_infrastructure_retry_count':len(retries['attempts']),
      'exclusions_manifest':'configs/run_exclusions.json','exclusions_sha256':sha256(ROOT/'configs/run_exclusions.json'),
      'start_reserved_hours':starting_hours,'latest_reserved_hours':current_hours,
      'reserved_hours_during_session':current_hours-starting_hours,'resource_timestamp_utc':live['utc'],
      'core_hashes_verified':live['core_files_verified'],'supplement_hashes_verified':live['supplement_files_verified'],
      'core_scientific_commit':core_freeze['code_commit'],
      'core_freeze_sha256':live['core_freeze_sha256'],'review_freeze_sha256':live['review_freeze_sha256'],
      'retry_manifest':str((CACHE/'recovery_attempts.json').relative_to(ROOT)),
      'gpu_controllers_launched_by_overnight_work':0,'supplement_reserved_hours':live['review_reserved_hours']}
    write(OUT/('HANDOFF_STATE.json' if final else 'PROGRESS_STATE.json'),snapshot)
    lines=['# '+('Overnight report' if final else 'Overnight progress report')+'\n',
      f'Window began **{begun.isoformat()}** ({begun.astimezone(zone).strftime("%Y-%m-%d %H:%M:%S %Z")}). '
      f'This report was generated **{now.isoformat()}** ({now.astimezone(zone).strftime("%Y-%m-%d %H:%M:%S %Z")}), '
      f'after **{duration:.2f} actual hours**. Target handoff: {session["target_handoff_utc"]}. '
      +('The supervision session has ended; the healthy authorized core campaign may continue under its existing controls.' if final else 'The ten-hour supervision session remains active.'),
      '\n## Scientific and operational integrity\n',
      f'All **{live["core_files_verified"]} core** and **{live["supplement_files_verified"]} supplementary** frozen files match. '
      'No scientific file, model, seed, endpoint, training budget, sample allocation, decoding setting, checkpoint rule or queue order was changed. '
      'No duplicate controller or discretionary GPU job was launched. Nothing was pushed, published, submitted or sent to raters. '
      'The new tools perform local analysis and read-only monitoring.\n',
      f'Core scientific source commit: `{core_freeze["code_commit"]}`. '
      f'Core manifest SHA256: `{live["core_freeze_sha256"]}`. '
      f'Review manifest SHA256: `{live["review_freeze_sha256"]}`. '
      '[Final local/remote integrity and ownership check](FINAL_INTEGRITY.json).\n',
      f'Starting commit: `{session["starting_commit"]}`. Source/report HEAD when generated: `{head}`. '
      'The final report commit, if later, is visible in `git log`; a report cannot embed its own eventual commit hash. '
      'No tracked files are intentionally left uncommitted. Active campaign state, raw logs, adapters and checkpoints remain Git ignored and locally mirrored.\n']
    lines.extend('- `'+entry+'`' for entry in commits)
    lines += ['\n## Queue and resources\n',
      f'**{live["core_completed"]}/{live["core_scheduled"]}** scheduled core stages are complete. '
      f'**{len(new)}** completed after the starting inventory. Current stage: `{live["active_job"]}` '
      f'({live["stage_status"]}); {live["generation_requests"]:,} generation requests and {live["training_input_tokens"]:,} training input tokens in the latest stage status. '
      f'Progress snapshot: {live["utc"]}.\n',
      f'Next scheduled stage after the active operation: `{next_stage}`. '
      f'**{len(waiting)}** further stages remain in the unchanged queue. '
      f'Overnight infrastructure retries: **{len(retries["attempts"])}**. '
      'Historical failed/interrupted attempts and scientific exclusions remain recorded in '
      '[the machine-readable state]('+('HANDOFF_STATE.json' if final else 'PROGRESS_STATE.json')+') '
      'and `configs/run_exclusions.json`; they are excluded only under the existing rules, and their compute remains charged.\n',
      'Newly completed stages:\n']
    lines.extend('- `'+name+'`' for name in new)
    forecast=live['forecast'];remote=live.get('remote') or {}
    mirror_age=live.get('mirror_status_age_seconds')
    mirror_text=f'{mirror_age:.1f} seconds' if mirror_age is not None else 'pending first status mirror for this newly started stage'
    remote_space=f'{remote["free_bytes"]/2**30:.2f} GiB' if 'free_bytes' in remote else 'unavailable in this snapshot'
    lines += [f'\nReserved GPU time: **{starting_hours:.4f} h before**, **{current_hours-starting_hours:.4f} h during**, '
      f'**{current_hours:.4f}/96 h cumulative**, with **{96-current_hours:.4f} h remaining** at the snapshot. '
      f'Review consumption: **{live["review_reserved_hours"]:.4f}/2 h** cumulatively. '
      'Start-boundary reconstruction has approximately one-second clock precision. Failed attempts, loading and profiling are charged; utilization does not discount reservations.\n',
      f'The timing-based expected full-core total is **{forecast["expected_total_reserved_hours"]:.2f} h**; '
      f'the conservative timing scenario is **{forecast["conservative_total_reserved_hours"]:.2f} h**. '
      'These are forecasts, not guarantees or permission to shrink the grid. The earlier 92.74 h forecast is preserved separately. '
      'Supplementary work requires all 241 core stages, exact prerequisites, the cumulative two-hour subcap, and at least 30 minutes of contingency plus its existing margin.\n',
      f'Hardware snapshot: {remote.get("gpu","remote snapshot unavailable")}. Local free storage: '
      f'{live["local_free_bytes"]/2**30:.2f} GiB; remote free storage: {remote_space}. '
      f'Mirrored current status age: {mirror_text}. '
      'Completed evaluation trace and adapter mirror checks are in [MIRROR_CHECKS.json](MIRROR_CHECKS.json).\n',
      f'Remote container PID1 start: {remote.get("container_started","unknown")}; '
      f'measured container elapsed seconds: {remote.get("container_elapsed_seconds","not sampled in this snapshot")}. '
      f'Completed-run sampled GPU-busy time: {live["sampled_gpu_busy_hours_completed"]:.3f} h; utilization-weighted samples: '
      f'{live["utilization_weighted_hours_completed"]:.3f} h. These are distinct from reservation time and unknown billed pod uptime. '
      'The actual hourly rate is unavailable; no dollar cost is invented.\n',
      '\n## Main results — incomplete grid\n',
      'Each row is a complete eligible 64-turn evaluation on 240 paired families (480 conversations). '
      'No pilots, partial evaluations or excluded runs enter these estimates. The single untrained reference per model is reused, not independent replication.\n',
      '| Model | Condition | Seed | Paired successes | Conversation successes |', '|---|---|---:|---:|---:|']
    for r in results:lines.append(f'| {r["model"]} | {r["condition"]} | {r["seed"]} | {r["paired_successes"]}/240 | {r["conversation_successes"]}/480 |')
    lines += ['\n| Model | Comparison | Seed | Difference, pp | Exploratory 95% interval, pp | Both / first only / second only / neither |', '|---|---|---:|---:|---:|---:|']
    key=[r for r in contrasts if r['contrast'] in {'C5-C3','C5-C1','C5-C4','C5-A1','C5-A2','C5-A3','C3-C1'}]
    for r in key:lines.append(f'| {r["model"]} | {r["contrast"]} | {r["seed"]} | {100*r["difference"]:.2f} | '
      f'[{100*r["ci95_low"]:.2f}, {100*r["ci95_high"]:.2f}] | {r["both_succeed"]} / {r["only_first"]} / {r["only_second"]} / {r["neither"]} |')
    if not any(r['contrast']=='C5-C3' for r in key):lines.append('| qwen | **C5-C3 primary** | 17 | pending | pending | pending |')
    if not any(r['contrast']=='C5-C1' for r in key):lines.append('| qwen | **C5-C1 clean control** | 17 | pending | pending | pending |')
    lines += ['\nOne-seed intervals resample paired families (10,000 draws, seed 40721); they do not estimate training-seed variation. '
      'An interval containing zero does not establish equivalence. Complete planned three-seed comparisons use the unchanged frozen two-way procedure '
      'and fixed multiplicity family. Interim inspections never change stopping, sampling or checkpoints. '
      '[Interim-look log](INTERIM_LOOKS.jsonl), [complete-seed contrasts](complete_seed_contrasts.json).\n',
      '\n## Exposure, failures and mechanism limits\n',
      f'**{len(exposures)} completed fits** have actual-loss exposure summaries. '
      'The six original verified audits were reused; newly completed fits were reconstructed from the exact tokenizer, sampler and packing stream '
      'and checked against every optimizer-step target count. Buffer-loaded windows, orphan-masked suffixes and resume replay are separately accounted.\n',
      '| Model / condition / seed | Completed fits | Input tokens | Supervised target tokens | R1 recovery windows / families contributing loss |',
      '|---|---:|---:|---:|---:|']
    for r in read(OUT/'curriculum_associations.json'):
        if not r['completed_fits']:continue
        pool=f'{r["r1_recovery_loss_contributing_unique_windows"]} / {r["r1_recovery_loss_contributing_unique_families"]}' if r.get('r1_recovery_loss_contributing_unique_windows') is not None else 'pending'
        lines.append(f'| {r["model"]} / {r["condition"]} / {r["seed"]} | {r["completed_fits"]}/{r["planned_fits"]} | '
          f'{r["training_input_tokens"]:,} | {r["supervised_target_tokens"]:,} | {pool} |')
    lines += ['\nEqual input-token quotas do not equalize target-token exposure. A small repeatedly sampled recovery pool is not a larger set of independent failures; '
      'partial fits in the table are not full condition budgets.\n',
      '[Exposure and curriculum associations](CURRICULUM_ASSOCIATIONS.md) explicitly distinguish common input-token budgets from unequal target exposure. '
      '[Failure taxonomy](failure_taxonomy.csv) uses exclusive categories; [overlap counts](failure_overlaps.csv) retain nonexclusive flags. '
      '[Strata](strata.csv) separate familiar/held-out rules, worlds, framing and ambiguity. '
      'All 30 ambiguous locked families are creative/held-out, and all domains share the same six-slot schema. '
      '[Qualitative examples](QUALITATIVE_APPENDIX.md) are deterministically selected illustrations, not human validation.\n',
      'Training peer matches are typed coordination candidates, not proof of coalitions or hidden intentions. '
      'Temporal action/error associations may include genuine intervening user updates and are not causal attack severity. '
      'Original separate-slot motives can be jointly satisfied; original C4/C5 communication routing differs. '
      'A C5 advantage by itself would not identify biographies, private histories, peer interaction, memory necessity or broad transfer.\n',
      '\n## Unfinished evidence and submission assessment\n',
      'The complete three-seed primary comparison, independent-family trained replication, remaining character-count and history/peer ablations, '
      '32/128-turn sensitivity, larger-memory reference, common-fault recovery, unfamiliar interference, external benchmark, '
      'natural-language validation and human ratings remain required wherever their scheduled cells are pending. '
      'The full ordered list is preserved in the machine-readable state. Horizon and recovery curves must wait for their actual completed inputs; '
      'no values are interpolated from the 64-turn results. The post-review memory and contested-goal diagnostics also remain gated. '
      'The current package supports interim findings and further work, not a complete submission or a guarantee of acceptance.\n',
      '\n## Supplement and human-review status\n',
      f'Review coordinator status: **{live["review_state"].get("status")}**. '
      '[Readiness manifest](SUPPLEMENT_READINESS.json) reports exact pending checkpoints and the full-core gate. '
      'The post-C1 supplementary protocol and selection rules remain frozen. No unavailable memory/mechanism result is inferred.\n',
      'The original 60-item blinded action packet, item identities and private key are preserved; two rating forms remain blank. '
      'The separate 120-output prose packet requires its declared completed natural-language validation outputs. '
      'Missing inputs are listed in [human-review status](HUMAN_REVIEW_STATUS.json); no pilot or other condition is substituted and no ratings are fabricated.\n',
      '\n## Reproducible package and continuation\n',
      '[Figures and captions](FIGURES.md), [training curves](TRAINING_CURVES.md), [compute and gains](COMPUTE.md), '
      '[author-review LaTeX](../../paper/overnight_author_review.tex), [draft status](DRAFT_STATUS.json), '
      '[compiled review PDF](../../paper/overnight_author_review.pdf), [build provenance](PAPER_BUILD.json), '
      '[analysis commands](../../analysis/overnight/README.md), [tests](TESTS.json), '
      '[adapter lineage](ADAPTER_LINEAGE.json), [claim-to-evidence table](CLAIM_TO_EVIDENCE.md), '
      '[provenance](PACKAGE_PROVENANCE.json). Raw traces, adapter weights, optimizer checkpoints and PDF build products remain in the established ignored local mirror. '
      'The paper is incomplete and requires human scientific authorship and review; AI assistance is logged.\n',
      f'Core owner: `{live["processes"].get("core_controller_pid")}`. Review owner: `{live["processes"].get("review_coordinator_pid")}`. '
      f'Remote GPU process snapshot (PID, command): `{remote.get("gpu_processes","unavailable")}`. '
      'Core state/log: `artifacts/campaign_state.json`, `artifacts/campaign_controller.log`; '
      'review state/log: `artifacts/review_001/controller_state.json`, `artifacts/review_001/controller.log`. '
      f'Active stage log: `artifacts/campaign_configs/{live["active_job"]}.log`. '
      'Shared campaign lock: `artifacts/campaign.lock`; GPU lock: `artifacts/gpu.lock`.\n',
      'Run `PYTHONPATH=src .venv/bin/python -m analysis.overnight.monitor` for a read-only live check, '
      'then `PYTHONPATH=src .venv/bin/python -m analysis.overnight.update` to integrate newly completed evidence. '
      'Do not launch another controller. [Recovery instructions](RECOVERY.md) require proving a worker has stopped, preserving artifacts, '
      'using the existing resume map, and allowing at most two retries of the same infrastructure fault. '
      'No scientific redesign is authorized while the author is asleep.\n',
      'Next author decisions, when the relevant evidence is ready: review the bounded scientific interpretations; '
      'arrange two independent raters for the preserved packets; decide whether later work should test incompatible goals, routing and transfer beyond the shared schema. '
      'These are future review decisions, not prerequisites for continuing the already frozen queue.\n']
    (OUT/('OVERNIGHT_REPORT.md' if final else 'PROGRESS_REPORT.md')).write_text('\n'.join(lines))
    # Hash compact sources and outputs; raw evidence hashes live in the linked manifests.
    artifacts={}
    for p in sorted(OUT.rglob('*')):
        if p.is_file() and p.name!='PACKAGE_PROVENANCE.json':artifacts[str(p.relative_to(ROOT))]=sha256(p)
    sources=[*sorted((ROOT/'analysis/overnight').glob('*.py')),ROOT/'analysis/resource_snapshot.py',ROOT/'analysis/execution_report.py']
    provenance={'generated_utc':utc(),'source_commit_at_generation':head,'source_files':{str(p.relative_to(ROOT)):sha256(p) for p in sources},
      'compact_artifacts':artifacts,'raw_evidence_manifests':['evaluation_provenance.json','exposure_provenance.json','collection_provenance.json','MIRROR_CHECKS.json'],
      'classification':'Interim descriptive package; frozen scientific analyses and protocols unchanged'}
    write(OUT/'PACKAGE_PROVENANCE.json',provenance)
    print(json.dumps({'final':final,'actual_hours':duration,'new_completed_stages':len(new),'report':str(OUT.relative_to(ROOT))}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--final',action='store_true');main(p.parse_args().final)
