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

for suite in ('mechanism-development-v1','fresh-probe-v1','mechanism-validation-v1','mechanism-heldout-v1','root-diagnostic-v1','numerical-preservation-v1'):
    path=runs/suite;manifest_path=path/'manifest.json'
    if not manifest_path.exists():
        if suite=='numerical-preservation-v1':
            stop=runs/'numerical-preservation-execution/not-launched.json'
            progress.append({'suite':suite,'status':'not launched' if stop.exists() else 'frozen; last priority after confirmation; same cumulative 7200-second cap',
                             'reason':read(stop) if stop.exists() else None});continue
        progress.append({'suite':suite,'status':'not initialized locally; check mechanism handoff record'});continue
    manifest=read(manifest_path);model=manifest['config']['model'];model_path=path/model
    scored=sum(len(read(p)) for p in (model_path/'scores').glob('*.json'))
    complete=completed_event(model_path/'events.jsonl')
    progress.append({'suite':suite,'model':model,'scored_trajectories':scored,'planned_trajectories':manifest['trajectories'],
        'accepted_call_files':len(list((model_path/'calls').glob('*.json.gz'))),'completion_event':complete,
        'status':'complete checkpoint' if complete and scored==manifest['trajectories'] else 'incomplete checkpoint'})


path=runs/'objective-confirmation-v1'
if (path/'manifest.json').exists():
    manifest=read(path/'manifest.json')
    for model,planned in manifest['per_model_trajectories'].items():
        model_path=path/model;scored=sum(len(read(p)) for p in (model_path/'scores').glob('*.json'))
        complete=completed_event(model_path/'events.jsonl')
        progress.append({'suite':'objective-confirmation-v1','model':model,'independent_base_pairs':manifest['base_pairs'],
            'scored_trajectories':scored,'planned_trajectories':planned,'accepted_call_files':len(list((model_path/'calls').glob('*.json.gz'))),
            'completion_event':complete,'status':'complete checkpoint' if complete and scored==planned else 'incomplete checkpoint'})
else:progress.append({'suite':'objective-confirmation-v1','status':'frozen; queued after original Phi-4; shared 7200-second new-compute cap'})

adjacent=runs/'adjacent-explorations-v1'
if (adjacent/'manifest.json').exists():
    m=read(adjacent/'manifest.json');p=adjacent/m['config']['model']
    progress.append({'suite':'adjacent-explorations-v1','independent_base_pairs':m['base_pairs'],
        'planned_calls':m['calls'],'accepted_call_files':len(list((p/'calls').glob('*.json.gz'))),
        'completion_event':completed_event(p/'events.jsonl'),'execution_mode':m['config']['execution_mode']})
elif (root/'configs/frozen/adjacent-explorations-v1.json').exists():
    stop=runs/'adjacent-explorations-execution/not-launched.json'
    progress.append({'suite':'adjacent-explorations-v1','status':'not launched' if stop.exists() else
        'queued last after numerical preservation; at most 104 calls/900 seconds in the existing cumulative cap',
        'reason':read(stop) if stop.exists() else None})

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
