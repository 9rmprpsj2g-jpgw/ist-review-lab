"""Install supplied source/reference bytes against existing committed digests."""
import argparse
import hashlib
from pathlib import Path
import sys
import zipfile
import json
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.local_runtime import ROOT, SOURCE, REFERENCE, reference_entry, BASE
from src.durable_io import write_bytes, sha256_file
import subprocess


def main():
    p = argparse.ArgumentParser(); p.add_argument('bundle', type=Path); args = p.parse_args()
    lock = json.loads(subprocess.check_output(['git', 'show', BASE+':data/source_lock.json'], cwd=ROOT))
    expected = {'rcv1_topics_train.txt.bz2': (SOURCE, lock['sha256']),
                'C12_11_fixed_10.json': (REFERENCE, reference_entry()['sha256'])}
    with zipfile.ZipFile(args.bundle) as archive:
        if set(archive.namelist()) != set(expected) or archive.testzip() is not None:
            raise AssertionError('Input bundle member/CRC failure')
        for name, (target, digest) in expected.items():
            payload = archive.read(name)
            if hashlib.sha256(payload).hexdigest() != digest:
                raise AssertionError('Bundled input disagrees with committed digest')
            if target.exists():
                if sha256_file(target) != digest:
                    raise AssertionError('Existing input disagrees; will not overwrite')
            else:
                write_bytes(target, payload, expected_sha256=digest)
            print('VERIFIED', target.relative_to(ROOT), digest, flush=True)


if __name__ == '__main__':
    main()
