"""Launch from an immutable source copy, safe while the working tree evolves."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

p=argparse.ArgumentParser();p.add_argument('--entry',choices=['cli','development_gate'],default='cli')
a,arguments=p.parse_known_args()
if arguments[:1]==['--']:arguments=arguments[1:]
source={p.name:p.read_text() for p in Path('src/rep_sensitivity').glob('*.py')}
runner=Path('scripts/development_gate.py').read_text() if a.entry=='development_gate' else None
identity=hashlib.sha256(json.dumps({'source':source,'runner':runner},sort_keys=True).encode()).hexdigest()
root=Path('artifacts/implementations')/identity
package=root/'rep_sensitivity';package.mkdir(parents=True,exist_ok=True)
for name,content in source.items():
    path=package/name
    if path.exists() and path.read_text()!=content:raise RuntimeError('Changed immutable code snapshot')
    path.write_text(content)
environment=dict(os.environ,PYTHONPATH=str(root.resolve()))
if runner is not None:
    path=root/'runner.py';path.write_text(runner)
    command=[sys.executable,str(path),*arguments]
else:command=[sys.executable,'-m','rep_sensitivity.cli',*arguments]
print(json.dumps({'implementation_snapshot':identity,'entry':a.entry}),flush=True)
os.execve(sys.executable,command,environment)
