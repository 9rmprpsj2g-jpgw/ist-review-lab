"""Paired instrumentation contracts; no fitted models or retrieval fixtures."""
import unittest
from unittest.mock import patch
import numpy as np
from scipy.sparse import eye
from src.learner import ReviewLearner


class MarginScopeContracts(unittest.TestCase):
    def test_scope_preserves_selection_and_retains_ranked_union(self):
        X = eye(2400, format='csr')
        for policy in ('auto_tar', 'uncertainty', 'explore_10'):
            for batch_size in (20, 1200):
                with self.subTest(policy=policy,batch_size=batch_size):
                    records, selections = [], []
                    for scope in ('full','top_1000_plus_selected'):
                        learner=ReviewLearner(X,policy,11,{'audit':{'margin_scope':scope}})
                        learner.observe([0],[1]); learner.batch_size=batch_size
                        with patch('sklearn.svm.LinearSVC.fit'), patch(
                            'sklearn.svm.LinearSVC.decision_function',
                            side_effect=lambda matrix: np.asarray(matrix.argmax(axis=1)).ravel().astype(float)):
                            selections.append(learner.query(batch_size))
                        records.append(learner.last_round)
                    np.testing.assert_array_equal(*selections)
                    full, small=records
                    rows=np.asarray(full['candidate_margins']['rows'])
                    values=np.asarray(full['candidate_margins']['values'])
                    scores=-abs(values) if policy=='uncertainty' else values
                    ranked=rows[np.lexsort((rows,-scores))]
                    expected=set(ranked[:1000]) | set(selections[0])
                    self.assertEqual(set(small['candidate_margins']['rows']),expected)
                    self.assertEqual(small['candidate_count'],len(rows))
                    self.assertEqual(small['margin_scope'],'top_1000_plus_selected')
                    lookup=dict(zip(rows,values))
                    self.assertEqual(small['candidate_margins']['values'],
                                     [lookup[r] for r in small['candidate_margins']['rows']])
