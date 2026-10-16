"""Freeze the bounded development extension after matching CPU preflight and tests."""
import json
from pathlib import Path
from rep_sensitivity.schema import digest
from rep_sensitivity.storage import immutable_json,utcnow

source=digest({p.name:p.read_text() for p in Path('src/rep_sensitivity').glob('*.py')})
tests=json.loads(Path('records/tests/mechanism-v1.json').read_text())
if tests['source_sha256']!=source or not tests['passed']:raise RuntimeError('No passing integrity check for current source')
for name in ('mechanism-development-v1','fresh-probe-v1'):
    candidate=json.loads(Path('configs',name+'.json').read_text())
    preflights=[(p,json.loads(p.read_text())) for p in Path('records/preflight').glob(name+'-*.json')]
    matches=[(p,v) for p,v in preflights if v['config_sha256']==digest(candidate) and v.get('source_sha256')==source]
    if not matches:raise RuntimeError('Native-token preflight missing for current source: '+name)
    path,evidence=sorted(matches)[-1]
    frozen={**candidate,'status':'frozen'}
    record_path=Path('records/freezes',name+'.json')
    if record_path.exists():
        existing=json.loads(record_path.read_text())
        if existing['source_sha256']!=source or existing['config_sha256']!=digest(frozen):raise RuntimeError('Existing freeze differs; version the amendment')
    else:
        immutable_json(record_path,{'frozen_utc':utcnow(),'amendment':'mechanism-v1',
            'config_sha256':digest(frozen),'candidate_config_sha256':digest(candidate),'source_sha256':source,
            'runner_sha256':digest(Path('scripts/run_mechanism_study.py').read_text()),
            'analysis_manifest_sha256':digest(json.loads(Path('configs/mechanism-analysis-v1.json').read_text())),
            'allocation_rule_sha256':digest(json.loads(Path('configs/mechanism-allocation-v1.json').read_text())),
            'preflight_record':str(path),'preflight_sha256':digest(evidence),'integrity_check_sha256':digest(tests),
            'original_heldout_outcomes_inspected':False,
            'registration':'Prospective repository freeze, not external registration. Development remains exploratory.'})
    immutable_json(Path('configs/frozen',name+'.json'),frozen)
    print(name+' frozen; no inference launched')
