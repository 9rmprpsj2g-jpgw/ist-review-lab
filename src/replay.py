"""Replay a complete reference run without overwriting its audit or metrics."""

import sys as _durable_sys
from pathlib import Path as _DurablePath
_durable_sys.path.insert(0, str(_DurablePath(__file__).resolve().parents[1]))
from src import durable_io as _durable
import json
import numpy as np
from .data import ROOT,load_collection
from .learner import ReviewLearner


def main():
    X,ids,topics,_=load_collection()
    reference=json.loads((ROOT/'results/audits/C12_11_auto_tar.json').read_text())
    truth=np.array(['C12' in t for t in topics],dtype=np.uint8)
    learner=ReviewLearner(X,'auto_tar',11)
    initial=int(np.random.default_rng(11).choice(np.flatnonzero(truth)))
    learner.observe([initial],[1]);order=[initial]
    while len(order)<5000:
        batch=learner.query(5000-len(order));learner.observe(batch,truth[batch]);order+=batch.tolist()
    assert order==reference['row_order'], 'Replay diverged from the saved reference.'
    result={'status':'PASS','topic':'C12','seed':11,'policy':'auto_tar',
            'identical_review_positions':5000,'reference_preserved':True}
    _durable.write_text(ROOT/'results/replay_verification.json', json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
