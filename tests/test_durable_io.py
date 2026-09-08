"""Publication fault injection, using synthetic records, not retrieval fixtures."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from src.durable_io import atomic_file, atomic_json, sha256_file, write_csv


class DurablePublication(unittest.TestCase):
    def test_killed_unflushed_writer_never_publishes_partial(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'records.jsonl'
            program = """
import os,sys
from src.durable_io import atomic_file
with atomic_file(sys.argv[1], 'w', expected_count=47) as f:
    f.write('{"fit":1}\\n')
    os._exit(17)
"""
            result = subprocess.run([sys.executable, '-c', program, str(p)])
            self.assertEqual(result.returncode, 17)
            self.assertFalse(p.exists())
            atomic_json(Path(d)/'old.json', {'complete': True})
            old = Path(d)/'old.json'
            prior = old.read_bytes()
            result = subprocess.run([sys.executable, '-c', program, str(old)])
            self.assertEqual(result.returncode, 17)
            self.assertEqual(old.read_bytes(), prior)

    def test_valid_jsonl_truncated_at_record_boundary_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'records.jsonl'
            with self.assertRaises(ValueError):
                with atomic_file(p, 'w', expected_count=47) as f:
                    for i in range(41):
                        f.write(json.dumps({'fit':i})+'\n')
            self.assertFalse(p.exists())

    def test_fsync_failure_preserves_old_complete_file(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'old.json';atomic_json(p, {'complete':True})
            prior = p.read_bytes()
            with patch('src.durable_io.os.fsync', side_effect=OSError('injected write failure')):
                with self.assertRaises(OSError):
                    atomic_json(p, {'complete':False})
            self.assertEqual(p.read_bytes(), prior)

    def test_final_path_corruption_raises_and_removes_bad_publication(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'records.json';replace = os.replace
            def corrupt(source, target):
                replace(source, target)
                with open(target, 'wb') as f:
                    f.write(b'[')
            with patch('src.durable_io.os.replace', side_effect=corrupt):
                with self.assertRaises(ValueError):
                    atomic_json(p, [1,2])
            self.assertFalse(p.exists())

    def test_complete_roundtrip_and_independent_child_digest(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'records.jsonl'
            with atomic_file(p, 'w', expected_count=47) as f:
                for i in range(47):f.write(json.dumps({'fit':i})+'\n')
            expected = sha256_file(p)
            code = 'import sys;from src.durable_io import sha256_file;print(sha256_file(sys.argv[1]))'
            actual = subprocess.check_output([sys.executable,'-c',code,str(p)],text=True).strip()
            self.assertEqual(actual, expected)
            self.assertEqual(len(p.read_text().splitlines()),47)
            self.assertFalse(list(Path(d).glob('.writing-*')))

    def test_csv_gzip_and_json_count_verification(self):
        import pandas as pd
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'records.csv.gz';frame=pd.DataFrame({'value':[1,2]})
            write_csv(frame,p,index=False,compression={'method':'gzip','mtime':0})
            pd.testing.assert_frame_equal(pd.read_csv(p),frame)
            q=Path(d)/'records.json'
            digest=atomic_json(q,{'rows':[1,2]})
            self.assertEqual(digest,sha256_file(q))
            self.assertEqual(json.loads(q.read_text()),{'rows':[1,2]})
