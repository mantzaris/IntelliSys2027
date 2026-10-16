"""Scheduling-only entry point for the unchanged, already frozen root requests.

Run ONLY under the safe continuation controller after the original Qwen stage.
The historical runner/config are preserved. The scheduling amendment authorizes
this earlier natural boundary; no active inference is suspended or restarted.
"""
import fcntl
import importlib.metadata
import json
from pathlib import Path
from rep_sensitivity.root_diagnostic import run, analyze
from rep_sensitivity.schema import digest
from rep_sensitivity.storage import immutable_json,utcnow

root=Path('artifacts/runs/root-diagnostic-execution');root.mkdir(parents=True,exist_ok=True)
lock=(root/'.controller.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
if not Path('artifacts/runs/study-execution-v8/primary_replay_and_live-complete.json').exists():
    raise RuntimeError('Original Qwen stage is not complete')
freeze=json.loads(Path('records/freezes/root-diagnostic-v1.json').read_text())
config=json.loads(Path('configs/frozen/root-diagnostic-v1.json').read_text())
import rep_sensitivity
package=Path(rep_sensitivity.__file__).parent
if digest({p.name:p.read_text() for p in package.glob('*.py')})!=freeze['source_sha256'] or digest(config)!=freeze['config_sha256']:
    raise RuntimeError('Frozen root source/config mismatch')
for name,version in [('vllm','0.10.2'),('transformers','4.55.4')]:
    if importlib.metadata.version(name)!=version:raise RuntimeError('Inference environment changed')
if not (root/'complete.json').exists():
    run(config)
    result=analyze('artifacts/runs/'+config['name'],'results/'+config['name'])
    immutable_json(root/'complete.json',{'utc':utcnow(),'analysis_sha256':digest(result),'human_review':'pending'})
