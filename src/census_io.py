"""Atomic audit writes and provenance hashes for the approved census generation."""
import hashlib
import json
import os
from pathlib import Path
import tempfile


def atomic_json(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=path.parent,prefix='.writing-',delete=False) as handle:
            temporary=Path(handle.name)
            json.dump(value,handle,allow_nan=False)
            handle.write('\n');handle.flush();os.fsync(handle.fileno())
        os.replace(temporary,path)
    finally:
        if temporary is not None:temporary.unlink(missing_ok=True)


def sha256_file(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda:handle.read(1024*1024),b''):digest.update(block)
    return digest.hexdigest()
