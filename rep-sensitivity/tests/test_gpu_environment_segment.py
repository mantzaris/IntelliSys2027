import hashlib
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from scripts.gpu_environment_segment import patch_model_module


class GPUEnvironmentSegmentTests(unittest.TestCase):
    def fixture(self, directory):
        source = Path(directory) / 'models.py'
        source.write_text('frozen adapter fixture\n')
        writes = []

        class Model:
            settings = {'precision': 'bfloat16', 'seed': 42}

            def run(self, requests):
                self.received = requests
                return [{'text': '{"value":3}', 'input_tokens': 9}]

        module = SimpleNamespace(__file__=str(source), LocalModel=Model,
            immutable_json=lambda path, value: writes.append((Path(path), value)))
        config = {'segment_id': 'replacement-ada-v1', 'manifest_path': 'records/execution/replacement.json',
            'runtime_adapter_sha256': 'frozen-runtime-hash',
            'allowed_model_source_sha256': [hashlib.sha256(source.read_bytes()).hexdigest()]}
        return module, config, writes

    def test_environment_history_is_separate_and_other_artifacts_are_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            module, config, writes = self.fixture(directory)
            patch_model_module(module, config)
            old = {'gpu': 'original'}
            module.immutable_json('records/environment/model-hash.json', old)
            module.immutable_json('artifacts/runs/example/manifest.json', old)
            self.assertEqual(writes[0][0], Path('records/environment/replacement-ada-v1/model-hash.json'))
            self.assertEqual(writes[1], (Path('artifacts/runs/example/manifest.json'), old))
            self.assertEqual(old, {'gpu': 'original'})

    def test_sampling_inputs_settings_and_response_text_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            module, config, _ = self.fixture(directory)
            patch_model_module(module, config)
            model = module.LocalModel()
            requests = [{'prompt': 'fixed evidence', 'seed': 17, 'max_output_tokens': 2304}]
            result = model.run(requests)
            self.assertIs(model.received, requests)
            self.assertEqual(model.settings, {'precision': 'bfloat16', 'seed': 42})
            self.assertEqual(result[0]['text'], '{"value":3}')
            self.assertEqual(result[0]['execution_segment'], 'replacement-ada-v1')
            self.assertEqual(result[0]['input_tokens'], 9)

    def test_unknown_source_is_rejected_before_patch(self):
        with tempfile.TemporaryDirectory() as directory:
            module, config, _ = self.fixture(directory)
            config['allowed_model_source_sha256'] = []
            with self.assertRaisesRegex(RuntimeError, 'Unrecognized'):
                patch_model_module(module, config)
            self.assertFalse(hasattr(module, '_execution_segment_installed'))

    def test_repeated_import_does_not_tag_twice(self):
        with tempfile.TemporaryDirectory() as directory:
            module, config, _ = self.fixture(directory)
            patch_model_module(module, config)
            patch_model_module(module, config)
            self.assertEqual(module.LocalModel().run([])[0]['execution_segment'], config['segment_id'])


if __name__ == '__main__':
    unittest.main()
