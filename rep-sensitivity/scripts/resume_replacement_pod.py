"""Restore the existing serial queue after loss of the old RunPod container.

This schedules the original immutable runners. It does not define experiments,
change prompts, retry completed outputs, or reset their shared budget.
"""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from rep_sensitivity.storage import immutable_json, utcnow


def idle():
    deadline = time.monotonic() + 300
    while subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid',
                                   '--format=csv,noheader'], text=True).strip():
        if time.monotonic() >= deadline:
            raise RuntimeError('GPU remains occupied; no process interrupted')
        time.sleep(5)


def main():
    if os.environ.get('REP_EXECUTION_SEGMENT_ACTIVE') != str(os.getpid()):
        raise RuntimeError('Replacement hardware provenance hook is not active')
    config = json.loads(Path(os.environ['REP_EXECUTION_SEGMENT']).read_text())
    root = Path('artifacts/runs/replacement-ada-execution')
    root.mkdir(parents=True, exist_ok=True)
    lock = (root / '.controller.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    gpu = subprocess.check_output(['nvidia-smi', '--query-gpu=uuid', '--format=csv,noheader'], text=True).strip()
    if gpu != config['gpu_uuid']:
        raise RuntimeError('Runtime manifest names a different GPU')
    for stage in config['stages']:
        marker = root / (stage['name'] + '.json')
        if marker.exists():
            if json.loads(marker.read_text())['returncode'] != 0:
                raise RuntimeError('Prior stage failure requires inspection: ' + stage['name'])
            continue
        idle()
        environment = dict(os.environ, PYTHONPATH=str(Path(stage['snapshot']).resolve()))
        start = time.monotonic()
        with Path('logs', 'replacement-ada-' + stage['name'] + '.log').open('a') as log:
            code = subprocess.run([sys.executable, *stage['arguments']],
                env=environment, stdout=log, stderr=subprocess.STDOUT).returncode
        immutable_json(marker, {'utc': utcnow(), 'stage': stage['name'], 'returncode': code,
            'elapsed_wall_seconds': time.monotonic() - start, 'snapshot': stage['snapshot'],
            'execution_segment': config['segment_id']})
        if code:
            raise RuntimeError('Frozen runner stopped; accepted outputs preserved: ' + stage['name'])
        if stage['name'] == 'primary-replay-and-live':
            immutable_json('artifacts/runs/study-execution-v8/primary_replay_and_live-complete.json',
                {'stage': 'primary_replay_and_live', 'complete': True})
    immutable_json(root / 'complete.json', {'utc': utcnow(), 'queue_finished': True,
        'interpretation': 'Budget-limited stages can be skipped by their frozen rules. Consult each stage marker.'})


if __name__ == '__main__':
    main()
