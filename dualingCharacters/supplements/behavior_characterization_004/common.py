"""Shared paths and verified streaming; reuse the established artifact readers."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib
import json
from supplements.exploration_003.common import ROOT,sha256,stream,trace_path,write,write_csv,verified_stream
from supplements.exploration_003.analysis import verify_science as verify_previous

HERE=ROOT/'supplements/behavior_characterization_004'
REPORTS=HERE/'reports'
CACHE=ROOT/'artifacts/behavior_characterization_004'
CONDITIONS=('C1','C2','C3','C4','C5','C6','A1','A2','A3')

def read(path):return json.loads(Path(path).read_text())
def utc():return datetime.now(timezone.utc).isoformat()
def rank(tag,value):return hashlib.sha256((tag+':'+str(value)).encode()).hexdigest()
def log(message):
    with (REPORTS/'WORK_LOG.md').open('a') as f:f.write('\n- '+utc()+': '+message+'\n')

def verify_science():
    verify_previous()
    manifest=read(HERE/'SCIENTIFIC_MANIFEST.json')
    for name,digest in manifest['files'].items():
        if sha256(HERE/name)!=digest:raise ValueError('Behavior scientific file changed: '+name)
    return manifest
