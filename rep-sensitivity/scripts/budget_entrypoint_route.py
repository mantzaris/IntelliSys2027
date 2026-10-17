"""Use budget-only controller derivatives at the next process boundary.

The running supervisor retains its original queue. This narrowly scoped startup
hook redirects only its three future additional-budget controllers. It never
changes model imports, requests, sampling, cache keys or the active process.
"""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sys
from datetime import datetime, timezone


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def routed_command(argv, config, project):
    """Return an exact validated substitution, or None for unrelated commands."""
    if not argv or argv[0].startswith('-'):
        return None
    original = Path(argv[0]).resolve()
    project = Path(project).resolve()
    for route in config['routes']:
        if original != (project / route['original_entrypoint']).resolve():
            continue
        if sha256(original) != route['original_entrypoint_sha256']:
            raise RuntimeError('Changed original budget controller')
        replacement = project / route['replacement_entrypoint']
        if replacement.resolve() == original:
            raise RuntimeError('Recursive budget controller route')
        for name, expected in route['replacement_files_sha256'].items():
            if sha256(replacement.parent / name) != expected:
                raise RuntimeError('Changed budget-only derivative: ' + name)
        return [str(replacement), *argv[1:]]
    return None


def install(argv, manifest_path, manifest_sha256):
    path = Path(manifest_path).resolve()
    if sha256(path) != manifest_sha256:
        raise RuntimeError('Changed budget routing manifest')
    config = json.loads(path.read_text())
    if sha256(__file__) != config['routing_adapter_sha256']:
        raise RuntimeError('Changed budget routing adapter')
    project = path.parents[2]
    segment = os.environ.get('REP_EXECUTION_SEGMENT')
    if not segment or Path(segment).resolve() != (project / config['execution_segment']).resolve():
        return
    command = routed_command(argv, config, project)
    if command is None:
        return
    if Path.cwd().resolve() != project:
        raise RuntimeError('Budget controller started outside project')
    if sha256(project / config['allowance_record']) != config['allowance_sha256']:
        raise RuntimeError('Changed GPU allowance record')
    event = {'utc': datetime.now(timezone.utc).isoformat(), 'event': 'budget_controller_route',
        'pid': os.getpid(), 'original_arguments': argv, 'actual_arguments': command,
        'routing_manifest': str(path.relative_to(project)), 'routing_manifest_sha256': manifest_sha256,
        'allowance_record': config['allowance_record'], 'allowance_sha256': config['allowance_sha256'],
        'preflight_only': '--help' in argv}
    journal = project / config['routing_event_log']
    journal.parent.mkdir(parents=True, exist_ok=True)
    with journal.open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        stream.write(json.dumps(event) + '\n')
        stream.flush()
        os.fsync(stream.fileno())
    environment = dict(os.environ)
    # exec keeps the PID but starts a fresh interpreter. The hardware provenance
    # hook must reinstall its import finder in that interpreter.
    environment.pop('REP_EXECUTION_SEGMENT_ACTIVE', None)
    os.execve(sys.executable, [sys.executable, *command], environment)


if __name__ == 'rep_budget_entrypoint_route':
    try:
        install(startup_argv, routing_manifest, routing_manifest_sha256)
    except BaseException as error:
        print('Budget routing startup failed: ' + repr(error), file=sys.stderr, flush=True)
        os._exit(78)
