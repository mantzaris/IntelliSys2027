import json
from pathlib import Path
import tempfile
import unittest

from scripts.notify_study_completion import completion_ready, message


class CompletionNotificationTests(unittest.TestCase):
    def write(self, root, path, data):
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(data))

    def test_queue_finish_alone_does_not_announce_study_completion(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root, 'artifacts/runs/replacement-ada-execution/complete.json',
                {'queue_finished': True})
            self.assertFalse(completion_ready(root, '2026-10-17T00:00:00Z'))

    def test_requires_fresh_audited_package_and_matching_commit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(root, 'artifacts/runs/replacement-ada-execution/complete.json',
                {'queue_finished': True})
            review = {'raw_completeness_checked': True, 'completion_input_sha256': 'new',
                'assembled_utc': '2026-10-18T00:00:00Z',
                'completed_analysis_stages': ['main-v7', 'supporting-v7', 'live-v8', 'objective-confirmation-v1']}
            self.write(root, 'records/review-package.json', review)
            self.write(root, 'artifacts/review-package-commit.json', {'completion_input_sha256': 'old'})
            self.assertFalse(completion_ready(root, '2026-10-17T00:00:00Z'))
            self.write(root, 'artifacts/review-package-commit.json', {'completion_input_sha256': 'new'})
            self.assertTrue(completion_ready(root, '2026-10-17T00:00:00Z'))
            self.assertFalse(completion_ready(root, '2026-10-19T00:00:00Z'))
            review['raw_completeness_checked'] = False
            self.write(root, 'records/review-package.json', review)
            self.assertFalse(completion_ready(root, '2026-10-17T00:00:00Z'))

    def test_deadline_notification_does_not_claim_completion(self):
        self.assertIn('without a verified completed', message(False))
        self.assertIn('pending human scientific review', message(True))


if __name__ == '__main__':
    unittest.main()
