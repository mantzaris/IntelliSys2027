"""Separate paths and compact artifact helpers for the eight-hour follow-up."""
from pathlib import Path
from datetime import datetime, timezone
import json
import os

ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/'supplements/long_horizon_intent_002'
REPORTS=HERE/'reports'
ARTIFACTS=ROOT/'artifacts/long_horizon_intent_002'


def utc():return datetime.now(timezone.utc).isoformat()


def read(path,default=None):
    try:return json.loads(Path(path).read_text())
    except FileNotFoundError:
        if default is not None:return default
        raise


def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n');temporary.replace(path)


def log(message):
    with (REPORTS/'WORK_LOG.md').open('a') as out:out.write('\n- '+utc()+': '+message+'\n')


def reporting_environment():
    return {**os.environ,'PYTHONPATH':'src','PCC_REPORT_OUTPUT':str(REPORTS),'PCC_REPORT_CACHE':str(ARTIFACTS/'core_audits')}
