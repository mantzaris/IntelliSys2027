from pathlib import Path
import hashlib
import json
import os
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[2]
SESSION='overnight_20261024T023622Z'
# Explicit output routing lets later reporting sessions reuse these CPU audits
# without rewriting a historical handoff. Defaults preserve the original session.
OUT=Path(os.environ.get('PCC_REPORT_OUTPUT',str(ROOT/'reports'/SESSION))).resolve()
CACHE=Path(os.environ.get('PCC_REPORT_CACHE',str(ROOT/'artifacts'/SESSION))).resolve()
if not OUT.is_relative_to(ROOT) or not CACHE.is_relative_to(ROOT):
    raise ValueError('Reporting paths must remain within the study directory')


def utc():return datetime.now(timezone.utc).isoformat()


def read(path,default=None):
    try:return json.loads(Path(path).read_text())
    except (FileNotFoundError,json.JSONDecodeError):
        if default is not None:return default
        raise


def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n');temp.replace(path)


def append(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a') as f:f.write(json.dumps(value,sort_keys=True)+'\n')


def log(message):
    with (OUT/'WORK_LOG.md').open('a') as f:f.write('\n- '+utc()+': '+message+'\n')


def fingerprint(paths):
    return [[str(p.relative_to(ROOT)),p.stat().st_size,p.stat().st_mtime_ns] for p in paths]
