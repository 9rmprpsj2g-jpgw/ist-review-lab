"""Instrumentation contracts using mocked fits, not retrieval ground-truth fixtures."""
import json
import unittest
from unittest.mock import patch
import numpy as np
from scipy.sparse import eye
from src.audit import seed_round, externalize_round, replay_row_order
from src.learner import ReviewLearner, POLICIES
from src.config import resolve_plan


class Phase3Contracts(unittest.TestCase):
    def test_complete_audit_only_replay_all_policies(self):
        X = eye(128, format="csr")
        ids = [f"doc-{i}" for i in range(X.shape[0])]
        for policy in POLICIES:
            with self.subTest(policy=policy):
                learner = ReviewLearner(X, policy, seed=11)
                learner.observe([0], [1])
                order = [0]
                rounds = [externalize_round(seed_round(0, learner.batch_size), ids)]
                # Margins are mock inputs, not independently claimed retrieval truth.
                with patch("sklearn.svm.LinearSVC.fit", return_value=None), patch(
                    "sklearn.svm.LinearSVC.decision_function",
                    side_effect=lambda matrix: np.asarray(matrix.argmax(axis=1)).ravel().astype(float)
                ):
                    while len(order) < X.shape[0]:
                        selected = learner.query(X.shape[0]-len(order))
                        learner.observe(selected, np.zeros(len(selected), dtype=int))
                        order.extend(selected.tolist())
                        record = externalize_round(learner.last_round, ids)
                        self.assertEqual(record["selected_rows"], selected.tolist())
                        self.assertEqual(record["selected_document_ids"], [ids[r] for r in selected])
                        if record["fit"] is not None:
                            fit = record["fit"]
                            self.assertGreaterEqual(fit["fit_seconds"], 0)
                            self.assertEqual(fit["model_parameters"], learner.model.get_params())
                            self.assertEqual(record["temporary_negative_document_ids"],
                                             [ids[r] for r in learner.last_temporary])
                        else:
                            self.assertEqual(record["temporary_negative_document_ids"], [])
                        margins = record["candidate_margins"]
                        if policy not in ("random", "seed_similarity"):
                            self.assertEqual(set(margins["rows"]), set(range(len(ids)))-set(order[:-len(selected)]))
                            np.testing.assert_array_equal(margins["values"], np.asarray(margins["rows"], dtype=float))
                        else:
                            self.assertIsNone(margins)
                        rounds.append(record)
                audit = json.loads(json.dumps({"schema_version": 3, "rounds": rounds}, allow_nan=False))
                with patch("src.learner.new_svm", side_effect=AssertionError("Replay invoked a model")):
                    self.assertEqual(replay_row_order(audit), order)
                self.assertEqual(sum(r["fit"] is not None for r in rounds), learner.fit_count)

    def test_fit_timer_measures_fit_call(self):
        learner = ReviewLearner(eye(12, format="csr"))
        learner.observe([0], [1])
        # Mock clock values are test inputs; no claimed measured runtime fixture.
        ticks = [10., 12.]
        with patch("src.learner.time.perf_counter", side_effect=ticks), patch("sklearn.svm.LinearSVC.fit"):
            learner.fit()
        self.assertEqual(learner.last_fit["fit_seconds"], ticks[1]-ticks[0])

    def test_invalid_audit_and_unauthorized_truncation_rejected(self):
        with self.assertRaises(ValueError):
            resolve_plan({"audit": {"margin_scope": "top_n"}})
        record = externalize_round(seed_round(0, 1), ["external"])
        audit = {"schema_version": 3, "rounds": [record, {**record, "round_index": 1}]}
        with self.assertRaises(ValueError):
            replay_row_order(audit)
