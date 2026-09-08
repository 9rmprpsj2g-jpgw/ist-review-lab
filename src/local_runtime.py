"""Local-only census preconditions and provenance; no fitting or downloads."""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE = 'cbe42024cc632bc1872f18a7ed45313944e48361'
PYTHON = '3.12.13'
SOURCE = ROOT/'data/raw/rcv1_topics_train.txt.bz2'
REFERENCE = ROOT/'audit_store/local_reference/C12_11_fixed_10.json'
OLD_MANIFEST = ROOT/'audit_manifests/20260907_census_18add1f5ba0e.json'


def paths(generation):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', generation):
        raise ValueError('Generation must be a simple alphanumeric/hyphen/underscore name')
    return ROOT/'audit_store'/generation, ROOT/'local_outputs'/generation


def reference_entry():
    return next(e for e in json.loads(OLD_MANIFEST.read_text())['entries']
                if e['filename'] == REFERENCE.name)


def code_identity():
    files = subprocess.check_output(['git', 'ls-files', 'src', 'scripts', 'tests',
        'requirements-census.txt', 'experiment_plan_v2.json', 'data/source_lock.json'],
        cwd=ROOT, text=True).splitlines()
    return {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in files}


def check_worktree(generation):
    status = subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=all'], cwd=ROOT, text=True)
    allowed = f'audit_manifests/{generation}.json'
    unexpected = [line for line in status.splitlines() if line[3:] != allowed]
    if unexpected:
        raise RuntimeError('Commit preparation changes; only the current generated manifest may be dirty: '+repr(unexpected))


def check_environment(generation, require_clean=True):
    # Production and full-size storage checks are deliberately blocked in Linux sandbox.
    if sys.platform != 'darwin':
        raise RuntimeError('Local census/storage check requires macOS; sandbox census prohibited')
    if platform.python_version() != PYTHON:
        raise RuntimeError(f'Expected CPython {PYTHON}; found {platform.python_version()}')
    if platform.python_implementation() != 'CPython':
        raise RuntimeError('CPython required')
    for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
        if os.environ.get(key) != '1':
            raise RuntimeError(f'Export {key}=1 before starting Python')
    versions = {}
    for line in (ROOT/'requirements-census.txt').read_text().splitlines():
        if not line or line.startswith('#'):
            continue
        name, expected = line.split('==')
        actual = importlib.metadata.version(name)
        if actual != expected:
            raise RuntimeError(f'{name}: expected {expected}, found {actual}')
        versions[name] = actual
    subprocess.run(['git', 'merge-base', '--is-ancestor', BASE, 'HEAD'], cwd=ROOT, check=True)
    if require_clean:
        check_worktree(generation)
    from .durable_io import sha256_file
    lock = json.loads((ROOT/'data/source_lock.json').read_text())
    frozen_lock = json.loads(subprocess.check_output(['git', 'show', BASE+':data/source_lock.json'], cwd=ROOT))
    if lock != frozen_lock:
        raise AssertionError('Source lock differs from confirmed base')
    if not SOURCE.is_file() or sha256_file(SOURCE) != lock['sha256']:
        raise AssertionError('Missing/wrong source bytes; install the supplied locked input bundle')
    entry = reference_entry()
    if not REFERENCE.is_file() or REFERENCE.stat().st_size != entry['byte_size'] or sha256_file(REFERENCE) != entry['sha256']:
        raise AssertionError('Missing/wrong storage-test reference; install the supplied input bundle')
    audits, output = paths(generation)
    audits.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)
    # Credit this generation's already-written files so successful work does not
    # make the next resume fail the original fresh-generation space requirement.
    used_by_device = {}
    existing = [*audits.rglob('*'), *output.rglob('*'), ROOT/'audit_manifests'/f'{generation}.json']
    for path in existing:
        if path.is_file():
            stat = path.stat()
            used_by_device[stat.st_dev] = used_by_device.get(stat.st_dev, 0)+stat.st_size
    disk_requirements = []
    for directory in (audits, output, ROOT/'audit_manifests'):
        used = used_by_device.get(directory.stat().st_dev, 0)
        required = max(2*2**30, 20*2**30-used)
        free = shutil.disk_usage(directory).free
        disk_requirements.append({'path': str(directory), 'free_bytes': free,
                                  'generation_bytes_on_volume': used, 'required_free_bytes': required})
        if free < required:
            raise RuntimeError('Insufficient disk: 20 GiB initial allowance less generation files, with 2 GiB free reserve')
    import psutil
    memory = psutil.virtual_memory()
    if memory.available < 4*2**30:
        raise RuntimeError('At least 4 GiB currently available RAM required for two workers')
    import threadpoolctl
    return {'python': platform.python_version(), 'implementation': platform.python_implementation(),
            'executable': sys.executable, 'platform': platform.platform(), 'machine': platform.machine(),
            'versions': versions, 'byteorder': sys.byteorder, 'code_files': code_identity(),
            'code_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
            'source_sha256': lock['sha256'], 'reference_sha256': entry['sha256'],
            'memory_total_bytes': memory.total, 'memory_available_bytes': memory.available,
            'disk_free_bytes': shutil.disk_usage(audits).free,
            'disk_requirements': disk_requirements,
            'audit_device': audits.stat().st_dev, 'output_device': output.stat().st_dev,
            'threadpools': threadpoolctl.threadpool_info()}


def stable_identity(environment):
    return {k: environment[k] for k in ('python', 'implementation', 'executable', 'platform',
        'machine', 'versions', 'byteorder', 'code_files', 'code_commit', 'source_sha256',
        'reference_sha256', 'audit_device', 'output_device')}


def resolved_config(generation):
    from .config import resolve_plan
    config = resolve_plan(json.loads((ROOT/'experiment_plan_v2.json').read_text()))
    audits, output = paths(generation)
    config['outputs']['directory'] = str(output.relative_to(ROOT))
    config['outputs']['audit_directory'] = str(audits.relative_to(ROOT))
    config['inputs']['invoke_experiment'] = True
    from .learner import POLICIES
    historical = json.loads((ROOT/'experiment_plan.json').read_text())
    if config['topics'] != historical['topics'] or config['seeds'] != historical['seeds'] or set(config['policies']) != set(POLICIES):
        raise ValueError('Topics, seeds or policies differ from the approved grid')
    if len(config['topics']) != 5 or len(config['seeds']) != 3 or len(config['policies']) != 12 or config['budget'] != 23149:
        raise ValueError('Expected approved 5 x 3 x 12 census grid')
    return config
