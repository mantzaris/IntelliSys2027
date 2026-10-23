"""CPU-only final reporting after the existing core and supplemental controllers.

Does not launch or alter GPU jobs. Waits for core completion and a terminal
supplement decision, then obtains the shared controller lock before regenerating
and committing the compact author-review package on main. A failed core remains
pending for its normal infrastructure audit/resume; it is never called complete.
"""
from pathlib import Path
import fcntl
import json
import subprocess
import time
from pcc.campaign import commit_generated_package
from pcc.freeze import verify_freeze
from pcc.resources import sha256


def read(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def ready(core: dict, supplement: dict) -> bool:
    terminal = {'scheduled_supplement_complete', 'not_executed_budget_gate',
                'controller_error', 'incomplete', 'incomplete_storage_guard',
                'incomplete_archive_check'}
    return core.get('status') == 'scheduled_grid_complete' and supplement.get('status') in terminal


def main():
    root = Path(__file__).resolve().parents[1]
    state_path = root/'artifacts/final_report_controller_state.json'
    own_lock = (root/'artifacts/final_report_controller.lock').open('a+')
    fcntl.flock(own_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    implementation = sha256(Path(__file__))
    def state(status: str, **values):
        temporary = state_path.with_suffix('.tmp')
        temporary.write_text(json.dumps({'status': status, 'controller_sha256': implementation,
                                        'gpu_operations': 0, **values}, indent=2)+'\n')
        temporary.replace(state_path)
    state('waiting_for_existing_controllers')
    try:
        while not ready(read(root/'artifacts/campaign_state.json'),
                        read(root/'artifacts/unseen_profiles_controller_state.json')):
            time.sleep(30)
        shared = (root/'artifacts/campaign.lock').open('a+')
        while True:
            try:
                fcntl.flock(shared, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                time.sleep(30)
        verify_freeze(root)
        state('regenerating_saved_evidence')
        subprocess.run(['bash', 'analysis/regenerate_all.sh'], cwd=root, check=True)
        report = read(root/'reports/tables/execution_report_trace.json')
        if report['core_stages_completed'] != report['core_stages_scheduled']:
            raise RuntimeError('Core completion marker disagrees with actual run records')
        commit_generated_package(root, 'Full saved-evidence report regenerated after the original core queue and terminal supplement decision; human ratings and scientific author review remain pending')
        state('completed', report_sha256=sha256(root/'reports/EXECUTION_REPORT.md'),
              core_stages=report['core_stages_completed'],
              supplement_status=read(root/'artifacts/unseen_profiles_controller_state.json').get('status'))
    except Exception as error:
        state('reporting_error', error=str(error))
        raise


if __name__ == '__main__':
    main()
