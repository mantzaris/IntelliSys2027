"""Prospective repository freeze after integrity and native-token checks."""
import json
from pathlib import Path
from rep_sensitivity.schema import digest
from rep_sensitivity.storage import immutable_json, utcnow

read = lambda p: json.loads(Path(p).read_text())
config = read('configs/root-diagnostic-v1.json')
source = digest({p.name: p.read_text() for p in Path('src/rep_sensitivity').glob('*.py')})
tests = read('records/tests/interpretation-root-v1.json')
eligible = [read(p) for p in Path('records/preflight').glob('root-diagnostic-v1-*.json')
            if read(p)['source_sha256'] == source and read(p)['config_sha256'] == digest(config)]
if not tests['successful'] or tests['source_sha256'] != source or len(eligible) != 1:
    raise RuntimeError('Matching successful tests and unique native-token preflight required')
preflight = eligible[0]
frozen = {**config, 'status': 'frozen'}
record = {'utc': utcnow(), 'config_sha256': digest(frozen), 'source_sha256': source,
          'test_record_sha256': digest(tests), 'preflight_sha256': digest(preflight),
          'source_pilot_manifest_sha256': digest(read(Path(config['source_run'])/'manifest.json')),
          'controller_sha256': digest(Path('scripts/run_root_diagnostic.py').read_text()),
          'model_record_sha256': digest(read('records/models/qwen3.json')),
          'analysis': 'root_diagnostic.analyze in the same immutable source snapshot',
          'registration': 'Prospective repository freeze of exploratory development diagnostic, not external registration.',
          'heldout_outcomes_inspected': False, 'amendment': 'PROTOCOL_AMENDMENT_V2.md'}
immutable_json('configs/frozen/root-diagnostic-v1.json', frozen)
immutable_json('records/freezes/root-diagnostic-v1.json', record)
print(json.dumps(record))
