"""Resume from a run's immutable source snapshot, not a changed working tree."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

p=argparse.ArgumentParser()
p.add_argument('run_directory')
p.add_argument('--model',required=True)
a=p.parse_args()
root=Path(a.run_directory)
source_path=root/'implementation.json'
source=json.loads(source_path.read_text())
fingerprint=hashlib.sha256(source_path.read_bytes()).hexdigest()
destination=Path('artifacts/implementations')/fingerprint/'rep_sensitivity'
destination.mkdir(parents=True,exist_ok=True)
for name,text in source.items():
    if Path(name).name!=name or not name.endswith('.py'):
        raise ValueError('Unexpected source snapshot member')
    path=destination/name
    if path.exists() and path.read_text()!=text:raise RuntimeError('Changed archived implementation')
    path.write_text(text)
manifest=json.loads((root/'manifest.json').read_text())
config_path=destination.parent/'config.json'
config_path.write_text(json.dumps(manifest['config'],indent=2)+'\n')
environment=dict(os.environ,PYTHONPATH=str(destination.parent.resolve()))
subprocess.run([sys.executable,'-m','rep_sensitivity.cli','run','--config',str(config_path),
                '--model',a.model],env=environment,check=True)
