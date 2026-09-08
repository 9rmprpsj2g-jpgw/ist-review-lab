"""Run the locked, paired simulation; save a complete review-order audit."""

import sys as _durable_sys
from pathlib import Path as _DurablePath
_durable_sys.path.insert(0, str(_DurablePath(__file__).resolve().parents[1]))
from src import durable_io as _durable
import argparse
import hashlib
import json
import os
import platform
import resource
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
from .census_io import atomic_json

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
    audit = {"schema_version": 3, "budget": budget, "n": len(y),
             "resolved_config": learner.config, "audit_config": learner.config["audit"],
             "rounds": rounds, "topic": topic, "seed": random_seed, "policy": policy,
             "row_order": order, "batch_ends": batch_ends,
             "observed_labels": y[order].tolist()}
    if replay_row_order(audit) != order:
        raise AssertionError("Audit-only replay differs from observed row order")
    dest = output_directory(config.get("outputs", {}).get("audit_directory",
                            str(output_directory(output_dir) / "audits")))
    dest.mkdir(parents=True, exist_ok=True)
    audit_path = dest / f"{topic}_{random_seed}_{policy}.json"
    if audit_path.exists():
        raise ValueError("Refusing to overwrite an existing audit")
    if len(order) != min(budget, len(y)):
        raise AssertionError("Incomplete intended audit record count")
    result["audit_sha256"] = atomic_json(audit_path, audit)
    result["worker_process_peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
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
    _durable.write_text(destination/"resolved_config.json", json.dumps(resolved,indent=2)+"\n")
    actual = {str(seed):new_svm(seed,resolved).get_params(deep=True) for seed in resolved.get("seeds",[0])}
    _durable.write_text(destination/"model_parameters.json", json.dumps(actual,indent=2)+"\n")
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
            _durable.write_csv(pd.DataFrame(results), destination / "runs.csv", index=False)
    environment = {"python": platform.python_version(), "platform": platform.platform(),
                   "numpy": np.__version__, "scipy": scipy.__version__,
                   "scikit_learn": sklearn.__version__, "pandas": pd.__version__,
                   "seconds_wall": time.perf_counter()-start, "jobs": args.jobs,
                   "plan_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
                   "data_sha256": info["sha256"], "runs": len(results)}
    _durable.write_text(destination / "environment.json", json.dumps(environment, indent=2)+"\n")


if __name__ == "__main__":
    main()
