"""Durable atomic writes and complete-artifact/decoded-content validation."""
from contextlib import contextmanager
import csv
import gzip
import json
import os
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image
import fitz
import nbformat


@contextmanager
def atomic_file(path, mode="wb"):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        fd, temporary = tempfile.mkstemp(prefix=".writing-", dir=path.parent)
        with os.fdopen(fd, mode) as handle:
            yield handle
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            Path(temporary).unlink(missing_ok=True)


def cleanup_temporary_files(directory):
    """Only call after worker exit; never remove another live writer's files."""
    removed = []
    for path in sorted(Path(directory).rglob(".writing-*")):
        if path.is_file():
            removed.append({"file":str(path.relative_to(directory)), "bytes":path.stat().st_size})
            path.unlink(missing_ok=True)
    return removed


def atomic_copy(source, target):
    with atomic_file(target) as handle:
        handle.write(Path(source).read_bytes())


def xml_tree(element):
    # Attribute order and formatting indentation do not change parsed content.
    return (element.tag, tuple(sorted(element.attrib.items())),
            (element.text or "").strip(), (element.tail or "").strip(),
            tuple(xml_tree(child) for child in element))


def validate_artifacts(directory):
    records = {}
    for path in sorted(Path(directory).rglob("*")):
        if not path.is_file():
            continue
        name = str(path.relative_to(directory))
        if path.name.startswith(".writing-"):
            continue  # Scratch litter is cleaned/logged separately.
        if path.stat().st_size == 0:
            raise RuntimeError(f"Incomplete artifact: {name}")
        suffix = path.suffix
        detail = {"bytes": path.stat().st_size}
        if suffix == ".png":
            with Image.open(path) as im:
                im.verify()
            with Image.open(path) as im:
                im.load()
                detail.update(format="PNG", dimensions=list(im.size))
        elif suffix == ".svg":
            root = ET.parse(path).getroot()
            if root.tag != "{http://www.w3.org/2000/svg}svg":
                raise RuntimeError(f"Not an SVG: {name}")
            detail["format"] = "SVG parsed XML"
        elif suffix == ".pdf":
            if not path.read_bytes().rstrip().endswith(b"%%EOF"):
                raise RuntimeError(f"Incomplete PDF: {name}")
            with fitz.open(path) as doc:
                if doc.is_repaired or len(doc) == 0:
                    raise RuntimeError(f"PDF required repair or has no pages: {name}")
                for page in doc:
                    page.get_pixmap(dpi=100)
                detail.update(format="PDF decoded pages", pages=len(doc))
        elif suffix in (".json", ".ipynb"):
            json.loads(path.read_text())
            if suffix == ".ipynb":
                nbformat.validate(nbformat.read(path, as_version=4))
            detail["format"] = "parsed JSON"
        elif suffix == ".csv" or path.name.endswith(".csv.gz"):
            opener = gzip.open if suffix == ".gz" else open
            with opener(path, "rt", newline="") as handle:
                reader = csv.reader(handle, strict=True)
                header = next(reader)
                count = 0
                for row in reader:
                    if len(row) != len(header):
                        raise RuntimeError(f"Incomplete CSV row: {name}:{count+2}")
                    count += 1
            detail.update(format="parsed CSV", rows=count, columns=len(header))
        elif suffix == ".html":
            if not path.read_text().rstrip().endswith("</html>"):
                raise RuntimeError(f"Incomplete HTML: {name}")
            detail["format"] = "HTML end marker"
        else:
            path.read_text()
            detail["format"] = "decoded text"
        records[name] = detail
    return records


def figures_equal(a, b):
    if a.suffix == ".png":
        with Image.open(a) as left, Image.open(b) as right:
            return np.array_equal(np.asarray(left.convert("RGBA")), np.asarray(right.convert("RGBA")))
    if a.suffix == ".svg":
        return xml_tree(ET.parse(a).getroot()) == xml_tree(ET.parse(b).getroot())
    if a.suffix == ".pdf":
        with fitz.open(a) as left, fitz.open(b) as right:
            if len(left) != len(right):
                return False
            for p, q in zip(left, right):
                x, y = p.get_pixmap(dpi=100), q.get_pixmap(dpi=100)
                if (x.width, x.height, x.n, x.samples) != (y.width, y.height, y.n, y.samples):
                    return False
            return True
    raise ValueError("Unknown figure format")
