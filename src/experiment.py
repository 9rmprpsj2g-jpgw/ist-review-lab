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
from .learner import ReviewLearner, new_svm, POLICIES
from .config import resolve_plan
from .metrics import evaluate
from .audit import seed_round, externalize_round, replay_row_order

_X = _IDS = _TOPICS = None


def initialize():
    global _X, _IDS, _TOPICS
    _X, _IDS, _TOPICS, _ = load_collection()


def simulate(task):
    topic, random_seed, policy, budget, config, output_dir = task
    y = np.array([topic in s for s in _TOPICS], dtype=np.uint8)
    learner = ReviewLearner(_X, policy, random_seed, config)
    seed_index = int(learner.streams["seed_doc"].choice(np.flatnonzero(y)))
    learner.observe([seed_index], [1])
    rounds = [externalize_round(seed_round(seed_index, learner.batch_size, learner.config["audit"]["margin_scope"], len(y)-1), _IDS)]
    order = [seed_index]
    batch_ends = [1]
    start = time.perf_counter()
    while len(order) < min(budget, len(y)):
        batch = learner.query(budget-len(order))
        learner.observe(batch, y[batch])
        order.extend(batch.tolist())
        batch_ends.append(len(order))
        rounds.append(externalize_round(learner.last_round, _IDS))
    result = evaluate(order, y)
    result.update(topic=topic, seed=random_seed, policy=policy,
                  seed_doc_id=_IDS[seed_index], fits=learner.fit_count,
                  seconds=time.perf_counter()-start)
    for target in (75, 90):
        exact = result[f"effort_at_{target}"]
        result[f"batch_effort_at_{target}"] = (
            next(b for b in batch_ends if b >= exact) if exact else None)
    audit = {"schema_version": 3, "audit_config": learner.config["audit"],
             "rounds": rounds, "topic": topic, "seed": random_seed, "policy": policy,
             "row_order": order, "batch_ends": batch_ends,
             "observed_labels": y[order].tolist()}
    if replay_row_order(audit) != order:
        raise AssertionError("Audit-only replay differs from observed row order")
    dest = output_directory(output_dir) / "audits"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / f"{topic}_{random_seed}_{policy}.json").write_text(json.dumps(audit, allow_nan=False))
    return result


def output_directory(path):
    destination = Path(path)
    if not destination.is_absolute():
        destination = ROOT / destination
    destination = destination.resolve()
    if destination == (ROOT/"results").resolve() or (ROOT/"results").resolve() in destination.parents:
        raise ValueError("results/ is frozen v1 evidence; choose a new output directory")
    return destination


def write_configuration(config, destination):
    """Record instantiated parameters without fitting a model or loading data."""
    resolved = resolve_plan(config)
    if any(policy not in POLICIES for policy in resolved.get("policies", [])):
        raise ValueError("Unknown policy in plan; frozen_svm is now seed_only_frozen")
    destination = output_directory(destination)
    destination.mkdir(parents=True, exist_ok=True)
    (destination/"resolved_config.json").write_text(json.dumps(resolved,indent=2)+"\n")
    actual = {str(seed):new_svm(seed,resolved).get_params(deep=True) for seed in resolved.get("seeds",[0])}
    (destination/"model_parameters.json").write_text(json.dumps(actual,indent=2)+"\n")
    return resolved


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--plan", type=Path, default=ROOT/"experiment_plan_v2.json")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    config_path = args.plan
    config = resolve_plan(json.loads(config_path.read_text()))
    destination = output_directory(args.output_dir or config.get("outputs",{}).get("directory","phase2_outputs"))
    if not config.get("inputs",{}).get("invoke_experiment",False):
        raise ValueError("Experiment execution is disabled in this plan; Phase 3B requires separate approval")
    config = write_configuration(config,destination)
    X, ids, topics, info = load_collection()
    print(json.dumps(info), flush=True)
    print({t: sum(t in s for s in topics) for t in config["topics"]}, flush=True)
    jobs = [(t,s,p,config["budget"],config,str(destination)) for t in config["topics"]
            for s in config["seeds"] for p in config["policies"]]
    start = time.perf_counter()
    results = []
    with ProcessPoolExecutor(max_workers=args.jobs, initializer=initialize) as pool:
        for result in pool.map(simulate, jobs):
            results.append(result)
            print(f'{len(results)}/{len(jobs)} {result["topic"]} '
                  f'{result["seed"]} {result["policy"]}: '
                  f'R@1000={result["recall_at_1000"]:.3f}', flush=True)
            pd.DataFrame(results).to_csv(destination / "runs.csv", index=False)
    environment = {"python": platform.python_version(), "platform": platform.platform(),
                   "numpy": np.__version__, "scipy": scipy.__version__,
                   "scikit_learn": sklearn.__version__, "pandas": pd.__version__,
                   "seconds_wall": time.perf_counter()-start, "jobs": args.jobs,
                   "plan_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
                   "data_sha256": info["sha256"], "runs": len(results)}
    (destination / "environment.json").write_text(json.dumps(environment, indent=2)+"\n")


if __name__ == "__main__":
    main()
