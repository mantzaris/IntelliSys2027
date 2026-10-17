"""Archive budget-only derivatives without changing scientific source snapshots."""
import hashlib
import json
from pathlib import Path

from authorized_gpu_budget import ALLOWANCE_RECORD, ALLOWANCE_SHA256, authorized_cap


ORIGINALS = {
    'objective-confirmation': 'cc8294c88b1248805dc3a4611bf6032c1f3f113c5a98bbe86264f7f24c8d8ac3',
    'numerical-preservation': '334ad32ea09d2210209b8e8e19e11f46e2f52d5fd97e49407227f912253658e9',
    'adjacent-explorations': '83c76e24aaa4e440be5c068f624736fea11c4227e9c3db7a30fa6aa14227e28c',
}


def hash_bytes(value):
    return hashlib.sha256(value).hexdigest()


def immutable_write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise RuntimeError('Immutable artifact differs: ' + str(path))
    else:
        with path.open('xb') as stream:
            stream.write(data)


def main():
    cap = authorized_cap()
    routes = []
    for stage, original in ORIGINALS.items():
        source = Path('artifacts/implementations') / original
        contents = {str(p.relative_to(source)): p.read_bytes() for p in source.rglob('*')
            if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
        runner = contents['runner.py'].decode()
        old = ("config['additional_gpu_wall_seconds_cap']-prior_seconds(events)"
               if stage == 'objective-confirmation' else '7200-prior_seconds(events)')
        new = ("authorized_cap(config['additional_gpu_wall_seconds_cap'])-prior_seconds(events)"
               if stage == 'objective-confirmation' else
               "authorized_cap(config['shared_gpu_wall_seconds_cap'])-prior_seconds(events)")
        if runner.count(old) != 1:
            raise RuntimeError('Unexpected frozen budget expression: ' + stage)
        runner = runner.replace(old, new)
        marker = '\ndef main():'
        if runner.count(marker) != 1:
            raise RuntimeError('Unexpected frozen controller structure')
        runner = runner.replace(marker, '\nfrom authorized_gpu_budget import authorized_cap\n' + marker)
        revised = {**contents, 'runner.py': runner.encode(),
            'authorized_gpu_budget.py': Path('scripts/authorized_gpu_budget.py').read_bytes()}
        hashes = {name: hash_bytes(data) for name, data in sorted(revised.items())}
        archive_id = hash_bytes(json.dumps(hashes, sort_keys=True).encode())
        destination = Path('artifacts/implementations') / archive_id
        for name, data in revised.items():
            immutable_write(destination / name, data)
        # All model, task, prompt, scoring and analysis files retain their bytes.
        unchanged = [name for name in contents if name != 'runner.py']
        assert all(revised[name] == contents[name] for name in unchanged)
        routes.append({'stage': stage, 'original_entrypoint': str(source / 'runner.py'),
            'original_entrypoint_sha256': hash_bytes(contents['runner.py']),
            'replacement_entrypoint': str(destination / 'runner.py'),
            'replacement_files_sha256': hashes, 'unchanged_original_file_count': len(unchanged),
            'changed_existing_files': ['runner.py'], 'added_files': ['authorized_gpu_budget.py']})
    adapter = Path('scripts/budget_entrypoint_route.py').read_bytes()
    adapter_hash = hash_bytes(adapter)
    adapter_path = Path('artifacts/runtime-adapters') / adapter_hash / 'budget_entrypoint_route.py'
    immutable_write(adapter_path, adapter)
    manifest = {'amendment_id': 'additional-gpu-allowance-v2', 'cumulative_cap_seconds': cap,
        'allowance_record': str(ALLOWANCE_RECORD), 'allowance_sha256': ALLOWANCE_SHA256,
        'execution_segment': 'records/execution/replacement-ada-v1.json',
        'routing_adapter': str(adapter_path), 'routing_adapter_sha256': adapter_hash,
        'routing_event_log': 'artifacts/runs/replacement-ada-execution/budget-routes.jsonl',
        'scope': 'Only future entrypoints are routed. Existing processes and scientific configurations remain unchanged.',
        'routes': routes}
    path = Path('records/execution/additional-gpu-budget-routing-v2.json')
    data = (json.dumps(manifest, indent=2, sort_keys=True) + '\n').encode()
    immutable_write(path, data)
    print(json.dumps({'manifest': str(path), 'sha256': hash_bytes(data),
        'adapter': str(adapter_path), 'routes': [r['replacement_entrypoint'] for r in routes]}))


if __name__ == '__main__':
    main()
