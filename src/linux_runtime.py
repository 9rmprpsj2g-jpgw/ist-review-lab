"""External Linux allocation checks; existing numerical/integrity gates stay intact."""
import json
import os
from pathlib import Path
import platform
import subprocess


def memory_controllers(proc=Path('/proc/self'), mounts=None):
    """Read current and ancestor cgroup v1/v2 memory limits, including job caps.

    Resolve mount roots instead of assuming that a cgroup namespace starts at /.
    Values are allocation observations, never a replacement for psutil's host gate.
    """
    memberships = [line.split(':', 2) for line in (proc/'cgroup').read_text().splitlines()]
    lines = mounts if mounts is not None else (proc/'mountinfo').read_text().splitlines()
    observations = []
    for line in lines:
        left, right = line.split(' - ', 1)
        fields, fs = left.split(), right.split()
        if fs[0] not in ('cgroup', 'cgroup2'):
            continue
        unified = fs[0] == 'cgroup2'
        if not unified and 'memory' not in fs[2].split(','):
            continue
        member = next((p for _, controllers, p in memberships
                       if (controllers == '' if unified else 'memory' in controllers.split(','))), None)
        if member is None:
            continue
        def unescape(text):
            for escape, value in (('\\040', ' '), ('\\011', '\t'), ('\\012', '\n'), ('\\134', '\\')):
                text = text.replace(escape, value)
            return text
        mount_root, mount = Path(unescape(fields[3])), Path(unescape(fields[4]))
        try:
            relative = Path(member).relative_to(mount_root)
        except ValueError:
            continue
        directory = mount/relative
        limit_name, usage_name = ('memory.max', 'memory.current') if unified else ('memory.limit_in_bytes', 'memory.usage_in_bytes')
        while directory == mount or mount in directory.parents:
            limit_path, usage_path = directory/limit_name, directory/usage_name
            if limit_path.exists() and usage_path.exists():
                raw = limit_path.read_text().strip()
                usage = int(usage_path.read_text())
                limit = None if raw == 'max' or int(raw) >= 2**60 else int(raw)
                observations.append({'path': str(directory), 'version': 2 if unified else 1,
                                     'limit_bytes': limit, 'usage_bytes': usage})
            if directory == mount:
                break
            directory = directory.parent
    return observations


def allocation_available(host_available, controllers, slurm):
    if slurm and not controllers:
        raise RuntimeError('Cannot read the Slurm memory controller; ask the site to expose job usage/limits before running')
    caps = [max(0, c['limit_bytes']-c['usage_bytes']) for c in controllers if c['limit_bytes'] is not None]
    if slurm and not caps:
        raise RuntimeError('No finite Slurm memory cap is visible; allocation headroom is unverified')
    available = min([host_available, *caps])
    if available < 4*2**30:
        raise RuntimeError('At least 4 GiB currently available within host AND allocation required for two workers')
    return available


def check_linux_resources(root, audits, output, host_available):
    if platform.machine() != 'x86_64':
        raise RuntimeError('This pinned Linux handoff targets x86_64; other architectures need separate validation')
    if len(os.sched_getaffinity(0)) < 2:
        raise RuntimeError('Two CPU slots required for the unchanged two workers')
    slurm = bool(os.environ.get('SLURM_JOB_ID'))
    if slurm and int(os.environ.get('SLURM_CPUS_PER_TASK', '0')) < 2:
        raise RuntimeError('Request one Slurm task with at least two CPUs')
    directories = (root, audits, output, root/'audit_manifests', root/'data', root/'data/raw')
    devices = {p.stat().st_dev for p in directories}
    if len(devices) != 1:
        raise RuntimeError('Linux handoff requires the whole checkout and all output directories on one tested filesystem; do not split work and scratch volumes')
    mounts = []
    for directory in directories:
        item = json.loads(subprocess.check_output(['findmnt', '--json', '--target', str(directory),
            '--output', 'TARGET,SOURCE,FSTYPE,OPTIONS'], text=True))['filesystems'][0]
        if item['fstype'] in ('overlay', 'aufs', 'tmpfs', 'ramfs'):
            raise RuntimeError('Use a persistent external filesystem, not overlay/container or memory-backed storage: '+str(directory))
        mounts.append({'path': str(directory), **item})
    controllers = memory_controllers()
    available = allocation_available(host_available, controllers, slurm)
    return {'linux_host': {'mounts': mounts, 'cgroup_memory': controllers,
        'allocation_available_bytes': available, 'cpu_affinity': sorted(os.sched_getaffinity(0)),
        'hostname': platform.node(), 'slurm_job_id': os.environ.get('SLURM_JOB_ID'),
        'slurm_mem_per_node_mib': os.environ.get('SLURM_MEM_PER_NODE'),
        'scope': 'External Linux, single persistent filesystem; all original gates required'}}