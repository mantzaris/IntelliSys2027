"""Add a deterministic mutation sidecar without changing frozen experimental data."""
import argparse
import json
from pathlib import Path
from rep_sensitivity.mutations import describe
from rep_sensitivity.schema import digest
from rep_sensitivity.storage import immutable_json

p=argparse.ArgumentParser();p.add_argument('run');a=p.parse_args()
root=Path(a.run);pairs=json.loads((root/'pairs.json').read_text())
records=[describe(pair) for pair in pairs]
immutable_json(root/'mutation-records-v1.json',records)
immutable_json(Path('records/mutations')/(root.name+'.json'),{
    'suite':root.name,'base_pairs':len(records),'mutation_records_sha256':digest(records),
    'source_pairs_sha256':digest(pairs),'preconditions_verified':all(r['preconditions_verified'] for r in records)})
print(json.dumps({'base_pairs':len(records),'mutation_records_sha256':digest(records)}))
