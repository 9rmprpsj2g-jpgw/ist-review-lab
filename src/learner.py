"""Label-blind ranking. Only observe() can supply reviewed labels.

Auto TAR's temporary negatives are never recorded as reviewer judgments.
The SVM implementation is an explicit deviation from the paper's SVMlight.
"""
import math
import numpy as np
from sklearn.svm import LinearSVC

POLICIES = ("random", "seed_similarity", "frozen_svm", "uncertainty",
            "auto_tar", "fixed_20", "explore_10")


def new_svm(seed=0):
    return LinearSVC(C=1.0, loss="hinge", dual=True, tol=1e-4,
                     max_iter=10000, random_state=int(seed))


class ReviewLearner:
    def __init__(self, X, policy="auto_tar", seed=0):
        if policy not in POLICIES:
            raise ValueError(f"Unknown policy: {policy}")
        self.X = X
        self.policy = policy
        self.rng = np.random.default_rng(seed)
        self.seed = seed
        self.labels = {}  # Real judgments only.
        self.batch_size = 20 if policy == "fixed_20" else 1
        self.model = None
        self.last_temporary = np.array([], dtype=int)
        self.fit_count = 0

    def observe(self, indices, labels):
        indices, labels = list(indices), list(labels)
        if len(indices) != len(labels):
            raise ValueError("One label is required for each document.")
        if len(indices) != len(set(indices)):
            raise ValueError("A document occurs twice in the batch.")
        for i, label in zip(indices, labels):
            if i in self.labels:
                raise ValueError("A reviewed document cannot be counted twice.")
            if label not in (0, 1) or not 0 <= i < self.X.shape[0]:
                raise ValueError("Labels must be 0 or 1, with valid row indices.")
        self.labels.update({int(i): int(v) for i, v in zip(indices, labels)})

    def remaining(self):
        mask = np.ones(self.X.shape[0], dtype=bool)
        mask[list(self.labels)] = False
        return np.flatnonzero(mask)

    def fit(self):
        if 1 not in self.labels.values():
            raise ValueError("Supply at least one confirmed relevant seed.")
        candidates = self.remaining()
        # Deliberately sample only unreviewed documents to avoid contradictory
        # copies of already reviewed positives. Recorded as a paper deviation.
        self.last_temporary = self.rng.choice(
            candidates, min(100, len(candidates)), replace=False)
        train_ids = np.array(list(self.labels) + self.last_temporary.tolist())
        train_y = np.array(list(self.labels.values()) + [0]*len(self.last_temporary))
        if len(np.unique(train_y)) < 2:
            raise ValueError("No unreviewed or confirmed negative examples remain.")
        self.model = new_svm(self.seed)
        self.model.fit(self.X[train_ids], train_y)
        self.fit_count += 1

    def rank(self):
        candidates = self.remaining()
        if not len(candidates):
            return candidates
        if self.policy == "random":
            return self.rng.permutation(candidates)
        if self.policy == "seed_similarity":
            seed_id = next(i for i, v in self.labels.items() if v == 1)
            scores = (self.X[candidates] @ self.X[seed_id].T).toarray().ravel()
        else:
            if self.model is None or self.policy != "frozen_svm":
                self.fit()
            scores = self.model.decision_function(self.X[candidates])
            if self.policy == "uncertainty":
                scores = -np.abs(scores)
        # Fixed row-index tie-breaking, independent of relevance labels.
        return candidates[np.lexsort((candidates, -scores))]

    def query(self, limit):
        ranked = self.rank()
        size = min(self.batch_size, int(limit), len(ranked))
        if self.policy == "explore_10" and size >= 10:
            n_explore = max(1, int(size * 0.1))
            exploit = ranked[:size-n_explore]
            explore = self.rng.choice(ranked[size-n_explore:], n_explore, replace=False)
            selected = np.concatenate([exploit, explore])
        else:
            selected = ranked[:size]
        if self.policy != "fixed_20":
            self.batch_size += math.ceil(self.batch_size / 10)
        return selected
