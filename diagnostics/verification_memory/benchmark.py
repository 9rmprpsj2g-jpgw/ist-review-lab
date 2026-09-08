"""Benchmark unchanged durable JSON verification on retained actual census audits."""
import argparse
from contextlib import contextmanager
import gc
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src import durable_io as io
from src.data import load_collection
HERE=Path(__file__).resolve().parent
STORE=ROOT/'audit_store/verification_memory'


def rss_kib():
    fields=dict(line.split(':',1) for line in Path('/proc/self/status').read_text().splitlines() if ':' in line)
    return int(fields['VmRSS'].split()[0])


def child(path, name):
    X,ids,topics,info=load_collection()  # hold the real feature matrix, no fits
    with path.open() as f:value=json.load(f)
    gc.collect()
    report={'input':str(path.relative_to(ROOT)),'input_bytes':path.stat().st_size,
            'rounds':len(value['rounds'])-1,'margin_entries':sum(len(r['candidate_margins']['rows']) for r in value['rounds'] if r['candidate_margins'] is not None),
            'rss_before_kib':rss_kib(),'hwm_before_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            'feature_matrix_bytes':sum(a.nbytes for a in [X.data,X.indices,X.indptr]),'operations':[]}
    def timed(kind,func):
        def wrapped(*args,**kwargs):
            started=time.perf_counter();result=func(*args,**kwargs)
            report['operations'].append({'kind':kind,'seconds':time.perf_counter()-started,
                'rss_after_kib':rss_kib(),'hwm_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
            return result
        return wrapped
    original_atomic=io.atomic_file
    @contextmanager
    def measured_atomic(*args,**kwargs):
        kwargs['validator']=timed('full_value_equality',kwargs['validator'])
        with original_atomic(*args,**kwargs) as stream:
            yield stream
            report['serialization_finished_at']=time.perf_counter()
    old_parse,old_hash=io.parse_count,io.sha256_file
    io.atomic_file=measured_atomic
    io.parse_count=timed('parse_count',old_parse)
    io.sha256_file=timed('disk_hash',old_hash)
    started=time.perf_counter()
    dest=STORE/(name+'.json')
    digest=io.atomic_json(dest,value)
    finished=time.perf_counter()
    report.update(write_and_verify_seconds=finished-started,
        post_serialization_seconds=finished-report.pop('serialization_finished_at'),
        verification_seconds=sum(x['seconds'] for x in report['operations']),
        verification_peak_rss_kib=max(x['hwm_kib'] for x in report['operations']),
        rss_after_kib=rss_kib(),output_sha256=digest,output_bytes=dest.stat().st_size)
    io.atomic_file=original_atomic;io.parse_count=old_parse;io.sha256_file=old_hash
    io.atomic_json(HERE/(name+'.json'),report)
    print(json.dumps({k:v for k,v in report.items() if k!='operations'}),flush=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--child',type=Path);parser.add_argument('--name');args=parser.parse_args()
    if args.child:return child(args.child,args.name)
    if STORE.exists():raise ValueError('Benchmark store exists; do not overwrite')
    STORE.mkdir(parents=True)
    manifest=json.loads((ROOT/'audit_manifests/20260907_census_18add1f5ba0e.json').read_text())
    entry=max((e for e in manifest['entries'] if e['policy']=='fixed_10'),key=lambda e:e['byte_size'])
    source=ROOT/'audit_store'/manifest['generation_id']/entry['filename']
    if io.sha256_file(source)!=entry['sha256'] or source.stat().st_size!=entry['byte_size']:raise AssertionError('Benchmark source integrity failure')
    from src.census import validate_audit
    validate_audit(source,(entry['topic'],entry['seed'],entry['policy'],entry['budget']))
    with source.open() as f:value=json.load(f)
    paths=[]
    for numerator in [1,2]:
        rounds=1+(len(value['rounds'])-1)*numerator//4
        end=value['batch_ends'][rounds-1]
        part={**value,'rounds':value['rounds'][:rounds],'row_order':value['row_order'][:end],
            'batch_ends':value['batch_ends'][:rounds],'observed_labels':value['observed_labels'][:end],
            'budget':end}
        path=STORE/f'prefix_{numerator}quarters.json';io.atomic_json(path,part);paths.append(path)
    paths.append(source)
    del value,part;gc.collect()
    provenance={'source_manifest':str((ROOT/'audit_manifests/20260907_census_18add1f5ba0e.json').relative_to(ROOT)),
        'source_entry':entry,'method':'Actual census audit plus actual round prefixes for size scaling; no model fits. Fresh process per measurement, holds real feature matrix and deserialized audit throughout verification. JSON load creates independent Python objects (conservative versus shared ID strings in a freshly generated audit). Warm-cache local filesystem; no cold-cache claim.',
        'cgroup_memory_max':Path('/sys/fs/cgroup/memory.max').read_text().strip(),
        'cgroup_memory_current_before':Path('/sys/fs/cgroup/memory.current').read_text().strip()}
    io.atomic_json(HERE/'provenance.json',provenance)
    for index,path in enumerate(paths):
        for repeat in range(2):
            name=f'size{index}_repeat{repeat}'
            subprocess.run([sys.executable,str(ROOT/'scripts/capture_command.py'),str(HERE/(name+'.log')),sys.executable,__file__,'--child',str(path),'--name',name],check=True,cwd=ROOT)
            record=json.loads((HERE/(name+'.json')).read_text())
            output=STORE/(name+'.json')
            if io.sha256_file(output)!=record['output_sha256'] or output.stat().st_size!=record['output_bytes']:raise AssertionError('Benchmark post-exit integrity failure')
            print(name,record['verification_peak_rss_kib'],record['verification_seconds'],flush=True)
    print('COMPLETE',flush=True)


if __name__=='__main__':main()
