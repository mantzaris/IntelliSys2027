"""Factual author-review report from saved analysis; no new scientific estimator."""
from collections import Counter
from pathlib import Path
import json
from pcc.campaign import jobs, load_overrides, resolve_job
from pcc.freeze import verify_freeze
from pcc.resources import sha256


def effect_text(row: dict | None) -> str:
    if row is None:
        return 'Pending: no complete matched three-seed contrast is available.'
    return (f"{100*row['difference']:+.2f} percentage points; 95% paired seed/family interval "
            f"[{100*row['ci95'][0]:+.2f}, {100*row['ci95'][1]:+.2f}], "
            f"{row['families']} scenario families and {row['seeds']} training seeds. "
            'Three seeds provide limited information about training-seed variability.')


def assessment(core_complete: bool, primary: dict | None) -> str:
    if not core_complete:
        return 'Further execution is required. This is an incomplete evidence package, not a submission-ready paper.'
    if primary is None:
        return 'The scheduled stages are complete but the primary contrast is unavailable; the analysis requires audit before a paper can be assessed.'
    lo, hi = primary['ci95']
    if hi < 0:
        conclusion = 'The primary interval favors generic adversarial training over the three-character method. Preserve the negative finding; it does not support the proposed advantage.'
    elif lo <= 0:
        conclusion = 'The primary interval includes zero. The proposed advantage is not established, and the limited precision does not establish equivalence or absence of a practically meaningful effect.'
    else:
        conclusion = 'The primary interval lies above zero in this controlled benchmark. Persistence, interaction, narrative and independent-family claims still require their own controls and validity assessment.'
    return conclusion + ' A narrower empirical paper may be considered after author review of novelty, limitations and all controls. Human scientific authorship and pending human validation prevent treating this generated package as a compliant finished submission.'


