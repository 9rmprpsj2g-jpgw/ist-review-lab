"""Allocation and dispatch contracts only; no model fits or large-file trials."""
import os
from pathlib import Path
import signal
import tempfile
import unittest
from unittest.mock import patch
from src.durable_io import write_text
from src.linux_runtime import allocation_available, memory_controllers
from src.local_runtime import check_platform
from scripts.linux_census import interrupt


class LinuxHandoffContracts(unittest.TestCase):
    def test_host_free_memory_cannot_override_job_cap(self):
        with self.assertRaisesRegex(RuntimeError, 'host AND allocation'):
            allocation_available(32*2**30, [{'limit_bytes': 4*2**30, 'usage_bytes': 1}], True)

    def test_four_gib_gate_retained(self):
        self.assertEqual(allocation_available(4*2**30, [], False), 4*2**30)
        with self.assertRaises(RuntimeError):
            allocation_available(4*2**30-1, [], False)

    def test_unreadable_or_unlimited_slurm_allocation_stops(self):
        for controllers in ([], [{'limit_bytes': None, 'usage_bytes': 0}]):
            with self.assertRaises(RuntimeError):
                allocation_available(32*2**30, controllers, True)

    def test_parent_cgroup_limit_is_observed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); proc = root/'proc'; mount = root/'cgroups'
            write_text(proc/'cgroup', '0::/job/step\n')
            write_text(mount/'job/step/memory.max', 'max\n')
            write_text(mount/'job/step/memory.current', '0\n')
            write_text(mount/'job/memory.max', str(4*2**30))
            write_text(mount/'job/memory.current', '1\n')
            lines = [f'1 0 0:1 / {mount} rw - cgroup2 cgroup rw']
            observed = memory_controllers(proc, lines)
            with self.assertRaises(RuntimeError):
                allocation_available(32*2**30, observed, True)

    def test_v1_mount_root_is_resolved(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); proc = root/'proc'; mount = root/'memory'
            write_text(proc/'cgroup', '4:memory:/slurm/job\n')
            write_text(mount/'job/memory.limit_in_bytes', str(16*2**30))
            write_text(mount/'job/memory.usage_in_bytes', str(2**30))
            observed = memory_controllers(proc, [f'1 0 0:1 /slurm {mount} rw - cgroup cgroup rw,memory'])
            self.assertEqual(allocation_available(32*2**30, observed, True), 15*2**30)

    def test_linux_is_explicit_and_sandbox_stays_blocked(self):
        with patch('src.local_runtime.sys.platform', 'linux'), patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError):
                check_platform()
            with patch.dict(os.environ, {'IST_CENSUS_HOST': 'external-linux'}):
                check_platform()
                with patch.dict(os.environ, {'CODEX_PRIMARY_RUNTIME_ROOT': '/runtime'}):
                    with self.assertRaises(RuntimeError):
                        check_platform()

    def test_termination_enters_existing_interruption_cleanup(self):
        with patch('scripts.linux_census.signal.signal') as handler:
            with self.assertRaises(KeyboardInterrupt):
                interrupt(signal.SIGTERM, None)
            handler.assert_any_call(signal.SIGTERM, signal.SIG_IGN)
            handler.assert_any_call(signal.SIGUSR1, signal.SIG_IGN)