"""Small local artifact helpers, shared by extraction and publication."""
from pathlib import Path
from datetime import datetime, timezone
import csv
import gzip
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
CACHE = ROOT / 'artifacts/dialogue_interpretation_005'
REPORTS = HERE / 'reports'

def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''): h.update(chunk)
    return h.hexdigest()

def read(path): return json.loads(Path(path).read_text())
def now(): return datetime.now(timezone.utc).isoformat()
def rank(tag, key): return hashlib.sha256(f'{tag}:{key}'.encode()).hexdigest()
def write(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
def stream(path):
    opener = gzip.open if str(path).endswith('.gz') else open
    with opener(path, 'rt') as source:
        for line, text in enumerate(source, 1):
            if text.strip(): yield line, json.loads(text)
def csv_write(path, rows, fields=None):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields or list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
def verified(path, expected):
    if not Path(path).exists(): raise FileNotFoundError(f'Required evidence artifact missing: {path}')
    if digest(path) != expected: raise ValueError(f'Evidence hash mismatch: {path}')
def relative(path): return str(Path(path).relative_to(ROOT))
