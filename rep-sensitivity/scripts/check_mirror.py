"""Compare immutable raw-file hashes on the existing pod and local mirror."""
import hashlib
import json
from pathlib import Path
import subprocess
from datetime import datetime, timezone

# No response content is printed or evaluated. Use existing verified SSH host key.
code = '''import hashlib,json
from pathlib import Path
root=Path('/workspace/rep-sensitivity/artifacts/runs')
out={}
for suite in ('pilot-v7','validation-v7','main-v7'):
 p=root/suite
 out[suite]={str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest()
  for pattern in ('manifest.json','pairs.json','frozen-reports.json','implementation.json','*/scores/*.json','*/calls/*.json.gz')
  for f in p.glob(pattern)}
print(json.dumps(out))
'''
command = ['ssh', '-i', str(Path.home()/'.ssh/id_rsa'), '-o', 'IdentitiesOnly=yes', '-o', 'BatchMode=yes',
    '-o', 'ConnectTimeout=15', '-o', 'StrictHostKeyChecking=yes',
    '-o', 'UserKnownHostsFile=/tmp/intellisys-runpod-known-hosts', '-p', '19997',
    'root@195.26.233.32', 'python -']
remote = json.loads(subprocess.check_output(command, input=code, text=True))
comparisons = []
for suite, files in remote.items():
    matches = 0; missing = []; different = []
    for relative, sha in files.items():
        local = Path('artifacts/runs')/suite/relative
        if not local.exists(): missing.append(relative)
        elif hashlib.sha256(local.read_bytes()).hexdigest() != sha: different.append(relative)
        else: matches += 1
    comparisons.append({'suite': suite, 'remote_immutable_files_at_snapshot': len(files),
        'identical_local_files': matches, 'not_yet_local': missing, 'different_content': different})
record = {'utc': datetime.now(timezone.utc).isoformat(), 'comparisons': comparisons,
          'interpretation': 'No held-out choices inspected. Additional remote calls after the snapshot are expected; a lag is not a content conflict.'}
Path('records/execution/mirror-verification-v2.json').write_text(json.dumps(record, indent=2)+'\n')
print(json.dumps(record))
if any(r['different_content'] for r in comparisons): raise SystemExit('Immutable content mismatch')
