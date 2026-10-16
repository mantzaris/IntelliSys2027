"""Launch from an immutable source copy, safe while the working tree evolves."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

p=argparse.ArgumentParser();p.add_argument('--entry',choices=['cli','development_gate','study','live_revision_study','mechanism_study'],default='cli')
p.add_argument('--snapshot-only',action='store_true')
a,arguments=p.parse_known_args()
if arguments[:1]==['--']:arguments=arguments[1:]
source={p.name:p.read_text() for p in Path('src/rep_sensitivity').glob('*.py')}
runner=Path('scripts',{'development_gate':'development_gate.py','study':'run_study.py','live_revision_study':'run_corrected_live_study.py','mechanism_study':'run_mechanism_study.py'}[a.entry]).read_text() if a.entry!='cli' else None
configuration={p.name:p.read_text() for p in Path('configs').glob('*.json')} if a.entry in ('study','live_revision_study','mechanism_study') else {}
identity=hashlib.sha256(json.dumps({'source':source,'runner':runner,'configuration':configuration},sort_keys=True).encode()).hexdigest()
root=Path('artifacts/implementations')/identity
package=root/'rep_sensitivity';package.mkdir(parents=True,exist_ok=True)
for name,content in source.items():
    path=package/name
    if path.exists() and path.read_text()!=content:raise RuntimeError('Changed immutable code snapshot')
    path.write_text(content)
environment=dict(os.environ,PYTHONPATH=str(root.resolve()))
for name,content in configuration.items():
    path=root/'configuration'/name;path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists() and path.read_text()!=content:raise RuntimeError('Changed immutable configuration snapshot')
    path.write_text(content)
if runner is not None:
    path=root/'runner.py';path.write_text(runner)
    command=[sys.executable,str(path),*(['--templates',str(root/'configuration')] if a.entry in ('study','live_revision_study','mechanism_study') else []),*arguments]
else:command=[sys.executable,'-m','rep_sensitivity.cli',*arguments]
print(json.dumps({'implementation_snapshot':identity,'entry':a.entry}),flush=True)
if a.snapshot_only:raise SystemExit(0)
os.execve(sys.executable,command,environment)
