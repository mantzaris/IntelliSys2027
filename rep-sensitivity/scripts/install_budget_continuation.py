"""Install the authorized allowance at future stage starts, without GPU calls."""
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import sysconfig

from authorized_gpu_budget import ALLOWANCE_RECORD, ALLOWANCE_SHA256, authorized_cap
from budget_entrypoint_route import routed_command
from freeze_budget_continuation import immutable_write
from run_objective_confirmation import append, prior_seconds


def main():
    project = Path(__file__).resolve().parents[1]
    if Path.cwd() != project or Path(sys.prefix).resolve() != project / '.venv':
        raise RuntimeError('Run from the remote project using its own .venv')
    cap = authorized_cap()
    manifest_path = project / 'records/execution/additional-gpu-budget-routing-v2.json'
    raw = manifest_path.read_bytes()
    manifest_sha = hashlib.sha256(raw).hexdigest()
    manifest = json.loads(raw)
    for route in manifest['routes']:
        routed_command([str(project / route['original_entrypoint'])], manifest, project)
    for suite in ('objective-confirmation-v1', 'numerical-preservation-v1', 'adjacent-explorations-v1'):
        if next((project / 'artifacts/runs' / suite).glob('*/calls/*.json.gz'), None) is not None:
            raise RuntimeError('Affected stage already produced responses; inspect before amendment')
    shared = project / 'artifacts/runs/objective-confirmation-execution'
    shared.mkdir(parents=True, exist_ok=True)
    with (shared / '.controller.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        ledger = shared / 'budget.jsonl'
        events = [json.loads(x) for x in ledger.read_text().splitlines() if x]
        if not any(e.get('event') == 'allowance_amendment' and
                   e.get('authorization_sha256') == ALLOWANCE_SHA256 for e in events):
            append(ledger, {'event': 'allowance_amendment', 'cumulative_cap_seconds': cap,
                'previous_cap_seconds': 7200, 'charged_seconds': prior_seconds(events),
                'authorization': str(ALLOWANCE_RECORD), 'authorization_sha256': ALLOWANCE_SHA256,
                'routing_manifest_sha256': manifest_sha})
        adapter = project / manifest['routing_adapter']
        if hashlib.sha256(adapter.read_bytes()).hexdigest() != manifest['routing_adapter_sha256']:
            raise RuntimeError('Changed budget routing adapter')
        startup = ("import os,runpy,sys; os.environ.get('REP_EXECUTION_SEGMENT') and "
            f"runpy.run_path({str(adapter)!r}, run_name='rep_budget_entrypoint_route', "
            f"init_globals={{'startup_argv':sys.argv[:], 'routing_manifest':{str(manifest_path)!r}, "
            f"'routing_manifest_sha256':{manifest_sha!r}}})\n")
        compile(startup, 'rep_authorized_budget.pth', 'exec')
        hook = Path(sysconfig.get_path('purelib')) / 'rep_authorized_budget.pth'
        immutable_write(hook, startup.encode())
        # --help exits before config loading, prerequisite checks or model calls.
        # Each original queued command must demonstrably reach its derivative.
        checks = []
        route_log = project / manifest['routing_event_log']
        before = len(route_log.read_text().splitlines()) if route_log.exists() else 0
        for route in manifest['routes']:
            env = dict(os.environ, REP_EXECUTION_SEGMENT=str(project / manifest['execution_segment']),
                PYTHONPATH=str((project / route['original_entrypoint']).parent))
            completed = subprocess.run([sys.executable, route['original_entrypoint'], '--help'],
                env=env, capture_output=True, text=True, timeout=30)
            if completed.returncode != 0:
                raise RuntimeError('Budget route preflight failed: ' + completed.stderr)
            checks.append({'stage': route['stage'], 'returncode': completed.returncode})
        routes = [json.loads(x) for x in route_log.read_text().splitlines()][before:]
        if len(routes) != 3 or not all(e['preflight_only'] for e in routes):
            raise RuntimeError('Future queued entrypoints did not route exactly once')
        record = {'utc': datetime.now(timezone.utc).isoformat(), 'cumulative_cap_seconds': cap,
            'charged_seconds': prior_seconds(events), 'remaining_seconds': cap - prior_seconds(events),
            'routing_manifest_sha256': manifest_sha, 'startup_hook': str(hook.relative_to(project)),
            'startup_hook_sha256': hashlib.sha256(startup.encode()).hexdigest(),
            'preflight_routes': checks, 'gpu_calls_from_installation': 0,
            'active_processes_restarted': False, 'scientific_design_changed': False}
        destination = project / 'records/execution/additional-gpu-budget-installed-v2.json'
        if not destination.exists():
            immutable_write(destination, (json.dumps(record, indent=2) + '\n').encode())
        print(json.dumps(record))


if __name__ == '__main__':
    main()
