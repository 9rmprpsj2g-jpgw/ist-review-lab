"""Metrics are evaluator-only: no decisions use unreviewed ground truth."""
import math
import numpy as np


def evaluate(order, y, checkpoints=(20, 100, 500, 1000, 2000, 5000)):
    order = np.asarray(order, dtype=int)
    if len(set(order)) != len(order):
        raise ValueError("Repeated review IDs invalidate effort accounting.")
    total = int(np.sum(y))
    if total == 0:
        raise ValueError("Recall is undefined for a topic without positives.")
    gains = np.cumsum(np.asarray(y)[order])
    out = {"n": len(y), "positives": total, "reviewed": len(order)}
    for k in checkpoints:
        if k <= len(order):
            found = int(gains[k-1])
            out[f"found_at_{k}"] = found
            out[f"precision_at_{k}"] = found / k
            out[f"recall_at_{k}"] = found / total
    for target in (0.75, 0.90):
        hits = np.flatnonzero(gains >= math.ceil(target * total))
        effort = int(hits[0]+1) if len(hits) else None
        out[f"effort_at_{int(target*100)}"] = effort
        # WSS@r = r - fraction screened. It is not 1 - fraction screened.
        out[f"wss_at_{int(target*100)}"] = target-effort/len(y) if effort else None
    return out