def generate(root: Path) -> dict:
    frozen = verify_freeze(root)
    inputs = {'configs/freeze.json': sha256(root/'configs/freeze.json')}
    def read(path: str, default):
        source = root/path
        if not source.exists():
            return default
        inputs[path] = sha256(source)
        return json.loads(source.read_text())
    overrides = load_overrides(root)
    stage_rows = []
    for original in jobs(frozen['plan']):
        job = resolve_job(original, overrides)
        status = read(f"artifacts/runs/{job['id']}/status.json", {})
        stage_rows.append({'id': job['id'], 'command': job['command'],
                           'status': status.get('status', 'not_started')})
    completed = sum(row['status'] == 'completed' for row in stage_rows)
    pending = [row for row in stage_rows if row['status'] != 'completed']
    core_complete = not pending
    main = read('reports/tables/main_results.json', [])
    effects = read('reports/tables/main_contrasts.json', [])
    # This report may be refreshed independently of the expensive full package.
    # Recompute only small metadata so current outcomes never accompany stale costs.
    from resource_snapshot import snapshot
    snapshot(root)
    resource = read('reports/tables/resource_totals.json', {})
    transfer = read('reports/tables/transfer.json', [])
    external = read('reports/tables/external.json', [])
    human = read('reports/tables/human_review_status.json', {})
    supplemental = read('artifacts/unseen_profiles_controller_state.json', {})
    primary = next((row for row in effects if row['model'] == 'qwen' and
                    row['contrast'] == 'C5-C3' and row['seeds'] == 3), None)
    replication = next((row for row in effects if row['model'] == 'phi' and
                        row['contrast'] == 'C5-C3' and row['seeds'] == 3), None)
    lines = ['# Execution and evidence report — author review required', '',
             'Generated from saved run records and existing deterministic analyses. Scheduled jobs are not counted as observations. No submission or publication has occurred.', '',
             '## 1. What ran', '',
             f'{completed}/{len(stage_rows)} eligible scheduled core stages have completed. Stage counts include collection, fitting, evaluation and validation; they are not independent trained models.', '',
             'Hardware: one existing RunPod NVIDIA RTX 6000 Ada, 49,140 MiB reported VRAM; PyTorch 2.8.0+cu128, CUDA 12.8 and driver 595.91.07. Hardware inspection is recorded in `RUN_STATE.md`. BF16 rank-8 LoRA performs actual parameter updates; vLLM inference shares the backbone across role contexts.', '']
    if resource:
        lines.append(f"Recorded project consumption: {resource['reserved_gpu_hours']:.3f}/96 reserved GPU-hours, including failed and excluded attempts; {resource['inference_input_tokens']:,} inference input tokens, {resource['generated_output_tokens']:,} generated output tokens and {resource['training_input_tokens']:,} training input tokens. Observed pod interval: {resource['observed_pod_wall_hours_first_to_latest_run']:.3f} hours, which is not total billed lifetime. Actual hourly rate and dollar cost are unknown.")
    lines += ['', 'Reproduce the package from saved artifacts:', '', '```bash',
              'cd dualingCharacters', 'bash analysis/regenerate_all.sh',
              'PYTHONPATH=src .venv/bin/python analysis/progress.py', '```', '',
              'Print the fixed queue with `PYTHONPATH=src .venv/bin/python -m pcc.campaign --dry-run`. Execute it only after confirming that the existing controller has stopped; the authorized SSH environment and resume procedure are in `README.md`. Exact model revisions are in `configs/models.json`. No base-model cache or bulk checkpoint belongs in Git.', '',
              '| Model | Training condition | Completed seeds | Paired success | Seed SD |',
              '|---|---|---:|---:|---:|']
    for row in main:
        rate = 'pending' if row['paired_success'] is None else f"{row['paired_success']:.4f}"
        sd = '—' if row['seed_sd'] is None else f"{row['seed_sd']:.4f}"
        lines.append(f"| {row['model']} | {row['condition']} | {row['executed_seeds']}/3 | {rate} | {sd} |")
    lines += ['', 'Condition means above may cover different completed seed sets. Do not compare incomplete aggregates across conditions; use matched-seed contrasts and the per-seed tables. The shared untrained reference is not independent replication.',
              '', '## 2. Primary effect and uncertainty', '', effect_text(primary), '',
              'This is C5 minus C3 on antagonist-free 64-turn paired success. The corrected small pilots are engineering checks, not substitutes for this contrast. Excluded serialization runs remain in historical records and resource totals.', '',
              '## 3. What the controls support', '',
              '| Qwen contrast | Complete three-seed estimate |', '|---|---|']
    for comparator, meaning in [('C4', 'third character'), ('A1', 'narrative versus motives'),
                                ('A2', 'private history'), ('A3', 'peer interaction')]:
        result = next((row for row in effects if row['model']=='qwen' and
                       row['contrast']=='C5-'+comparator and row['seeds']==3), None)
        text = effect_text(result)
        if result is not None:
            text += f" Prespecified Holm-adjusted secondary p={result['holm_p_secondary']:.6g}."
        lines.append(f'| C5−{comparator}: {meaning} | {text} |')
    lines += ['', 'A primary advantage alone cannot establish narrative, persistence, interaction or coalition mechanisms. Character choices and coordination candidates are recorded separately in `main_character_diagnostics.json`; peer-message counts are not proof of a coalition. Severity was not equalized by the common opportunity cap.', '',
              '## 4. Transfer and independent-family confirmation', '',
              'All main tests remove antagonists; their estimates above directly assess transfer into the common scaffold. The additional fixed horizon, larger-memory, unfamiliar-fault and recovery settings are distinct diagnostics.', '',
              'Phi independent-model C5−C3: ' + effect_text(replication), '',
              f"Saved transfer aggregate rows: {len(transfer)} (includes main and common-subset reference rows; not a count of independent experiments). Saved external scoring rows: {len(external)}. LongMemEval uses a predetermined 50-question subset with adapted retrieval and judging; it is not an official comparable score. Unseen-profile supplement status: `{supplemental.get('status','not_started')}`.", '',
              '## 5. Exact unfinished requirements and weaknesses', '']
    if pending:
        counts = Counter(row['command'] for row in pending)
        lines.append('Unfinished scheduled stages by command: ' + ', '.join(f'{key}={value}' for key, value in sorted(counts.items())) + '. Every exact run ID and state is in `reports/tables/execution_report_trace.json`.')
    else:
        lines.append('Every original scheduled core stage has a completed record. This does not by itself establish the scientific hypotheses.')
    lines += ['', f"Human review: `{human.get('status','pending')}`; annotations: `{human.get('human_ratings','not_supplied')}`. Two independent raters and subsequent adjudication remain required unless actual completed sheets are supplied. Scientific author review, claim approval and a final current conference-policy check remain outstanding.", '',
              'Limitations include scripted users, a small shared categorical task schema, concentrated ambiguity cases, only three training seeds, limited power for a five-point effect, teacher-supplied targets, fixed retrieval, potentially unequal interference severity and jointly satisfiable antagonist-owned options. Frozen history-dependent characters are not jointly learned adversaries. The memory study cannot establish AGI, consciousness, universal robustness or general long-horizon planning.', '',
              '## 6. Candid evidence assessment', '', assessment(core_complete, primary), '',
              'All interpretations remain candidates for human scientific review. Failed runs, negative findings and missing cells must remain visible.']
    report_path = root/'reports/EXECUTION_REPORT.md'
    report_path.write_text('\n'.join(lines)+'\n')
    inputs['analysis/execution_report.py'] = sha256(Path(__file__))
    trace = {'classification': 'Mechanical factual report; existing estimators only',
             'core_stages_completed': completed, 'core_stages_scheduled': len(stage_rows),
             'unfinished_stages': pending, 'inputs': inputs, 'report_sha256': sha256(report_path)}
    (root/'reports/tables/execution_report_trace.json').write_text(json.dumps(trace, indent=2)+'\n')
    print(json.dumps({key: trace[key] for key in ('core_stages_completed','core_stages_scheduled')}))
    return trace


if __name__ == '__main__':
    generate(Path(__file__).resolve().parents[1])
