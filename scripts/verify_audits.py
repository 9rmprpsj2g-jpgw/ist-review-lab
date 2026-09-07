"""Standalone standard-library verifier for separately downloaded census audits.

Usage after extracting ZIPs into the same directory:
  python3 verify_audits.py audit_manifests/GENERATION.json
By default missing audits are a failure. --allow-partial permits checking a
subset of downloaded packages but never reports the complete grid verified.
"""
import argparse
import hashlib
import json
from pathlib import Path


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def verify(manifest_path,allow_partial=False):
    manifest=json.loads(manifest_path.read_text());root=manifest_path.parent.parent
    verified=[];missing=[]
    for entry in manifest['entries']:
        path=root/'audit_store'/manifest['generation_id']/entry['filename']
        if not path.exists():missing.append(entry['filename']);continue
        if path.stat().st_size!=entry['byte_size'] or digest(path)!=entry['sha256']:
            raise AssertionError(f'Byte integrity failed: {path.name}')
        audit=json.loads(path.read_text())
        for key in ('topic','seed','policy','budget','n'):
            if audit[key]!=entry[key]:raise AssertionError(f'Identity mismatch: {key}')
        order=[];ends=[]
        for index,record in enumerate(audit['rounds']):
            if record['round_index']!=index:raise AssertionError('Round index mismatch')
            if not len(record['selected_rows'])==len(record['selected_document_ids'])==len(record['selection_operators']):
                raise AssertionError('Selection alignment mismatch')
            order.extend(record['selected_rows']);ends.append(len(order))
        if order!=audit['row_order'] or ends!=audit['batch_ends'] or len(order)!=audit['n'] or set(order)!=set(range(audit['n'])):
            raise AssertionError('Incomplete census replay')
        if len(audit['observed_labels'])!=len(order):raise AssertionError('Label alignment mismatch')
        verified.append(entry['filename'])
    if len(manifest['entries'])!=len(manifest['expected_grid']):raise AssertionError('Incomplete manifest')
    expected={(r['topic'],r['seed'],r['policy'],r['budget']) for r in manifest['expected_grid']}
    found={(r['topic'],r['seed'],r['policy'],r['budget']) for r in manifest['entries']}
    if expected!=found or len(found)!=len(manifest['entries']):raise AssertionError('Grid mismatch')
    if missing and not allow_partial:raise AssertionError(f'Missing {len(missing)} audits; download the remaining ZIPs')
    return dict(status='PARTIAL_VERIFIED' if missing else 'COMPLETE_VERIFIED',
                verified=len(verified),missing=len(missing),generation_id=manifest['generation_id'])


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('manifest',type=Path)
    parser.add_argument('--allow-partial',action='store_true');args=parser.parse_args()
    print(json.dumps(verify(args.manifest,args.allow_partial),indent=2))
