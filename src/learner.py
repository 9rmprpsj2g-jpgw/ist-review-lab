"""Label-blind ranking. Only observe() can supply reviewed labels.

Auto TAR's temporary negatives are never recorded as reviewer judgments.
The SVM implementation is an explicit deviation from the paper's SVMlight.
"""
import math
import hashlib
import time
from copy import deepcopy
from fractions import Fraction
import numpy as np
from sklearn.svm import LinearSVC
from .config import resolve_plan

POLICIES = ("random", "seed_similarity", "seed_only_frozen", "uncertainty",
            "auto_tar", "fixed_20", "explore_10")


STREAM_NAMES = ("seed_doc", "temp_negatives", "exploration", "certification")


def named_streams(seed):
    return {name: np.random.default_rng(int.from_bytes(
        hashlib.sha256(f"ist-review-lab|{int(seed)}|{name}".encode("utf-8")).digest(), "big"))
        for name in STREAM_NAMES}


def new_svm(seed=0, plan=None):
    return LinearSVC(**resolve_plan(plan)["svm"], random_state=int(seed))


class ReviewLearner:
    def __init__(self, X, policy="auto_tar", seed=0, plan=None):
        if policy not in POLICIES:
            raise ValueError(f"Unknown policy: {policy}")
        self.X = X
        self.policy = policy
        self.streams = named_streams(seed)
        self.config = resolve_plan(plan)
        self.epsilon = Fraction(str(self.config["epsilon"]))
        self.exploration_carry = Fraction(0)
        self.seed = seed
        self.labels = {}  # Real judgments only.
        self.batch_size = 20 if policy == "fixed_20" else 1
        self.model = None
        self.last_temporary = np.array([], dtype=int)
        self.fit_count = 0
        self.last_fit = None
        self.last_round = None
        self.round_count = 0
        self.candidate_margins = None

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
        self.last_temporary = self.streams["temp_negatives"].choice(
            candidates, min(100, len(candidates)), replace=False)
        train_ids = np.array(list(self.labels) + self.last_temporary.tolist())
        train_y = np.array(list(self.labels.values()) + [0]*len(self.last_temporary))
        if len(np.unique(train_y)) < 2:
            raise ValueError("No unreviewed or confirmed negative examples remain.")
        self.model = new_svm(self.seed, self.config)
        train_X = self.X[train_ids]
        parameters = deepcopy(self.model.get_params(deep=True))
        started = time.perf_counter()
        self.model.fit(train_X, train_y)
        elapsed = time.perf_counter() - started
        self.fit_count += 1
        self.last_fit = {"fit_index": self.fit_count,
                         "temporary_negative_rows": self.last_temporary.tolist(),
                         "model_parameters": parameters, "fit_seconds": elapsed}

    def rank(self):
        self.candidate_margins = None
        candidates = self.remaining()
        if not len(candidates):
            return candidates
        if self.policy == "random":
            # Exclusive consumer: random and explore_10 cannot coexist in a run.
            # Retain the Phase 2 stream to preserve its realized trajectories.
            return self.streams["exploration"].permutation(candidates)
        if self.policy == "seed_similarity":
            seed_id = next(i for i, v in self.labels.items() if v == 1)
            scores = (self.X[candidates] @ self.X[seed_id].T).toarray().ravel()
        else:
            if self.model is None or self.policy != "seed_only_frozen":
                self.fit()
            scores = self.model.decision_function(self.X[candidates])
            self.candidate_margins = {"rows": candidates.tolist(),
                                      "values": scores.tolist()}
            if self.policy == "uncertainty":
                scores = -np.abs(scores)
        # Fixed row-index tie-breaking, independent of relevance labels.
        return candidates[np.lexsort((candidates, -scores))]

    def query(self, limit):
        before = self.batch_size
        previous_fit = self.fit_count
        ranked = self.rank()
        n_explore = 0
        size = min(self.batch_size, int(limit), len(ranked))
        if self.policy == "explore_10" and size >= 10:
            # Carry applies to eligible review slots only. The intentional gate
            # excludes earlier/small batches and the externally supplied seed.
            self.exploration_carry += size*self.epsilon
            n_explore = int(self.exploration_carry)
            self.exploration_carry -= n_explore
            exploit = ranked[:size-n_explore]
            explore = self.streams["exploration"].choice(ranked[size-n_explore:], n_explore, replace=False)
            selected = np.concatenate([exploit, explore])
        else:
            selected = ranked[:size]
        if self.policy != "fixed_20":
            self.batch_size += math.ceil(self.batch_size / 10)
        self.round_count += 1
        self.last_round = {
            "round_index": self.round_count,
            "fit_index": self.fit_count or None,
            "fit": deepcopy(self.last_fit) if self.fit_count != previous_fit else None,
            "candidate_margins": self.candidate_margins,
            "margin_unavailable_reason": (
                "policy_has_no_svm" if self.policy in ("random", "seed_similarity") else None),
            "selected_rows": selected.tolist(),
            "selection_operators": (["random"] * size if self.policy == "random" else
                                    ["exploit"] * (size-n_explore) + ["explore"] * n_explore),
            "batch_size_before_growth": before,
            "batch_size_after_growth": self.batch_size,
        }
        return selected
