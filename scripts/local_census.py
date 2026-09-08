"""Two local macOS workers; durable run receipts, strict resume, visible progress.

No Phase 4 analysis. A completed run means both audit and producer receipt exist.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import traceback
import uuid
import resource
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.local_runtime import ROOT, paths, check_environment, stable_identity, resolved_config
from src.durable_io import atomic_file, atomic_json, sha256_file, _sync_directory, write_csv, write_bytes


def config_digest(config):
    return hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()


def run_name(task):
    return f'{task[0]}_{task[1]}_{task[2]}'


def summarize_convergence(audit, parameters):
    fits = [r['fit'] for r in audit['rounds'] if r['fit'] is not None]
    bad = 0; warnings_count = 0
    for fit in fits:
        n = fit.get('n_iter')
        if type(n) is not int or not 0 < n <= parameters['max_iter'] or type(fit.get('converged')) is not bool:
            raise AssertionError('Missing/invalid permanent convergence record')
        if fit['model_parameters'] != parameters:
            raise AssertionError('Fit-time parameters differ from resolved model')
        warnings_list = fit.get('warnings')
        if not isinstance(warnings_list, list):
            raise AssertionError('Missing captured warning list')
        convergence_warning = any(w['category'] == 'ConvergenceWarning' for w in warnings_list)
        if fit['converged'] != (not convergence_warning):
            raise AssertionError('Convergence status disagrees with captured warning')
        bad += not fit['converged']; warnings_count += len(warnings_list)
    return {'nonconverged_fits': bad, 'captured_warnings': warnings_count,
            'max_n_iter': max((f['n_iter'] for f in fits), default=0),
            'fit_seconds': sum(f['fit_seconds'] for f in fits)}


def validate_completed(audit_path, receipt_path, task, config, identity):
    from src.census import validate_audit
    from src.learner import new_svm
    receipt = json.loads(receipt_path.read_text())
    if receipt['config_sha256'] != config_digest(config) or receipt['environment'] != identity:
        raise AssertionError('Resume provenance/configuration mismatch')
    entry = validate_audit(audit_path, task)  # All existing checks retained.
    result = receipt['result']
    if (result['topic'], result['seed'], result['policy']) != task[:3]:
        raise AssertionError('Producer result has wrong run identity')
    if entry['sha256'] != result['audit_sha256'] or entry['fits'] != result['fits'] or result['reviewed'] != config['budget']:
        raise AssertionError('Producer/post-exit audit identity or completeness mismatch')
    audit = json.loads(audit_path.read_text())
    if audit['resolved_config'] != config:
        raise AssertionError('Audit has wrong resolved configuration')
    convergence = summarize_convergence(audit, new_svm(task[1], config).get_params())
    if convergence != receipt['convergence']:
        raise AssertionError('Producer/post-exit convergence summary mismatch')
    # Validate source prevalence without fitting or using a newly estimated R.
    import pandas as pd
    old = pd.read_csv(ROOT/'results/runs.csv')
    counts = old.loc[old.topic == task[0], ['n', 'positives']].drop_duplicates()
    if len(counts) != 1 or counts.isna().any().any():
        raise AssertionError('Invalid immutable topic counts')
    n, relevant = map(int, counts.iloc[0])
    if audit['n'] != n or sum(audit['observed_labels']) != relevant or result['positives'] != relevant:
        raise AssertionError('Census labels/results disagree with immutable prevalence')
    entry.update(convergence)
    entry['receipt_sha256'] = sha256_file(receipt_path)
    entry['worker_process_peak_rss_kib'] = result['worker_process_peak_rss_kib']
    return entry, result


def recover_completed(grid, audit_dir, config, identity, prior_entries):
    found = {}; results = {}; previous = {e['filename']: e for e in prior_entries}
    if len(previous) != len(prior_entries):
        raise AssertionError('Duplicate completed entry in prior manifest')
    expected_names = {run_name(t)+'.json' for t in grid}
    if any(p.name not in expected_names for p in audit_dir.glob('*.json')):
        raise AssertionError('Unexpected root audit outside approved grid')
    for task in grid:
        name = run_name(task); audit = audit_dir/(name+'.json'); receipt = audit_dir/'receipts'/(name+'.json')
        if audit.name in previous and (not audit.exists() or not receipt.exists()):
            raise AssertionError('Previously committed completed run is missing')
        if receipt.exists() and not audit.exists():
            raise AssertionError('Producer receipt exists but audit is missing')
        if audit.exists() and not receipt.exists():
            # Do not manufacture a producer digest from an orphan and call it evidence.
            # It must parse/validate first; corrupted final publications remain a hard stop.
            from src.census import validate_audit
            validate_audit(audit, task)
            before = sha256_file(audit)
            quarantine = audit_dir/'uncommitted'; quarantine.mkdir(exist_ok=True)
            target = quarantine/(name+'-'+uuid.uuid4().hex+'.json')
            write_bytes(target, audit.read_bytes(), expected_sha256=before)
            if sha256_file(target) != before:
                raise AssertionError('Uncommitted audit changed while being preserved')
            audit.unlink(); _sync_directory(audit_dir)
            print('UNCOMMITTED audit retained; rerunning interrupted run:', name, flush=True)
            continue
        if not receipt.exists():
            continue
        entry, result = validate_completed(audit, receipt, task, config, identity)
        if audit.name in previous and entry != previous[audit.name]:
            raise AssertionError('Completed run differs from prior manifest; never update expected digest')
        found[task] = entry; results[task] = result
        print(f'RESUME_CHECK {len(found)} completed audit(s) verified: {name}', flush=True)
    return found, results


def worker(args):
    if sys.platform != 'darwin':
        raise RuntimeError('Production worker is macOS-only; no sandbox census')
    def parent_watch():
        while True:
            if os.getppid() != args.parent_pid:
                os._exit(130)
            time.sleep(.5)
    threading.Thread(target=parent_watch, daemon=True).start()
    config = resolved_config(args.generation)
    audit_dir, output = paths(args.generation)
    preflight = json.loads((output/'preflight.json').read_text())
    from src import experiment
    from src.census import feature_digest
    from src.learner import new_svm
    experiment.initialize()
    if feature_digest(experiment._X, experiment._IDS) != preflight['feature_matrix_sha256']:
        raise AssertionError('Worker features differ from local preflight')
    task = (args.topic, args.seed, args.policy, config['budget'])
    print('START', run_name(task), flush=True)
    from scripts.check_local_storage import preserve_failures
    with preserve_failures(audit_dir):
        result = experiment.simulate((*task, config, str(output)),
            progress=lambda event: print('PROGRESS '+json.dumps(event), flush=True))
    audit = json.loads((audit_dir/(run_name(task)+'.json')).read_text())
    convergence = summarize_convergence(audit, new_svm(args.seed, config).get_params())
    result['worker_process_peak_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024
    receipt_path = audit_dir/'receipts'/(run_name(task)+'.json')
    if receipt_path.exists():
        raise AssertionError('Never overwrite a producer completion receipt')
    atomic_json(receipt_path, {'result': result, 'convergence': convergence,
        'config_sha256': config_digest(config), 'environment': stable_identity(preflight)})
    print('FINISHED', run_name(task), json.dumps(convergence), flush=True)


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--generation', required=True)
    parser.add_argument('--worker', action='store_true'); parser.add_argument('--topic')
    parser.add_argument('--seed', type=int); parser.add_argument('--policy'); parser.add_argument('--parent-pid', type=int)
    args = parser.parse_args()
    if args.worker:
        return worker(args)
    environment = check_environment(args.generation)
    identity = stable_identity(environment)
    config = resolved_config(args.generation)
    audit_dir, output = paths(args.generation)
    preflight = json.loads((output/'preflight.json').read_text())
    storage = json.loads((output/'storage_check.json').read_text())
    if preflight['status'] != 'PASS' or stable_identity(preflight) != identity or preflight['resolved_config'] != config:
        raise AssertionError('Run preflight after any environment/configuration change')
    if storage['status'] != 'PASS' or len(storage['trials']) != 20 or storage['environment'] != identity or storage['audit_device'] != audit_dir.stat().st_dev:
        raise AssertionError('A passing storage check on this environment/volume is required')
    # Operational lock, not a result artifact. Children inherit it so a killed
    # parent cannot permit a second generation writer while a child is still alive.
    lock_fd = os.open(audit_dir/'generation.lock', os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(lock_fd); raise RuntimeError('Generation already has live writers')
    try:
        run_generation(args, config, environment, preflight, lock_fd)
    finally:
        os.close(lock_fd)


def run_generation(args, config, environment, preflight, lock_fd):
    import pandas as pd
    import psutil
    from src.experiment import write_configuration
    environment['threadpools'] = preflight['threadpools']
    audit_dir, output = paths(args.generation)
    grid = [(t, s, p, config['budget']) for t in config['topics'] for s in config['seeds'] for p in config['policies']]
    if len(set(grid)) != 180:
        raise AssertionError('Approved grid must contain 180 unique runs')
    manifest_path = ROOT/'audit_manifests'/(args.generation+'.json')
    identity = stable_identity(environment)
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        if manifest['config_sha256'] != config_digest(config) or manifest['environment_identity'] != identity:
            raise AssertionError('Generation changed: choose a new generation, never replace expected provenance')
        if manifest['status'] == 'FAILED':
            raise RuntimeError('Prior integrity/worker failure requires review; no automatic retry')
        expected_grid = [dict(topic=t, seed=s, policy=p, budget=b) for t,s,p,b in grid]
        if manifest['expected_grid'] != expected_grid or manifest['completed'] != len(manifest['entries']):
            raise AssertionError('Prior manifest grid/count inconsistency')
        if manifest['status'] not in ('RUNNING', 'INTERRUPTED', 'COMPLETE', 'COMPLETE_WITH_NONCONVERGENCE'):
            raise AssertionError('Unknown prior generation status')
    else:
        manifest = {'schema_version': 3, 'generation_id': args.generation, 'status': 'RUNNING',
            'code_commit': environment['code_commit'], 'resolved_config': config,
            'config_sha256': config_digest(config), 'environment_identity': identity,
            'environment': environment, 'source': preflight['source'],
            'feature_matrix_sha256': preflight['feature_matrix_sha256'],
            'expected_grid': [dict(topic=t, seed=s, policy=p, budget=b) for t,s,p,b in grid],
            'supersedes_failed_generation': '20260907_census_18add1f5ba0e',
            'entries': [], 'completed': 0, 'sessions': [], 'archive_status': 'LOCAL_DURABLE_FILES'}
    entries, results = recover_completed(grid, audit_dir, config, identity, manifest['entries'])
    write_configuration(config, output)
    start = time.perf_counter(); session_id = uuid.uuid4().hex
    stop = threading.Event(); monitor_stop = threading.Event(); guard = threading.Lock()
    children = {}; peak = [0]; monitoring_warnings = []
    def monitor():
        while not monitor_stop.wait(.5):
            try:
                processes = [psutil.Process(), *psutil.Process().children(recursive=True)]
                rss = 0
                for process in processes:
                    try: rss += process.memory_info().rss
                    except psutil.NoSuchProcess: pass
                peak[0] = max(peak[0], rss)
            except psutil.NoSuchProcess: pass
            except psutil.AccessDenied as error:
                monitoring_warnings.append(str(error))
    monitor_thread = threading.Thread(target=monitor, daemon=True); monitor_thread.start()
    def execute(task):
        if stop.is_set():
            return None
        name = run_name(task); log_path = audit_dir/'logs'/f'{name}-{session_id}.log'
        command = [sys.executable, '-u', __file__, '--generation', args.generation, '--worker',
                   '--topic', task[0], '--seed', str(task[1]), '--policy', task[2], '--parent-pid', str(os.getpid())]
        with atomic_file(log_path, 'w') as log:
            with guard:
                if stop.is_set():
                    return None
                process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT, text=True, bufsize=1, pass_fds=(lock_fd,))
                children[name] = process
            for line in process.stdout:
                log.write(line)
                with guard:
                    print('['+name+'] '+line, end='', flush=True)
            process.wait()  # Full exit before independent audit reads/digests.
            with guard: children.pop(name, None)
        if process.returncode:
            raise RuntimeError(f'{name} exited {process.returncode}; inspect {log_path}')
        return validate_completed(audit_dir/(name+'.json'), audit_dir/'receipts'/(name+'.json'), task, config, identity)
    def publish(status):
        manifest.update(status=status, completed=len(entries), entries=[entries[t] for t in grid if t in entries])
        manifest['nonconverged_by_policy_topic'] = {p: {t: sum(e['nonconverged_fits'] for task,e in entries.items() if task[0] == t and task[2] == p) for t in config['topics']} for p in config['policies']}
        manifest['nonconverged_fits'] = sum(e['nonconverged_fits'] for e in entries.values())
        manifest['captured_warnings'] = sum(e['captured_warnings'] for e in entries.values())
        manifest['total_audit_bytes'] = sum(e['byte_size'] for e in entries.values())
        manifest['total_fits'] = sum(e['fits'] for e in entries.values())
        write_csv(pd.DataFrame([results[t] for t in grid if t in results]), output/'runs.csv', index=False) if results else None
        atomic_json(manifest_path, manifest)
    publish('RUNNING')
    print(f'RESUME VERIFIED {len(entries)}/180; two workers; {180-len(entries)} remaining', flush=True)
    pool = ThreadPoolExecutor(max_workers=2)
    futures = {pool.submit(execute,t): t for t in grid if t not in entries}
    status = 'RUNNING'
    try:
        for future in as_completed(futures):
            task = futures[future]; result = future.result()
            if result is None:
                continue
            entries[task], results[task] = result
            publish('RUNNING')
            print(f'COMPLETE {len(entries)}/180 {run_name(task)} nonconverged={entries[task]["nonconverged_fits"]} elapsed={time.perf_counter()-start:.1f}s', flush=True)
        if len(entries) != 180:
            raise AssertionError('Incomplete census grid')
        status = 'COMPLETE_WITH_NONCONVERGENCE' if manifest['nonconverged_fits'] else 'COMPLETE'
    except BaseException as error:
        status = 'INTERRUPTED' if isinstance(error, KeyboardInterrupt) else 'FAILED'
        manifest['last_error'] = {'error': repr(error), 'traceback': traceback.format_exc()}
        stop.set()
        with guard:
            for process in children.values():
                if process.poll() is None: process.terminate()
        raise
    finally:
        pool.shutdown(wait=True, cancel_futures=True)
        monitor_stop.set(); monitor_thread.join()
        manifest['sessions'].append({'session_id': session_id, 'seconds_wall': time.perf_counter()-start,
            'sampled_process_tree_peak_rss_bytes': peak[0], 'sampling_interval_seconds': .5,
            'monitoring_warnings': monitoring_warnings,
            'rss_caveat': 'Sampled sum including parent and workers; shared pages counted per process, short peaks may be missed. Worker OS high-water RSS separately retained.'})
        manifest['seconds_wall'] = sum(s['seconds_wall'] for s in manifest['sessions'])
        publish(status)
    print(json.dumps({'status': status, 'completed': len(entries), 'nonconverged_fits': manifest['nonconverged_fits'],
        'audit_bytes': manifest['total_audit_bytes'], 'seconds_wall': manifest['seconds_wall'],
        'sampled_peak_rss_bytes_this_session': peak[0]}), flush=True)
    if status == 'COMPLETE_WITH_NONCONVERGENCE':
        raise SystemExit(2)  # Data retained, review required; never auto-increase max_iter.


if __name__ == '__main__':
    main()
