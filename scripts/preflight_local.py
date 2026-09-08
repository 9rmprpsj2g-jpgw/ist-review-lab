"""Read/validate local environment and source before any production fit."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.local_runtime import check_environment, paths, resolved_config
from src.durable_io import atomic_json


def main():
    p = argparse.ArgumentParser(); p.add_argument('--generation', required=True); args = p.parse_args()
    environment = check_environment(args.generation)
    from src.data import load_collection
    from src.census import feature_digest
    from src.config import resolve_plan
    import pandas as pd
    X, ids, topics, info = load_collection()
    config = resolved_config(args.generation)
    old = pd.read_csv(Path(__file__).resolve().parents[1]/'results/runs.csv')
    for topic in config['topics']:
        counts = old.loc[old.topic == topic, ['n', 'positives']].drop_duplicates()
        if len(counts) != 1 or counts.isna().any().any():
            raise AssertionError('Missing/inconsistent immutable N/R')
        n, r = map(int, counts.iloc[0])
        if len(ids) != n or sum(topic in t for t in topics) != r or config['budget'] != n:
            raise AssertionError('Collection differs from immutable N/R')
    environment['feature_matrix_sha256'] = feature_digest(X, ids)
    import threadpoolctl
    environment['threadpools'] = threadpoolctl.threadpool_info()
    environment['source'] = info
    environment['resolved_config'] = resolve_plan(config)
    environment['status'] = 'PASS'
    _, output = paths(args.generation)
    atomic_json(output/'preflight.json', environment)
    print(json.dumps({'status': 'PASS', 'python': environment['python'],
        'available_gib': environment['memory_available_bytes']/2**30,
        'free_disk_gib': environment['disk_free_bytes']/2**30,
        'source_sha256': environment['source_sha256'],
        'feature_matrix_sha256': environment['feature_matrix_sha256']}, indent=2))


if __name__ == '__main__':
    main()
