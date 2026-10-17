"""One-time completion message to the requesting Codex chat; no GPU execution."""
import argparse
from datetime import datetime, timezone
import fcntl
import json
from pathlib import Path
import subprocess
import time
import uuid


def read_json(path):
    try:
        return json.loads(Path(path).read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def completion_ready(project, not_before):
    """Require the completed queue, audited local package and matching commit."""
    project = Path(project)
    queue = read_json(project / 'artifacts/runs/replacement-ada-execution/complete.json')
    review = read_json(project / 'records/review-package.json')
    committed = read_json(project / 'artifacts/review-package-commit.json')
    if not queue or not review or not committed:
        return False
    identity = review.get('completion_input_sha256')
    return bool(queue.get('queue_finished') and review.get('raw_completeness_checked') and
        identity and committed.get('completion_input_sha256') == identity and
        review.get('assembled_utc', '') >= not_before and
        {'main-v7', 'supporting-v7', 'live-v8', 'objective-confirmation-v1'} <=
        set(review.get('completed_analysis_stages', [])))


def message(complete):
    if complete:
        return (
            'Automated completion notice requested by the user in this chat. '
            'rep-sensitivity has a completed replacement-pod queue and a locally mirrored, '
            'audited review package with a matching completion commit. Verify '
            'rep-sensitivity/records/review-package.json, artifacts/review-package-commit.json, '
            'and the stage markers. Then send the user a concise completion message here, '
            'distinguishing completed and budget-skipped experiments, actual results, and '
            'pending human scientific review. Do not start new experiments or claim completion '
            'if verification fails. This message is an automated check, not evidence by itself.'
        )
    return (
        'The user-requested rep-sensitivity completion watcher reached its 72-hour deadline '
        'without a verified completed review package. Check the existing controller and local '
        'mirror, then report the actual status in this chat. Do not claim completion or start '
        'additional experiments merely because this notification was triggered.'
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    config_path = Path(args.config).resolve()
    config = json.loads(config_path.read_text())
    uuid.UUID(config['thread_id'])
    project = Path(config['project']).resolve()
    state = config_path.parent
    with (state / '.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (state / 'delivery-attempt.json').exists():
            return  # Never repeat an ambiguously accepted queued message.
        while True:
            complete = completion_ready(project, config['created_utc'])
            expired = datetime.now(timezone.utc).timestamp() >= config['deadline_epoch']
            if args.check_only:
                print(json.dumps({'completion_ready': complete, 'deadline_expired': expired,
                    'message_sent': False}))
                return
            if complete or expired:
                attempt = {'utc': datetime.now(timezone.utc).isoformat(),
                    'completion_ready': complete, 'reason': 'complete' if complete else 'deadline',
                    'thread_id': config['thread_id']}
                with (state / 'delivery-attempt.json').open('x') as stream:
                    stream.write(json.dumps(attempt, indent=2) + '\n')
                command = [config['codex_binary'], 'queue', '--thread', config['thread_id'],
                    '--message', message(complete)]
                try:
                    result = subprocess.run(command, cwd=project.parent, capture_output=True,
                        text=True, timeout=60)
                    delivery = {'returncode': result.returncode,
                        'stdout': result.stdout, 'stderr': result.stderr,
                        'queued': result.returncode == 0}
                except subprocess.TimeoutExpired:
                    delivery = {'queued': None, 'error': 'Ambiguous timeout; no automatic duplicate'}
                (state / 'delivery-result.json').write_text(json.dumps(delivery, indent=2) + '\n')
                print(json.dumps(delivery), flush=True)
                return
            (state / 'heartbeat.json').write_text(json.dumps({
                'utc': datetime.now(timezone.utc).isoformat(), 'completion_ready': False}) + '\n')
            time.sleep(60)


if __name__ == '__main__':
    main()
