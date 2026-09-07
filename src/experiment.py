"""Run the locked, paired simulation; save a complete review-order audit."""
import argparse
import hashlib
import json
import os
import platform
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np
import pandas as pd
import scipy
import sklearn
from .data import load_collection, ROOT
from .learner import ReviewLearner
from .metrics import evaluate

_X = _IDS = _TOPICS = None


def initialize():
    global _X, _IDS, _TOPICS
    _X, _IDS, _TOPICS, _ = load_collection()


def simulate(task):
    topic, random_seed, policy, budget = task
    y = np.array([topic in s for s in _TOPICS], dtype=np.uint8)
    seed_index = int(np.random.default_rng(random_seed).choice(np.flatnonzero(y)))
    learner = ReviewLearner(_X, policy, random_seed)
    learner.observe([seed_index], [1])
    order = [seed_index]
    batch_ends = [1]
    start = time.perf_counter()
    while len(order) < min(budget, len(y)):
        batch = learner.query(budget-len(order))
        learner.observe(batch, y[batch])
        order.extend(batch.tolist())
        batch_ends.append(len(order))
    result = evaluate(order, y)
    result.update(topic=topic, seed=random_seed, policy=policy,
                  seed_doc_id=_IDS[seed_index], fits=learner.fit_count,
                  seconds=time.perf_counter()-start)
    for target in (75, 90):
        exact = result[f"effort_at_{target}"]
        result[f"batch_effort_at_{target}"] = (
            next(b for b in batch_ends if b >= exact) if exact else None)
    audit = {"topic": topic, "seed": random_seed, "policy": policy,
             "row_order": order, "batch_ends": batch_ends,
             "observed_labels": y[order].tolist()}
    dest = ROOT / "results/audits"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / f"{topic}_{random_seed}_{policy}.json").write_text(json.dumps(audit))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--jobs", type=int, default=2)
    args = parser.parse_args()
    config_path = ROOT / "experiment_plan.json"
    config = json.loads(config_path.read_text())
    X, ids, topics, info = load_collection()
    print(json.dumps(info), flush=True)
    print({t: sum(t in s for s in topics) for t in config["topics"]}, flush=True)
    jobs = [(t,s,p,config["budget"]) for t in config["topics"]
            for s in config["seeds"] for p in config["policies"]]
    start = time.perf_counter()
    results = []
    with ProcessPoolExecutor(max_workers=args.jobs, initializer=initialize) as pool:
        for result in pool.map(simulate, jobs):
            results.append(result)
            print(f'{len(results)}/{len(jobs)} {result["topic"]} '
                  f'{result["seed"]} {result["policy"]}: '
                  f'R@1000={result["recall_at_1000"]:.3f}', flush=True)
            pd.DataFrame(results).to_csv(ROOT / "results/runs.csv", index=False)
    environment = {"python": platform.python_version(), "platform": platform.platform(),
                   "numpy": np.__version__, "scipy": scipy.__version__,
                   "scikit_learn": sklearn.__version__, "pandas": pd.__version__,
                   "seconds_wall": time.perf_counter()-start, "jobs": args.jobs,
                   "plan_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
                   "data_sha256": info["sha256"], "runs": len(results)}
    (ROOT / "results/environment.json").write_text(json.dumps(environment, indent=2)+"\n")


if __name__ == "__main__":
    main()
