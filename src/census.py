"""Approved data generation only. No cross-policy analysis or hypothesis tests."""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import time
import traceback
import warnings
import numpy as np
import pandas as pd
import scipy
import sklearn
from sklearn.exceptions import ConvergenceWarning
from . import experiment
from .audit import replay_row_order
from .config import resolve_plan
from .census_io import atomic_json,sha256_file
from .data import ROOT


def initialize():
    warnings.simplefilter('error',ConvergenceWarning)
    experiment.initialize()


def feature_digest(X,ids):
    h=hashlib.sha256()
    h.update(json.dumps({'shape':X.shape,'data':str(X.data.dtype),
        'indices':str(X.indices.dtype),'indptr':str(X.indptr.dtype)} ,sort_keys=True).encode())
    for array in (X.data,X.indices,X.indptr):h.update(array.tobytes(order='C'))
    h.update(json.dumps([str(x) for x in ids],ensure_ascii=True,separators=(',',':')).encode())
    return h.hexdigest()


def validate_audit(path, expected):
    audit=json.loads(path.read_text())
    topic,seed,policy,budget=expected
    if (audit['topic'],audit['seed'],audit['policy'],audit['budget']) != expected:
        raise AssertionError('Audit run identity mismatch')
    order=replay_row_order(audit)
    if order != audit['row_order'] or len(order)!=budget or set(order)!=set(range(audit['n'])):
        raise AssertionError('Incomplete or inconsistent census order')
    ends=np.cumsum([len(r['selected_rows']) for r in audit['rounds']]).tolist()
    if ends!=audit['batch_ends'] or len(audit['observed_labels'])!=len(order):
        raise AssertionError('Audit boundary/label alignment mismatch')
    if any(v not in (0,1) for v in audit['observed_labels']):
        raise AssertionError('Invalid audit label')
    current_fit=0;reviewed=0
    for index,r in enumerate(audit['rounds']):
        count=audit['n']-reviewed if index else audit['n']-1
        if r['candidate_count']!=count:raise AssertionError('Candidate count mismatch')
        if r['margin_scope']!=audit['audit_config']['margin_scope']:raise AssertionError('Scope mismatch')
        if r['fit'] is not None:
            current_fit+=1
            if r['fit_index']!=current_fit or r['fit']['fit_index']!=current_fit:
                raise AssertionError('Fit index mismatch')
            if not np.isfinite(r['fit']['fit_seconds']) or r['fit']['fit_seconds']<0:
                raise AssertionError('Invalid fit timing')
        if r['fit_index']!=(current_fit or None):raise AssertionError('Model reference mismatch')
        m=r['candidate_margins']
        if m is not None:
            if not len(m['rows'])==len(m['values'])==len(m['document_ids']):raise AssertionError('Margin alignment mismatch')
            if len(set(m['rows']))!=len(m['rows']) or not np.isfinite(m['values']).all():raise AssertionError('Invalid margins')
            if not set(r['selected_rows']).issubset(m['rows']):raise AssertionError('Selected margins missing')
            if len(m['rows'])<r['margin_window_resolved']:raise AssertionError('Margin window truncated')
        reviewed+=len(r['selected_rows'])
    return dict(topic=topic,seed=seed,policy=policy,budget=budget,n=audit['n'],
        reviewed=len(order),rounds=len(audit['rounds'])-1,fits=current_fit,
        margin_scope=audit['audit_config']['margin_scope'],filename=path.name,
        byte_size=path.stat().st_size,sha256=sha256_file(path),validation_status='PASS')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--plan',type=Path,required=True)
    parser.add_argument('--jobs',type=int,default=2);args=parser.parse_args()
    started=time.perf_counter()
    config=resolve_plan(json.loads(args.plan.read_text()))
    if not config.get('inputs',{}).get('invoke_experiment',False):raise ValueError('Run not authorized in config')
    destination=experiment.output_directory(config['outputs']['directory'])
    audit_dir=experiment.output_directory(config['outputs']['audit_directory'])
    if audit_dir.exists():raise ValueError('Generation directory already exists; do not overwrite')
    if ROOT/'audit_store' not in audit_dir.parents:raise ValueError('Census audits must reside in audit_store')
    destination.mkdir(parents=True,exist_ok=True);audit_dir.mkdir(parents=True)
    experiment.write_configuration(config,destination)
    # Read only immutable v1 N/R columns for census integrity checks.
    old=pd.read_csv(ROOT/'results/runs.csv')
    topic_counts={}
    for topic in config['topics']:
        counts=old.loc[old.topic==topic,['n','positives']].drop_duplicates()
        if len(counts)!=1 or counts.isna().any().any():raise ValueError('Missing/inconsistent N/R')
        topic_counts[topic]=tuple(map(int,counts.iloc[0]))
    X,ids,topics,info=experiment.load_collection()
    for topic,(n,r) in topic_counts.items():
        if len(ids)!=n or sum(topic in labels for labels in topics)!=r:
            raise AssertionError('Collection disagrees with immutable N/R')
        if config['budget']!=n:raise ValueError('Every arm must run at census')
    grid=[(t,s,p,config['budget']) for t in config['topics'] for s in config['seeds'] for p in config['policies']]
    manifest=dict(generation_id=audit_dir.name,status='RUNNING',schema_version=3,
        code_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),
        resolved_config=config,config_sha256=hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest(),
        source=info,feature_matrix_sha256=feature_digest(X,ids),
        feature_digest_encoding='sorted JSON(shape,dtypes), CSR data/indices/indptr bytes in C order, compact ASCII JSON external IDs; native endian recorded by environment',
        environment=dict(python=platform.python_version(),platform=platform.platform(),numpy=np.__version__,
                         scipy=scipy.__version__,sklearn=sklearn.__version__,byteorder=__import__('sys').byteorder),
        rng_derivation='SHA-256 ist-review-lab|integer_seed|stream_name; default_rng',
        expected_grid=[dict(topic=t,seed=s,policy=p,budget=b) for t,s,p,b in grid],
        completed=0,failed=[],entries=[],archive_status='PENDING_TRANSFER')
    manifest_path=ROOT/'audit_manifests'/f'{audit_dir.name}.json'
    atomic_json(manifest_path,manifest)
    del X,ids,topics
    pool=ProcessPoolExecutor(max_workers=args.jobs,initializer=initialize)
    futures={pool.submit(experiment.simulate,(*task,config,str(destination))):task for task in grid}
    results=[]
    try:
        for future in as_completed(futures):
            task=futures[future];result=future.result()
            path=audit_dir/f'{task[0]}_{task[1]}_{task[2]}.json'
            entry=validate_audit(path,task)
            if entry['fits']!=result['fits'] or result['reviewed']!=config['budget']:
                raise AssertionError('Result/audit completeness mismatch')
            if result['positives']!=topic_counts[task[0]][1]:raise AssertionError('Result prevalence mismatch')
            manifest['entries'].append(entry);manifest['completed']+=1
            results.append(result)
            pd.DataFrame(results).to_csv(destination/'runs.csv',index=False)
            atomic_json(manifest_path,manifest)
            print(json.dumps(dict(completed=len(results),total=len(grid),topic=task[0],seed=task[1],policy=task[2],
                                  fits=entry['fits'],audit_bytes=entry['byte_size'],elapsed_seconds=time.perf_counter()-started)),flush=True)
    except BaseException as error:
        manifest['status']='FAILED';manifest['failed'].append(dict(run=futures.get(locals().get('future')),
            error=repr(error),traceback=traceback.format_exc()))
        manifest['seconds_wall']=time.perf_counter()-started
        atomic_json(manifest_path,manifest)
        for process in list(pool._processes.values()):
            if process.is_alive():os.kill(process.pid,signal.SIGTERM)
        pool.shutdown(wait=True,cancel_futures=True)
        raise
    else:pool.shutdown(wait=True)
    if manifest['completed']!=len(grid):raise AssertionError('Missing grid runs')
    manifest['status']='COMPLETE';manifest['seconds_wall']=time.perf_counter()-started
    manifest['total_audit_bytes']=sum(e['byte_size'] for e in manifest['entries'])
    manifest['total_fits']=sum(e['fits'] for e in manifest['entries'])
    atomic_json(manifest_path,manifest)
    print(json.dumps({'status':'COMPLETE','seconds_wall':manifest['seconds_wall'],
                      'audits':manifest['completed'],'bytes':manifest['total_audit_bytes']}),flush=True)


if __name__=='__main__':main()
