"""Independently recompute all stored metrics from the audit trail."""

import sys as _durable_sys
from pathlib import Path as _DurablePath
_durable_sys.path.insert(0, str(_DurablePath(__file__).resolve().parents[1]))
from src import durable_io as _durable
import json
import math
import numpy as np
import pandas as pd
from .data import load_collection, ROOT


def main():
    _, ids, topics, _=load_collection()
    frame=pd.read_csv(ROOT/'results/runs.csv')
    config=json.loads((ROOT/'experiment_plan.json').read_text())
    expected={(t,s,p) for t in config['topics'] for s in config['seeds'] for p in config['policies']}
    actual=set(zip(frame.topic,frame.seed,frame.policy))
    assert actual==expected and len(frame)==len(expected), 'Missing or duplicated runs'
    checks=0
    for row in frame.itertuples(index=False):
        audit=json.loads((ROOT/f'results/audits/{row.topic}_{row.seed}_{row.policy}.json').read_text())
        order=audit['row_order']
        assert len(order)==config['budget'] and len(set(order))==len(order)
        assert all(0<=i<len(ids) for i in order)
        truth=[int(row.topic in topics[i]) for i in order]
        assert truth==audit['observed_labels']
        assert ids[order[0]]==str(row.seed_doc_id)
        total=sum(row.topic in t for t in topics)
        assert total==row.positives and truth[0]==1
        for k in (20,100,500,1000,2000,5000):
            found=sum(truth[:k])
            assert math.isclose(getattr(row,f'recall_at_{k}'),found/total,abs_tol=1e-12)
            assert math.isclose(getattr(row,f'precision_at_{k}'),found/k,abs_tol=1e-12)
            checks+=2
        cumulative=0; hits={75:None,90:None}
        for effort,label in enumerate(truth,start=1):
            cumulative+=label
            for target in hits:
                if hits[target] is None and cumulative>=math.ceil(target*total/100):hits[target]=effort
        for target,expected_effort in hits.items():
            value=getattr(row,f'effort_at_{target}')
            assert (pd.isna(value) if expected_effort is None else value==expected_effort)
            if expected_effort:
                assert math.isclose(getattr(row,f'wss_at_{target}'),target/100-expected_effort/len(ids),abs_tol=1e-12)
                assert getattr(row,f'batch_effort_at_{target}')==next(b for b in audit['batch_ends'] if b>=expected_effort)
            checks+=1
    assert frame.groupby(['topic','seed']).seed_doc_id.nunique().eq(1).all()
    result={'status':'PASS','verified_runs':len(frame),'metric_comparisons':checks,
            'checks':['unique review IDs','matched seeds across methods','revealed labels match source',
                      'fixed budget respected','independent precision and recall arithmetic',
                      'censored recall thresholds','batch-complete effort','WSS definition']}
    _durable.write_text(ROOT/'results/verification.json', json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
