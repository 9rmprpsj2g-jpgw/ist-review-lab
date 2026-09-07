"""Census schedule and margin-window contracts; mocked fits only."""
import math
import unittest
from unittest.mock import patch
import numpy as np
from scipy.sparse import eye
from src.learner import ReviewLearner
from src.audit import externalize_round,seed_round


class CensusContracts(unittest.TestCase):
    def test_widened_window_and_selection_identity(self):
        X=eye(2600,format='csr')
        for policy in ('auto_tar','uncertainty','explore_10','grow_5pct','grow_20pct'):
            for size in (20,1200,2500):
                with self.subTest(policy=policy,size=size):
                    observed=[]
                    for scope in ('full','batch_plus_100_min_1000_plus_selected'):
                        learner=ReviewLearner(X,policy,11,{'audit':{'margin_scope':scope}})
                        learner.observe([0],[1]);learner.batch_size=size
                        with patch('sklearn.svm.LinearSVC.fit'),patch('sklearn.svm.LinearSVC.decision_function',
                            side_effect=lambda matrix:np.asarray(matrix.argmax(axis=1)).ravel().astype(float)):
                            selected=learner.query(size)
                        observed.append((selected,learner.last_round))
                    np.testing.assert_array_equal(observed[0][0],observed[1][0])
                    full=observed[0][1]['candidate_margins'];r=observed[1][1]
                    rows=np.asarray(full['rows']);values=np.asarray(full['values'])
                    scores=-abs(values) if policy=='uncertainty' else values
                    rank=rows[np.lexsort((rows,-scores))]
                    window=max(1000,size+100)
                    self.assertEqual(r['margin_window_requested'],window)
                    self.assertEqual(r['margin_window_resolved'],min(window,len(rows)))
                    self.assertEqual(set(r['candidate_margins']['rows']),set(rank[:window])|set(observed[0][0]))

    def test_new_schedule_recurrences(self):
        for policy in ('fixed_10','fixed_50','fixed_100','grow_5pct','grow_20pct'):
            learner=ReviewLearner(eye(5000,format='csr'),policy)
            if policy.startswith('fixed_'):
                expected=int(policy.split('_')[1])
            else:expected=1
            for _ in range(12):
                before=expected
                with patch.object(learner,'rank',return_value=np.arange(5000)):
                    selected=learner.query(5000)
                self.assertEqual(len(selected),before)
                if policy.startswith('grow_'):
                    rate=int(policy.split('_')[1].replace('pct',''))
                    expected+=math.ceil(before*rate/100)
                self.assertEqual(learner.batch_size,expected)

    def test_seed_scope_metadata(self):
        scope='batch_plus_100_min_1000_plus_selected'
        row=externalize_round(seed_round(0,1,scope),['a','b'])
        self.assertEqual(row['margin_scope'],scope)
        self.assertEqual(row['candidate_count'],len(['b']))
        self.assertIsNone(row['candidate_margins'])
