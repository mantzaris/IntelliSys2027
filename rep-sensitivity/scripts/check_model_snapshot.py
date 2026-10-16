"""Verify downloaded shard bytes against authoritative Hub LFS hashes."""
import argparse
import hashlib
import json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('alias');a=p.parse_args()
metadata=json.loads(Path('records/models',a.alias+'.json').read_text())
root=Path(Path('artifacts/models',a.alias+'_path.txt').read_text().strip())
checks=[]
for f in metadata['files']:
    path=root/f['name']
    if not f['name'].startswith('model-') or not path.exists():continue
    h=hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda:handle.read(8*1024*1024),b''):h.update(block)
    observed=h.hexdigest()
    assert observed==f['lfs_sha256'],f['name']
    checks.append({'name':f['name'],'sha256':observed,'bytes':path.stat().st_size})
assert checks,'No weight shards verified'
Path('records/models',a.alias+'-checksums.json').write_text(json.dumps(checks,indent=2)+'\n')
print(a.alias,len(checks),'shards verified')
