"""One publication path. Final-path verification is mandatory, not a success hint."""
from contextlib import contextmanager
import bz2
import csv
import errno
import gzip
import hashlib
import json
import os
from pathlib import Path
import tempfile
import warnings
import zipfile


def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def parse_count(path, kind):
    """Parse to EOF; return logical record count where the format defines one."""
    if kind in ('.json', '.ipynb'):
        with open(path, encoding='utf-8') as f:
            value = json.load(f)
        if kind == '.ipynb':
            import nbformat
            nbformat.validate(nbformat.from_dict(value))
        return len(value) if isinstance(value, (dict, list)) else 1
    if kind == '.jsonl':
        with open(path, encoding='utf-8') as f:
            return sum(1 for line in f if json.loads(line) is not None or line.strip() == 'null')
    if kind in ('.csv', '.csv.gz'):
        opener = gzip.open if kind.endswith('.gz') else open
        with opener(path, 'rt', newline='', encoding='utf-8') as f:
            reader = csv.reader(f, strict=True)
            header = next(reader)
            count = 0
            for row in reader:
                if len(row) != len(header):
                    raise ValueError('CSV column count mismatch')
                count += 1
            return count
    if kind in ('.zip', '.npz'):
        with zipfile.ZipFile(path) as z:
            if z.testzip() is not None:
                raise ValueError('ZIP CRC failure')
            if kind == '.npz':
                import numpy as np
                with np.load(path, allow_pickle=False) as arrays:
                    for key in arrays.files:
                        arrays[key]
            return len(z.infolist())
    if kind == '.bz2':
        with bz2.open(path, 'rb') as f:
            return sum(1 for _ in f)
    if kind == '.png':
        from PIL import Image
        with Image.open(path) as im:
            im.verify()
        with Image.open(path) as im:
            im.load()
        return 1
    if kind == '.svg':
        import xml.etree.ElementTree as ET
        if ET.parse(path).getroot().tag != '{http://www.w3.org/2000/svg}svg':
            raise ValueError('Not an SVG')
        return 1
    if kind == '.pdf':
        import fitz
        if not Path(path).read_bytes().rstrip().endswith(b'%%EOF'):
            raise ValueError('Missing PDF end marker')
        with fitz.open(path) as doc:
            if doc.is_repaired or not len(doc):
                raise ValueError('Incomplete PDF')
            for page in doc:
                page.get_pixmap(dpi=72)
            return len(doc)
    if kind in ('.md', '.txt', '.log', '.html', '.py', '.patch'):
        with open(path, encoding='utf-8') as f:
            return sum(1 for _ in f)
    return Path(path).stat().st_size  # opaque bytes: length and disk digest only


def _sync_directory(path):
    if os.name != 'posix':
        warnings.warn('Directory fsync unavailable on this platform', RuntimeWarning)
        return
    fd = os.open(path, os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0))
    try:
        try:
            os.fsync(fd)
        except OSError as exc:
            if exc.errno not in (errno.EINVAL, errno.ENOTSUP):
                raise
            warnings.warn('Filesystem does not support directory fsync', RuntimeWarning)
    finally:
        os.close(fd)


@contextmanager
def atomic_file(path, mode='wb', *, expected_count=None, expected_sha256=None,
                validator=None, **open_options):
    """Old complete file or new complete file; killed writers may leave ignored scratch.

    Count checks run before replace and after publication. An immutable expected
    digest, when supplied, is never derived here. Receipts hash the final path.
    Concurrent writers to the same final path are unsupported and must be avoided.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    kind = '.csv.gz' if path.name.endswith('.csv.gz') else path.suffix
    fd, temporary = tempfile.mkstemp(prefix='.writing-', dir=path.parent)
    published = False
    try:
        if 'b' not in mode:
            open_options.setdefault('encoding', 'utf-8')
        with os.fdopen(fd, mode, **open_options) as f:
            yield f
            expected_bytes = f.tell()
            f.flush()
            os.fsync(f.fileno())
            if os.fstat(f.fileno()).st_size != expected_bytes:
                raise ValueError(f'Serialized byte count mismatch for {path}')
        count = parse_count(temporary, kind)
        if expected_count is not None and count != expected_count:
            raise ValueError(f'Record count mismatch for {path}: {count} != {expected_count}')
        if validator is not None:
            validator(Path(temporary))
        size = os.stat(temporary).st_size
        staged_digest = sha256_file(temporary)
        if expected_sha256 is not None and staged_digest != expected_sha256:
            raise ValueError(f'Expected digest mismatch for {path}')
        os.replace(temporary, path)
        published = True
        _sync_directory(path.parent)
        final_digest = sha256_file(path)
        if path.stat().st_size != size or final_digest != staged_digest:
            raise ValueError(f'Published bytes differ for {path}')
        if parse_count(path, kind) != count:
            raise ValueError(f'Published record count differs for {path}')
        if validator is not None:
            validator(path)
        if sha256_file(path) != final_digest:
            raise ValueError(f'Final file changed during verification: {path}')
    except BaseException:
        if published:
            path.unlink(missing_ok=True)
            _sync_directory(path.parent)
        raise
    finally:
        Path(temporary).unlink(missing_ok=True)


def write_text(path, text, **options):
    payload = text.encode(options.get('encoding', 'utf-8'))
    with atomic_file(path, 'w', validator=lambda p: _same_bytes(p, payload), **options) as f:
        return f.write(text)


def _same_bytes(path, payload):
    if path.read_bytes() != payload:
        raise ValueError(f'Written content mismatch: {path}')


def write_bytes(path, payload, **options):
    with atomic_file(path, 'wb', validator=lambda p: _same_bytes(p, payload), **options) as f:
        return f.write(payload)


def atomic_json(path, value):
    def verify(p):
        with p.open(encoding='utf-8') as f:
            if json.load(f) != value:
                raise ValueError('JSON value/record completeness mismatch')
    with atomic_file(path, 'w', expected_count=len(value) if isinstance(value, (dict, list)) else 1,
                     validator=verify) as f:
        json.dump(value, f, allow_nan=False)
        f.write('\n')
    return sha256_file(path)


def write_csv(frame, path, **options):
    if hasattr(path, 'write'):
        return frame.to_csv(path, **options)  # caller owns an atomic_file context
    if str(path).endswith('.csv.gz'):
        import io
        compression = options.pop('compression', {'method': 'gzip'})
        gzip_options = dict(compression) if isinstance(compression, dict) else {}
        gzip_options.pop('method', None)
        with atomic_file(path, 'wb', expected_count=len(frame)) as raw:
            with gzip.GzipFile(fileobj=raw, mode='wb', filename='', **gzip_options) as compressed:
                with io.TextIOWrapper(compressed, encoding='utf-8', newline='') as text:
                    frame.to_csv(text, **options)
    else:
        with atomic_file(path, 'w', newline='', expected_count=len(frame)) as f:
            frame.to_csv(f, **options)


def save_figure(fig, path, **options):
    options.setdefault('format', Path(path).suffix.lstrip('.'))
    with atomic_file(path, 'wb') as f:
        fig.savefig(f, **options)


def write_notebook(notebook, path):
    import nbformat
    with atomic_file(path, 'w', validator=lambda p: _same_notebook(p, notebook)) as f:
        nbformat.write(notebook, f)


def _same_notebook(path, notebook):
    import nbformat
    if nbformat.read(path, as_version=4) != notebook:
        raise ValueError('Notebook content mismatch')
