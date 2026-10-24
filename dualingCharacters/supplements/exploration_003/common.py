"""Small shared I/O helpers, with immutable-source validation."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
from supplements.review_001.common import stream, trace_path, write, write_csv
from pcc.resources import sha256

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'supplements/exploration_003'
REPORTS = HERE / 'reports'
CACHE = ROOT / 'artifacts/exploration_003'
CONDITIONS = ('C1','C2','C3','C4','C5','C6','A1','A2','A3')

def utc():
    return datetime.now(timezone.utc).isoformat()

def read(path):
    return json.loads(Path(path).read_text())

def rank(tag, value):
    return hashlib.sha256((tag+':'+str(value)).encode()).hexdigest()

def log(message):
    with (REPORTS/'WORK_LOG.md').open('a') as target:
        target.write('\n- '+utc()+': '+message+'\n')

def verified_stream(path, expected):
    path = ROOT/path if not Path(path).is_absolute() else Path(path)
    before = path.stat()
    if sha256(path) != expected:
        raise ValueError('Frozen source hash mismatch: '+str(path))
    yield from stream(path)
    after = path.stat()
    if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):
        raise ValueError('Completed source changed while reading: '+str(path))

def verify_prior():
    from supplements.long_horizon_intent_002.freeze import verify
    verify()
    return {str(p.relative_to(ROOT)):sha256(p) for p in (
        ROOT/'configs/freeze.json',ROOT/'supplements/review_001/FREEZE.json',
        ROOT/'supplements/long_horizon_intent_002/FREEZE.json')}
