"""Wait behind existing controllers, then run the immutable root diagnostic."""
import argparse
import fcntl
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import time
from rep_sensitivity.root_diagnostic import run, analyze
from rep_sensitivity.schema import digest
from rep_sensitivity.storage import immutable_json, utcnow


def main():
    p = argparse.ArgumentParser(); p.add_argument('--after-pid', type=int)
    p.add_argument('--config', default='configs/frozen/root-diagnostic-v1.json'); a = p.parse_args()
    record = Path('artifacts/runs/root-diagnostic-execution'); record.mkdir(parents=True, exist_ok=True)
    lock = (record/'.controller.lock').open('a'); fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
    while a.after_pid:
        try:
            os.kill(a.after_pid, 0)
            if b'runner.py' not in Path('/proc', str(a.after_pid), 'cmdline').read_bytes(): break
        except (ProcessLookupError, FileNotFoundError): break
        time.sleep(5)
    required = [Path('artifacts/runs/study-execution-v8')/(name+'-complete.json')
                for name in ('primary_replay_and_live', 'secondary_replay_and_live')]
    required += [Path('artifacts/runs/mechanism-execution/extension-stage.json')]
    if not all(p.exists() for p in required):
        immutable_json(record/'blocked.json', {'utc': utcnow(), 'reason': 'Protected earlier stages have not completed'})
        return
    deadline = time.monotonic()+300
    while subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid', '--format=csv,noheader'], text=True).strip():
        if time.monotonic() > deadline: raise RuntimeError('GPU occupied; no process interrupted')
        time.sleep(5)
    for package, version in [('vllm', '0.10.2'), ('transformers', '4.55.4')]:
        if importlib.metadata.version(package) != version: raise RuntimeError('Changed inference environment')
    config = json.loads(Path(a.config).read_text())
    freeze = json.loads(Path('records/freezes/root-diagnostic-v1.json').read_text())
    source = {p.name: p.read_text() for p in (Path(__file__).parent/'rep_sensitivity').glob('*.py')}
    if digest(source) != freeze['source_sha256'] or digest(config) != freeze['config_sha256']:
        raise RuntimeError('Snapshot/config differs from root-diagnostic freeze')
    run(config)
    result = analyze('artifacts/runs/'+config['name'], 'results/'+config['name'])
    immutable_json(record/'complete.json', {'utc': utcnow(), 'analysis_sha256': digest(result), 'human_review': 'pending'})


if __name__ == '__main__': main()
