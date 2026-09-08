"""Phase 3C contracts plus 20 full-size publications on the actual audit volume.

No fits, retries or modified verification. A finite PASS is not an absence proof.
"""
import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
import resource
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.local_runtime import ROOT, REFERENCE, reference_entry, paths, check_environment, stable_identity
from src.durable_io import atomic_file, atomic_json, sha256_file


@contextmanager
def preserve_failures(directory):
    original = Path.unlink
    def capture(path, *args, **kwargs):
        if directory in path.parents and path.exists():
            os.link(path, path.with_name('preserved-'+path.name+'-'+uuid.uuid4().hex+'.bin'))
        return original(path, *args, **kwargs)
    Path.unlink = capture
    try:
        yield
    finally:
        Path.unlink = original


def child(destination):
    if sys.platform != 'darwin':
        raise RuntimeError('Full-size storage check is local macOS only')
    destination.mkdir(exist_ok=False)
    started = time.perf_counter()
    # Real matrix residency, no model fitting, same full JSON value verification.
    from src.data import load_collection
    X, ids, topics, info = load_collection()
    value = json.loads(REFERENCE.read_text())
    with preserve_failures(destination):
        digest = atomic_json(destination/'audit.json', value)
    atomic_json(destination/'receipt.json', {'sha256': digest,
        'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'seconds_wall': time.perf_counter()-started})


def main():
    p = argparse.ArgumentParser(); p.add_argument('--generation'); p.add_argument('--child', type=Path)
    args = p.parse_args()
    if args.child:
        return child(args.child)
    if not args.generation:
        p.error('--generation required')
    environment = check_environment(args.generation)
    audit_dir, output = paths(args.generation)
    preflight = json.loads((output/'preflight.json').read_text())
    if stable_identity(environment) != stable_identity(preflight):
        raise AssertionError('Environment changed after preflight')
    trial_dir = audit_dir/('storage-check-'+uuid.uuid4().hex)
    trial_dir.mkdir()
    logs = output/trial_dir.name
    logs.mkdir()
    env = os.environ.copy(); env['TMPDIR'] = str(trial_dir)
    with atomic_file(logs/'storage_contracts.log', 'w') as log:
        process = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests',
                                  '-p', 'test_durable_io.py', '-v'], cwd=ROOT, env=env,
                                 stdout=log, stderr=subprocess.STDOUT)
    if process.returncode:
        raise RuntimeError(f'Phase 3C write contracts failed; read {logs}/storage_contracts.log')
    expected = reference_entry()['sha256']
    reference = json.loads(REFERENCE.read_text())
    trials = []
    try:
        for index in range(20):
            directory = trial_dir/str(index)
            with atomic_file(logs/f'storage_trial_{index:02}.log', 'w') as log:
                process = subprocess.run([sys.executable, __file__, '--child', str(directory)],
                                         cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
            if process.returncode:
                raise RuntimeError(f'Storage trial {index} failed; no retry')
            # Parent waits for full child exit, then reparses and checks intended value.
            audit = directory/'audit.json'
            receipt = json.loads((directory/'receipt.json').read_text())
            if json.loads(audit.read_text()) != reference or sha256_file(audit) != expected or receipt['sha256'] != expected:
                raise AssertionError('Post-exit full-size storage verification failed')
            trials.append({'trial': index, 'bytes': audit.stat().st_size, 'sha256': expected,
                           'peak_rss_bytes': receipt['peak_rss_bytes'], 'seconds_wall': receipt['seconds_wall']})
            print(f'STORAGE {index+1}/20 PASS', flush=True)
    except BaseException as error:
        atomic_json(output/'storage_check.json', {'status': 'FAIL', 'error': repr(error), 'trials': trials})
        raise
    atomic_json(output/'storage_check.json', {'status': 'PASS', 'trials': trials,
        'environment': stable_identity(environment), 'audit_device': audit_dir.stat().st_dev,
        'logs': str(logs.relative_to(ROOT)),
        'caveat': 'No observed failure in six contracts and 20 full-size trials; not proof of indefinite reliability.'})
    print('Storage check PASS. Audits retained; no fit ran.', flush=True)


if __name__ == '__main__':
    main()
