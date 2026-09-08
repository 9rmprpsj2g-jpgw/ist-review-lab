"""Mocked orchestration/fit contracts; no research fixture or census/model runs."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import warnings
from scipy.sparse import eye
from sklearn.exceptions import ConvergenceWarning
from src.learner import ReviewLearner
from src.durable_io import atomic_json
from src.local_runtime import paths, resolved_config, ROOT, check_environment, check_worktree

spec = importlib.util.spec_from_file_location('local_census_contract', ROOT/'scripts/local_census.py')
runner = importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)


class LocalCensusContracts(unittest.TestCase):
    def test_generated_manifest_does_not_block_resume_but_source_edits_do(self):
        with patch('src.local_runtime.subprocess.check_output', return_value='?? audit_manifests/contract.json\n'):
            check_worktree('contract')
        with patch('src.local_runtime.subprocess.check_output', return_value=' M src/learner.py\n?? audit_manifests/contract.json\n'):
            with self.assertRaises(RuntimeError):
                check_worktree('contract')

    def test_warning_recorded_and_fit_continues_even_with_error_filter(self):
        learner = ReviewLearner(eye(12, format='csr'), 'auto_tar', 11)
        learner.observe([0], [1])
        def fake_fit(model, X, y):
            model.n_iter_ = model.max_iter
            warnings.warn('injected non-convergence', ConvergenceWarning)
            return model
        with warnings.catch_warnings():
            warnings.simplefilter('error', ConvergenceWarning)
            with patch('sklearn.svm.LinearSVC.fit', autospec=True, side_effect=fake_fit):
                learner.fit()
                learner.fit()
        self.assertEqual(learner.fit_count, 2)
        self.assertFalse(learner.last_fit['converged'])
        self.assertEqual(learner.last_fit['n_iter'], learner.model.max_iter)
        self.assertEqual(learner.last_fit['warnings'][0]['category'], 'ConvergenceWarning')

    def test_resume_validates_and_skips_completed_pair(self):
        task = ('synthetic', 11, 'random', 3)
        entry = {'filename': 'synthetic_11_random.json', 'sha256': 'trusted'}
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); atomic_json(root/entry['filename'], {})
            atomic_json(root/'receipts'/entry['filename'], {})
            with patch.object(runner, 'validate_completed', return_value=(entry, {'reviewed': 3})) as verify:
                found, results = runner.recover_completed([task], root, {}, {}, [entry])
            self.assertEqual(set(found), {task})
            self.assertEqual(results[task]['reviewed'], task[3])
            verify.assert_called_once()

    def test_resume_never_replaces_expected_digest(self):
        task = ('synthetic', 11, 'random', 3)
        entry = {'filename': 'synthetic_11_random.json', 'sha256': 'trusted'}
        original = copy.deepcopy(entry)
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); atomic_json(root/entry['filename'], {})
            atomic_json(root/'receipts'/entry['filename'], {})
            with patch.object(runner, 'validate_completed', return_value=({**entry, 'sha256': 'changed'}, {})):
                with self.assertRaises(AssertionError):
                    runner.recover_completed([task], root, {}, {}, [entry])
        self.assertEqual(entry, original)

    def test_orphan_preserved_but_not_counted_as_complete(self):
        task = ('synthetic', 11, 'random', 3)
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); path = root/'synthetic_11_random.json'; value = {'diagnostic': True}
            atomic_json(path, value)
            with patch('src.census.validate_audit'):
                found, results = runner.recover_completed([task], root, {}, {}, [])
            self.assertEqual(found, {}); self.assertEqual(results, {})
            self.assertFalse(path.exists())
            preserved = list((root/'uncommitted').glob('*.json'))
            self.assertEqual(len(preserved), 1)
            self.assertEqual(json.loads(preserved[0].read_text()), value)

    def test_local_grid_and_path_validation(self):
        with self.assertRaises(ValueError):
            paths('../results')
        config = resolved_config('contract-only')
        self.assertEqual(config['budget'], 23149)
        self.assertEqual(len(config['topics'])*len(config['seeds'])*len(config['policies']), 180)
        self.assertEqual(config['svm']['max_iter'], json.loads((ROOT/'experiment_plan_v2.json').read_text())['svm']['max_iter'])

    def test_missing_convergence_metadata_is_rejected(self):
        audit = {'rounds': [{'fit': {'fit_seconds': 1, 'model_parameters': {'max_iter': 100}}}]}
        with self.assertRaises(AssertionError):
            runner.summarize_convergence(audit, {'max_iter': 100})

    def test_linux_production_guard(self):
        with patch('src.local_runtime.sys.platform', 'linux'):
            with self.assertRaisesRegex(RuntimeError, 'sandbox census prohibited'):
                check_environment('contract-only')
