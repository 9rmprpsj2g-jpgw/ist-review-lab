"""Contract/regression checks only: no collection loader, experiments or metric fixtures."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from fractions import Fraction
from unittest.mock import patch, Mock

import numpy as np
from scipy.sparse import eye
from src.config import resolve_plan
from src.learner import ReviewLearner, named_streams, new_svm, STREAM_NAMES
from src.experiment import write_configuration, output_directory
from src.data import ROOT


class Phase2Contracts(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads((ROOT/"experiment_plan_v2.json").read_text())

    def test_C_configuration_reaches_instantiated_model(self):
        changed = copy.deepcopy(self.plan)
        changed["svm"]["C"] = 2.5
        original = new_svm(11,self.plan)
        model = new_svm(11,changed)
        self.assertEqual(model.get_params()["C"], changed["svm"]["C"])
        self.assertNotEqual(original.get_params()["C"], model.get_params()["C"])
        learner = ReviewLearner(eye(12,format="csr"),seed=11,plan=changed)
        learner.observe([0],[1])
        # No actual model training; test the fit path's constructor wiring.
        with patch("sklearn.svm.LinearSVC.fit",return_value=None):
            learner.fit()
        self.assertEqual(learner.model.get_params()["C"], changed["svm"]["C"])

    def test_unknown_config_keys_rejected(self):
        for bad in ({"epslion":.1},{"svm":{"CC":2}},{"outputs":{"direcotry":"x"}},{"analysis":{"bootstraps":3}}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                resolve_plan(bad)

    def test_epsilon_validation(self):
        for epsilon in (-.1,1.1,float("nan"),True):
            with self.subTest(epsilon=epsilon), self.assertRaises(ValueError):
                resolve_plan({"epsilon":epsilon})

    def test_streams_reproducible_and_isolated(self):
        for name in STREAM_NAMES:
            left,right=named_streams(29),named_streams(29)
            for other in STREAM_NAMES:
                if other != name:
                    left[other].random(100)
            np.testing.assert_array_equal(left[name].integers(0,100000,size=50),right[name].integers(0,100000,size=50))
        self.assertNotEqual(named_streams(11)["seed_doc"].bit_generator.state,
                            named_streams(11)["temp_negatives"].bit_generator.state)

    def test_eligible_exploration_carry_and_gate(self):
        for epsilon in (0,.1,.23,1):
            learner=ReviewLearner(eye(2000,format="csr"),"explore_10",plan={"epsilon":epsilon})
            eligible=total=0
            for size in (1,4,9,10,11,19,20,31,99,7):
                learner.batch_size=size
                rng=Mock()
                rng.choice.side_effect=lambda values,count,replace=False: values[-count:] if count else values[:0]
                learner.streams["exploration"]=rng
                with patch.object(learner,"rank",return_value=np.arange(2000)):
                    selected=learner.query(size)
                self.assertEqual(len(selected),size)
                self.assertEqual(len(set(selected)),size)
                if size < 10:
                    rng.choice.assert_not_called()
                else:
                    eligible+=size
                    total+=rng.choice.call_args.args[1]
                gap=Fraction(str(epsilon))*eligible-total
                self.assertGreaterEqual(gap,0)
                self.assertLess(gap,1)

    def test_renamed_policy_stays_frozen_and_auto_retrains(self):
        for policy in ("seed_only_frozen","auto_tar"):
            learner=ReviewLearner(eye(8,format="csr"),policy)
            def fit():
                learner.model=Mock()
                learner.model.decision_function.return_value=np.arange(8)
            with patch.object(learner,"fit",side_effect=fit) as spy:
                learner.rank();learner.rank()
            self.assertEqual(spy.call_count,1 if policy=="seed_only_frozen" else 2)
        with self.assertRaises(ValueError):
            ReviewLearner(eye(8),"frozen_svm")

    def test_snapshots_record_actual_parameters(self):
        with tempfile.TemporaryDirectory() as temporary:
            resolved=write_configuration(self.plan,temporary)
            self.assertEqual(json.loads((Path(temporary)/"resolved_config.json").read_text()),resolved)
            actual=json.loads((Path(temporary)/"model_parameters.json").read_text())
            for seed in self.plan["seeds"]:
                self.assertEqual(actual[str(seed)],new_svm(seed,resolved).get_params())
        for path in (ROOT/"results",ROOT/"results/audits"):
            with self.assertRaises(ValueError):
                output_directory(path)


if __name__=="__main__":
    unittest.main()
