from pathlib import Path
import csv
import gzip
import hashlib
import json
from pcc.resources import sha256
from pcc.eligibility import exclusions

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT/'supplements/review_001'
ARTIFACTS = ROOT/'artifacts/review_001'
RESULTS = HERE/'results'


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True)+'\n')
    temporary.replace(path)


def trace_path(path):
    path=Path(path); compressed=path.with_suffix(path.suffix+'.gz')
    return compressed if compressed.exists() else path


def stream(path):
    path=trace_path(path)
    opener=gzip.open if path.suffix=='.gz' else open
    with opener(path,'rt') as source:
        for line in source:
            if line.strip():yield json.loads(line)


def stable_rows(path, inputs):
    path=trace_path(path)
    before=path.stat()
    inputs[str(path.relative_to(ROOT))]=sha256(path)
    yield from stream(path)
    after=path.stat()
    if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):
        raise RuntimeError('Source changed during completed-artifact audit: '+str(path))


def eligible_runs(task=None):
    excluded=exclusions(ROOT)
    for path in sorted((ROOT/'artifacts/runs').glob('main-*/status.json')):
        meta=read(path)
        if meta['status']=='completed' and meta['run_id'] not in excluded and (task is None or meta.get('task')==task):
            yield path.parent,meta


def require_completed(run_id):
    run=ROOT/'artifacts/runs'/run_id
    meta=read(run/'status.json')
    if meta['status']!='completed' or run_id in exclusions(ROOT):
        raise ValueError('Requires completed eligible prerequisite: '+run_id)
    return run,meta


def write_csv(path, rows):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if not rows:path.write_text('');return
    fields=list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w',newline='') as target:
        writer=csv.DictWriter(target,fieldnames=fields,lineterminator='\n')
        writer.writeheader();writer.writerows(rows)


def identity(row):
    return row['family_id'],row['world']


def rank(tag, value):
    return hashlib.sha256((tag+':'+str(value)).encode()).hexdigest()


def record_source(inputs,path):
    path=Path(path);inputs[str(path.relative_to(ROOT))]=sha256(path)


def final_checkpoint(condition):
    if condition=='base':return None
    name=f'main-qwen-{condition.lower()}-17-r1-fit'+('-format2' if condition=='C1' else '')
    run,meta=require_completed(name)
    return run/'training/final'


def main_evaluation(condition):
    return 'base-qwen-eval' if condition=='base' else f'main-qwen-{condition.lower()}-17-eval'+('-format2' if condition=='C1' else '')
