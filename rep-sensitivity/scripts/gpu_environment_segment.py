"""Record replacement hardware without altering frozen inference or cache keys.

Installed as an opt-in .pth startup hook on the study's remote virtualenv.
Only the two frozen model-module namespaces below are intercepted. Their source
bytes must match the prospective runtime manifest. Prompts, decoding, seeds,
precision, batching and accepted-response lookup remain in the archived code.
"""
import functools
import hashlib
import importlib.abc
import importlib.machinery
import json
import os
from pathlib import Path
import sys


def patch_model_module(module, config):
    if getattr(module, '_execution_segment_installed', False):
        return
    source_hash = hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
    if source_hash not in config['allowed_model_source_sha256']:
        raise RuntimeError('Unrecognized frozen model adapter')
    record_id = config['segment_id']
    if Path(record_id).name != record_id or record_id in ('.', '..'):
        raise ValueError('Invalid environment segment name')
    original_write = module.immutable_json

    def environment_write(path, value):
        path = Path(path)
        if path.parent.resolve() == Path('records/environment').resolve():
            # The original file continues to describe the old GPU. A new driver
            # must never overwrite it merely because model settings are equal.
            value = {**value, 'execution_segment': record_id,
                'execution_manifest': config['manifest_path'],
                'runtime_adapter_sha256': config['runtime_adapter_sha256'],
                'frozen_model_source_sha256': source_hash}
            path = path.parent / record_id / path.name
        return original_write(path, value)

    original_run = module.LocalModel.run

    @functools.wraps(original_run)
    def run_with_segment(self, requests):
        responses = original_run(self, requests)
        for response in responses:
            if 'execution_segment' in response:
                raise RuntimeError('Ambiguous duplicate runtime tagging')
            response['execution_segment'] = record_id
            response['execution_manifest'] = config['manifest_path']
            response['runtime_adapter_sha256'] = config['runtime_adapter_sha256']
        return responses

    module.immutable_json = environment_write
    module.LocalModel.run = run_with_segment
    module._execution_segment_installed = True


class SegmentLoader(importlib.abc.Loader):
    def __init__(self, delegate, config):
        self.delegate, self.config = delegate, config

    def create_module(self, spec):
        method = getattr(self.delegate, 'create_module', None)
        return method(spec) if method else None

    def exec_module(self, module):
        self.delegate.exec_module(module)
        patch_model_module(module, self.config)


class SegmentFinder(importlib.abc.MetaPathFinder):
    def __init__(self, config):
        self.config = config

    def find_spec(self, fullname, path=None, target=None):
        if fullname not in ('rep_sensitivity.models', 'rep_replay_frozen.models'):
            return None
        spec = importlib.machinery.PathFinder.find_spec(fullname, path, target)
        if spec is not None and spec.loader is not None:
            spec.loader = SegmentLoader(spec.loader, self.config)
        return spec


def install():
    path = os.environ.get('REP_EXECUTION_SEGMENT')
    if not path:
        return
    config = json.loads(Path(path).read_text())
    observed = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if observed != config['runtime_adapter_sha256']:
        raise RuntimeError('Changed execution adapter')
    if os.environ.get('REP_EXECUTION_SEGMENT_ACTIVE') == str(os.getpid()):
        return
    sys.meta_path.insert(0, SegmentFinder(config))
    for name in ('rep_sensitivity.models', 'rep_replay_frozen.models'):
        if name in sys.modules:
            patch_model_module(sys.modules[name], config)
    os.environ['REP_EXECUTION_SEGMENT_ACTIVE'] = str(os.getpid())


if __name__ == 'rep_gpu_environment_segment':
    try:
        install()
    except BaseException as error:
        # Python otherwise prints a .pth error and continues without the hook.
        # Fail closed before any experiment can execute without provenance.
        print('Execution-segment startup failed: ' + repr(error), file=sys.stderr, flush=True)
        os._exit(78)
