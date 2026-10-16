"""Predeclared development qualification; accepted failures are never resampled."""
import json
from pathlib import Path
from .replay import run
from .storage import immutable_json


def rows(suite,alias):
    return [r for path in Path('artifacts/runs',suite,alias,'scores').glob('*.json')
            for r in json.loads(path.read_text())]


def qualify(alias,configuration_directory='configs'):
    name='competence-'+alias+'-v7';smoke='summary-smoke-'+alias+'-v7'
    gate_path=Path('records/gates')/(name+'.json')
    smoke_path=Path('records/gates')/(smoke+'.json')
    if gate_path.exists() and not json.loads(gate_path.read_text())['passed']:
        raise RuntimeError('Existing failed development gate; no resampling: '+alias)
    if (gate_path.exists() and smoke_path.exists()
            and json.loads(smoke_path.read_text())['contract_valid']):return None
    config=lambda suite:json.loads((Path(configuration_directory)/(suite+'.json')).read_text())
    model=run(config(name),alias)
    records=rows(name,alias)
    if len(records)!=96:raise RuntimeError('Incomplete development qualification')
    rates={kind:sum(r['correct'] for r in records if r['kind']==kind)/sum(r['kind']==kind for r in records)
           for kind in ('schedule','workflow')}
    passed=all(value>=0.85 for value in rates.values())
    immutable_json(gate_path,{'suite':name,'accuracy':rates,'threshold':0.85,'passed':passed,
        'rule':'Both task populations meet the unchanged point-estimate development threshold; not a power or robustness claim.'})
    if not passed:raise RuntimeError('Development competence gate not met: '+alias)
    run(config(smoke),alias,model=model)
    records=rows(smoke,alias)
    valid=len(records)==12 and not any(r['operational_failure'] for r in records)
    immutable_json(smoke_path,{'suite':smoke,'trajectories':len(records),'contract_valid':valid})
    if not valid:raise RuntimeError('Summary contract check failed: '+alias)
    return model
