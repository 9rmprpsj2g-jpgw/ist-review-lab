"""Download and verify public RCV1 token/label data; no raw stories included."""
import bz2
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.preprocessing import normalize

ROOT = Path(__file__).resolve().parents[1]
URL = "https://www.csie.ntu.edu.tw/~cjlin/libsvmtools/datasets/multilabel/rcv1_topics_train.txt.bz2"


def load_collection():
    path = ROOT / "data/raw/rcv1_topics_train.txt.bz2"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with urlopen(URL, timeout=120) as response:
            path.write_bytes(response.read())
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    lock = ROOT / "data/source_lock.json"
    if lock.exists():
        expected = json.loads(lock.read_text())["sha256"]
        if digest != expected:
            raise ValueError("Dataset checksum mismatch. Do not silently replace the benchmark.")
    rows, docs, topics = [], [], []
    with bz2.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            doc_id, labels, tokens = line.rstrip("\n").split("\t", 2)
            rows.append(doc_id)
            topics.append(set(labels.split()))
            docs.append(tokens)
    if len(rows) != 23149 or len(set(rows)) != len(rows):
        raise ValueError("Unexpected RCV1 document IDs or collection size.")
    # Cornell ltc: log frequency, unsmoothed inverse document frequency,
    # cosine normalization. Pre-stemmed, scrambled token inputs from RCV1.
    vectorizer = CountVectorizer(token_pattern=r"(?u)\S+", lowercase=False, min_df=2)
    counts = vectorizer.fit_transform(docs).astype(np.float64)
    df = np.asarray((counts > 0).sum(axis=0)).ravel()
    counts.data = 1 + np.log(counts.data)
    X = normalize(counts.multiply(np.log(len(docs)/df)).tocsr())
    info = {"source_url": URL, "sha256": digest, "rows": len(rows),
            "features": X.shape[1], "nnz": X.nnz,
            "unique_token_bags": len({tuple(sorted(d.split())) for d in docs}),
            "features_fit_scope": "all unlabeled documents in the fixed review pool",
            "source_split": "RCV1-v2 chronological training partition, used as a review pool"}
    if not lock.exists():
        lock.write_text(json.dumps(info, indent=2)+"\n")
    return X, rows, topics, info
