import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from scripts.authorized_gpu_budget import authorized_cap
from scripts import budget_entrypoint_route as router
from scripts.budget_entrypoint_route import routed_command
from scripts.run_objective_confirmation import prior_seconds
from scripts.capture_numerical_execution import unique_completed_clusters


class AuthorizedBudgetTests(unittest.TestCase):
    def test_amendment_keeps_completed_and_ambiguous_charges(self):
        events = [
            {'event': 'attempt_start', 'attempt': 'done', 'reserved_seconds': 480},
            {'event': 'attempt_end', 'attempt': 'done', 'elapsed_seconds': 450},
            {'event': 'allowance_amendment', 'cumulative_cap_seconds': 28800},
            {'event': 'attempt_start', 'attempt': 'ambiguous', 'reserved_seconds': 50},
        ]
        self.assertEqual(authorized_cap(), 28800)
        self.assertEqual(authorized_cap() - prior_seconds(events), 28300)
        self.assertEqual(prior_seconds(events), 500)

    def test_changed_authorization_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'authorization.json'
            path.write_text('{"cumulative_cap_seconds": 999999}')
            with self.assertRaisesRegex(RuntimeError, 'Changed GPU allowance'):
                authorized_cap(path=path)
        with self.assertRaisesRegex(RuntimeError, 'Invalid operational'):
            authorized_cap(900)

    def test_resume_announcements_do_not_inflate_independent_base_count(self):
        events = [
            {'event': 'cluster_complete', 'pair_id': 'one', 'trajectories': 72, 'utc': '2026-10-16T00:00:00Z'},
            {'event': 'cluster_complete', 'pair_id': 'one', 'trajectories': 72, 'utc': '2026-10-17T00:00:00Z'},
            {'event': 'cluster_complete', 'pair_id': 'two', 'trajectories': 72, 'utc': '2026-10-17T01:00:00Z'},
        ]
        unique = unique_completed_clusters(events)
        self.assertEqual(len(unique), 2)
        self.assertEqual(sum(e['trajectories'] for e in unique), 144)
        self.assertEqual(unique[0]['utc'], events[0]['utc'])


class BudgetRoutingTests(unittest.TestCase):
    def fixture(self, directory):
        project = Path(directory)
        old = project / 'old/runner.py'
        new = project / 'new/runner.py'
        old.parent.mkdir();new.parent.mkdir()
        old.write_text('original controller')
        new.write_text('budget-only controller')
        scientific = new.parent / 'models.py'
        scientific.write_text('unchanged model code')
        sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
        config = {'routes': [{'original_entrypoint': 'old/runner.py',
            'original_entrypoint_sha256': sha(old), 'replacement_entrypoint': 'new/runner.py',
            'replacement_files_sha256': {'runner.py': sha(new), 'models.py': sha(scientific)}}]}
        return project, old, new, scientific, config

    def test_only_named_entrypoint_changes_and_arguments_survive(self):
        with tempfile.TemporaryDirectory() as directory:
            project, old, new, _, config = self.fixture(directory)
            args = [str(old), '--config', 'frozen.json', '--budget-seconds', '200']
            self.assertEqual(routed_command(args, config, project), [str(new), *args[1:]])
            self.assertEqual(args[0], str(old))
            self.assertIsNone(routed_command([str(new)], config, project))
            self.assertIsNone(routed_command([str(project / 'main/runner.py')], config, project))
            self.assertIsNone(routed_command(['-c'], config, project))

    def test_scientific_source_mutation_prevents_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            project, old, _, scientific, config = self.fixture(directory)
            scientific.write_text('different precision or prompt')
            with self.assertRaisesRegex(RuntimeError, 'Changed budget-only derivative'):
                routed_command([str(old)], config, project)

    def test_original_entrypoint_mutation_prevents_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            project, old, _, _, config = self.fixture(directory)
            old.write_text('changed original')
            with self.assertRaisesRegex(RuntimeError, 'Changed original budget controller'):
                routed_command([str(old)], config, project)

    def test_reexec_reinstalls_hardware_hook_and_records_actual_arguments(self):
        with tempfile.TemporaryDirectory() as directory:
            project, old, new, _, config = self.fixture(directory)
            folder = project / 'records/execution'
            folder.mkdir(parents=True)
            allowance = folder / 'allowance.json'
            allowance.write_text('{}')
            config.update({'routing_adapter_sha256': router.sha256(router.__file__),
                'execution_segment': 'records/execution/segment.json',
                'allowance_record': 'records/execution/allowance.json',
                'allowance_sha256': router.sha256(allowance),
                'routing_event_log': 'events.jsonl'})
            manifest = folder / 'routing.json'
            manifest.write_text(json.dumps(config))
            original_cwd = Path.cwd()
            try:
                os.chdir(project)
                with mock.patch.dict(os.environ, {
                    'REP_EXECUTION_SEGMENT': str(project / config['execution_segment']),
                    'REP_EXECUTION_SEGMENT_ACTIVE': str(os.getpid()),
                }), mock.patch.object(router.os, 'execve') as execute:
                    router.install([str(old), '--help'], manifest, router.sha256(manifest))
                    args = execute.call_args.args
                    self.assertEqual(args[1][1:], [str(new), '--help'])
                    self.assertNotIn('REP_EXECUTION_SEGMENT_ACTIVE', args[2])
                    self.assertEqual(args[2]['REP_EXECUTION_SEGMENT'], str(project / config['execution_segment']))
                event = json.loads((project / 'events.jsonl').read_text())
                self.assertEqual(event['actual_arguments'], [str(new), '--help'])
                self.assertTrue(event['preflight_only'])
            finally:
                os.chdir(original_cwd)


if __name__ == '__main__':
    unittest.main()
