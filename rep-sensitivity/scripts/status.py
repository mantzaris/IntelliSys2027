"""Read locally mirrored progress without inspecting held-out decision outcomes."""
import json
from pathlib import Path
from datetime import datetime, timezone

root=Path(__file__).resolve().parents[1]
runs=root/'artifacts/runs'


def read(path):
    return json.loads(path.read_text())


def completed_event(path):
    if not path.exists():return False
    for line in path.read_text().splitlines():
        try:event=json.loads(line)
        except json.JSONDecodeError:continue  # An active append may be partially mirrored.
        if event.get('event')=='run_complete':return True
    return False


progress=[]
for suite in ('pilot-v7','controls-development-v7','live-development-v8',
              'validation-v7','main-v7','supporting-v7','live-v8'):
    path=runs/suite
    if not (path/'manifest.json').exists() and not (path/'config.json').exists():
        progress.append({'suite':suite,'status':'not initialized locally'});continue
    manifest=read(path/'manifest.json') if (path/'manifest.json').exists() else None
    config=manifest['config'] if manifest else read(path/'config.json')
    kind='replay' if manifest and 'manager_calls' in manifest else 'live' if manifest else 'controls'
    for model in config['models']:
        model_path=path/model
        if kind=='replay':
            planned=manifest['trajectories']//len(config['models'])
            scored=sum(len(read(p)) for p in (model_path/'scores').glob('*.json'))
        else:
            planned_manifest=manifest if kind=='live' else read(model_path/'run-manifest.json') if (model_path/'run-manifest.json').exists() else None
            planned=planned_manifest['trajectories'] if planned_manifest else None
            scored=len(list((model_path/'scores').glob('*.json')))
        completed=completed_event(model_path/'events.jsonl')
        progress.append({'suite':suite,'model':model,'scored_trajectories':scored,
            'planned_trajectories':planned,'accepted_call_files':len(list((model_path/'calls').glob('*.json.gz'))),
            'completion_event':completed,'status':'complete checkpoint' if completed and scored==planned else 'incomplete checkpoint'})

for suite in ('mechanism-development-v1','fresh-probe-v1','mechanism-validation-v1','mechanism-heldout-v1','root-diagnostic-v1'):
    path=runs/suite;manifest_path=path/'manifest.json'
    if not manifest_path.exists():
        progress.append({'suite':suite,'status':'not initialized locally; check mechanism handoff record'});continue
    manifest=read(manifest_path);model=manifest['config']['model'];model_path=path/model
    scored=sum(len(read(p)) for p in (model_path/'scores').glob('*.json'))
    complete=completed_event(model_path/'events.jsonl')
    progress.append({'suite':suite,'model':model,'scored_trajectories':scored,'planned_trajectories':manifest['trajectories'],
        'accepted_call_files':len(list((model_path/'calls').glob('*.json.gz'))),'completion_event':complete,
        'status':'complete checkpoint' if complete and scored==manifest['trajectories'] else 'incomplete checkpoint'})

mirror=root/'artifacts/last-successful-mirror.txt'
mirror_utc=mirror.read_text().strip() if mirror.exists() else None
age=(datetime.now(timezone.utc)-datetime.fromisoformat(mirror_utc.replace('Z','+00:00'))).total_seconds() if mirror_utc else None
failures=sorted((runs/'study-execution-v8').glob('failure-*.json'))
report={'checked_utc':datetime.now(timezone.utc).isoformat(),'last_successful_mirror_utc':mirror_utc,
        'mirror_age_seconds':round(age,1) if age is not None else None,'progress':progress,
        'successor_failure_records':[str(p.relative_to(root)) for p in failures],
        'review_package_assembled':(root/'records/review-package.json').exists(),
        'human_scientific_review':'pending',
        'note':'Local checkpoint counts may lag the GPU. Completion flags are not a substitute for the final raw-output inventory audit. No decision outcomes are read.'}
print(json.dumps(report,indent=2))
