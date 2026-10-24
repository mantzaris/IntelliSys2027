"""Read-only supplementary readiness; never bind, allocate, upload or infer."""
from pcc.campaign import jobs, load_overrides, resolve_job
from pcc.freeze import verify_freeze
from pcc.resources import sha256
from supplements.review_001.freeze import verify
from supplements.review_001.common import final_checkpoint, main_evaluation
from .common import ROOT, OUT, read, write, utc


def main():
    frozen = verify(); core = verify_freeze(ROOT); overrides = load_overrides(ROOT)
    queue = [resolve_job(j, overrides) for j in jobs(core['plan'])]
    missing = []
    for job in queue:
        status = read(ROOT / f'artifacts/runs/{job["id"]}/status.json', {})
        if status.get('status') != 'completed': missing.append(job['id'])
    checkpoints = {}
    for condition in ('base', 'C1', 'C3', 'C5'):
        evaluation = main_evaluation(condition); status = read(ROOT / f'artifacts/runs/{evaluation}/status.json', {})
        try:
            adapter = final_checkpoint(condition)
            checkpoint_status = 'complete' if adapter else 'base_no_adapter'
        except (FileNotFoundError, ValueError):
            adapter = None
            checkpoint_status = 'pending_required_final_checkpoint'
        # Evaluation validation already verifies immutable adapter bytes. Avoid rehashing large weights here.
        checkpoints[condition] = {'evaluation_id': evaluation, 'status': status.get('status', 'pending'),
          'checkpoint_status': checkpoint_status,
          'adapter': str(adapter.relative_to(ROOT)) if adapter else None,
          'evaluated_adapter_sha256': status.get('loaded_adapter_sha256'),
          'model_revision': status.get('model_revision'), 'chat_template_sha256': status.get('chat_template_sha256')}
    directory = ROOT / 'artifacts/review_001'
    inputs = {str(p.relative_to(ROOT)): {'bytes': p.stat().st_size, 'sha256': sha256(p)}
              for p in sorted((directory / 'inputs').glob('*.json'))}
    controller = read(directory / 'controller_state.json', {})
    marker = read(ROOT / 'artifacts/campaign_state.json', {}).get('status') == 'scheduled_grid_complete'
    result = {'utc': utc(), 'supplement_files_verified': len(frozen['files']),
      'supplement_freeze_sha256': sha256(ROOT / 'supplements/review_001/FREEZE.json'),
      'required_core_stages': len(queue), 'incomplete_core_stages': len(missing),
      'core_completion_marker': marker, 'core_gate_satisfied': not missing and marker,
      'fixed_checkpoints': checkpoints, 'prepared_input_manifests': inputs,
      'adapter_binding_exists': (directory / 'bindings.json').exists(),
      'timing_allocation_exists': (directory / 'allocation.json').exists(),
      'controller': controller, 'next_required_core_stage': missing[0] if missing else None,
      'launch_policy': 'Existing coordinator only after all 241 core stages; shared lock and cumulative ledger; two-hour aggregate cap inside 96 hours, 30-minute contingency and 90-second margin.',
      'no_model_calls_performed_by_this_audit': True,
      'allocation_status': 'Concrete allocation remains pending fixed post-core profiling; do not substitute an invented sample count.'}
    write(OUT / 'SUPPLEMENT_READINESS.json', result)
    print({'core_completed': len(queue) - len(missing), 'scheduled': len(queue), 'supplement_status': controller.get('status')})


if __name__ == '__main__':
    main()
