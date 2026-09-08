"""Prespecified independent I/O trials, never production retries or model runs."""
import argparse
import bisect
from contextlib import contextmanager
import gc
import importlib.util
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src import durable_io as io
HERE=Path(__file__).resolve().parent
STORE=ROOT/'audit_store/write_investigation'
RAM=Path('/dev/shm/ist_review_write_investigation')


def machine(path):
    v=os.statvfs(path)
    return {'disk_available_bytes':v.f_bavail*v.f_frsize,'disk_free_inodes':v.f_favail,
        'memory_current':Path('/sys/fs/cgroup/memory.current').read_text().strip(),
        'memory_events':Path('/sys/fs/cgroup/memory.events').read_text(),
        'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'rlimit_fsize':resource.getrlimit(resource.RLIMIT_FSIZE),
        'rlimit_as':resource.getrlimit(resource.RLIMIT_AS)}


def child(task):
    path=Path(task['input']);destination=Path(task['destination']);destination.mkdir(parents=True,exist_ok=False)
    report={'task':task,'status':'RUNNING','pid':os.getpid(),'before':machine(destination),'preserved':[]}
    original_unlink=Path.unlink
    def preserve_then_unlink(p,*args,**kwargs):
        if p.parent==destination and p.exists() and (p.name.startswith('.writing-') or p.name=='artifact.json'):
            evidence=destination/('preserved-'+p.name+'.bin')
            os.link(p,evidence)
            report['preserved'].append({'path':str(evidence),'size_at_capture':p.stat().st_size,'inode':p.stat().st_ino})
        return original_unlink(p,*args,**kwargs)
    Path.unlink=preserve_then_unlink  # failure cleanup observation only; all guards still raise
    started=time.perf_counter()
    try:
        if io.sha256_file(path)!=task['input_sha256']:raise AssertionError('Investigation input changed')
        if task['method']=='instrumented':
            spec=importlib.util.spec_from_file_location('memory_benchmark',ROOT/'diagnostics/verification_memory/benchmark.py')
            benchmark=importlib.util.module_from_spec(spec);spec.loader.exec_module(benchmark)
            benchmark.STORE=destination;benchmark.HERE=HERE
            benchmark.child(path,task['name'])  # unchanged prior timing wrapper and writer
            output=destination/(task['name']+'.json')
        else:
            from src.data import load_collection
            X,ids,topics,info=load_collection()  # same matrix residency; no fit
            with path.open() as f:value=json.load(f)
            output=destination/'artifact.json'
            if task['method']=='native':
                io.atomic_json(output,value)
            elif task['method']=='plain':
                # Diagnostic comparator, not a proposed replacement writer.
                fd,temporary=tempfile.mkstemp(prefix='.writing-',dir=destination)
                temporary=Path(temporary)
                try:
                    with os.fdopen(fd,'w',encoding='utf-8') as stream:
                        json.dump(value,stream,allow_nan=False);stream.write('\n')
                        stream.flush();os.fsync(stream.fileno())
                    with temporary.open() as stream:
                        if json.load(stream)!=value:raise AssertionError('Plain comparator full-value mismatch')
                    if io.sha256_file(temporary)!=task['input_sha256']:raise AssertionError('Plain comparator byte mismatch')
                    os.replace(temporary,output);io._sync_directory(destination)
                    with output.open() as stream:
                        if json.load(stream)!=value:raise AssertionError('Plain comparator post-publication mismatch')
                finally:temporary.unlink(missing_ok=True)
            else:raise ValueError('Unknown diagnostic method')
        report['output']=str(output);report['output_sha256']=io.sha256_file(output)
        report['output_bytes']=output.stat().st_size
        if report['output_sha256']!=task['input_sha256']:raise AssertionError('Published artifact differs from reference input')
        report['status']='PASS'
    except BaseException as error:
        report.update(status='FAIL',error=repr(error),traceback=traceback.format_exc())
        if isinstance(error,json.JSONDecodeError):
            report['decode_position']=error.pos;report['decode_buffer_characters']=len(error.doc)
            # Preserve exactly the string that the parser rejected, separately from staged bytes.
            payload=error.doc.encode('utf-8')
            io.write_bytes(destination/'rejected_read_buffer.bin',payload)
            report['rejected_read_buffer']=str(destination/'rejected_read_buffer.bin')
        print(report['traceback'],flush=True)
    finally:
        Path.unlink=original_unlink
        report['seconds_wall']=time.perf_counter()-started;report['after']=machine(destination)
        # A benchmark wrapper may still be installed after an exception. Restore from module reload
        # ONLY to publish the diagnostic receipt, never to retry the failed artifact.
        __import__('importlib').reload(io)
        for item in report['preserved']:
            p=Path(item['path']);item.update(bytes=p.stat().st_size,sha256=io.sha256_file(p))
        io.atomic_json(HERE/(task['name']+'_receipt.json'),report)
    print(json.dumps({'trial':task['name'],'status':report['status'],'seconds':report['seconds_wall']}),flush=True)


def prepare():
    if STORE.exists() or RAM.exists():raise ValueError('Investigation directory already exists')
    STORE.mkdir(parents=True);RAM.mkdir()
    manifest=json.loads((ROOT/'audit_manifests/20260907_census_18add1f5ba0e.json').read_text())
    entry=next(e for e in manifest['entries'] if e['filename']=='C12_11_fixed_10.json')
    source=ROOT/'audit_store'/manifest['generation_id']/entry['filename']
    if io.sha256_file(source)!=entry['sha256']:raise AssertionError('Source digest differs from committed manifest')
    with source.open() as f:full=json.load(f)
    inputs={'full':source}
    for mib in [20,40,60,70,80,100]:
        target=mib*2**20
        count=min(len(full['rounds']),max(2,int((target-2**20)/source.stat().st_size*len(full['rounds']))))
        while True:
            end=full['batch_ends'][count-1]
            value={**full,'rounds':full['rounds'][:count],'row_order':full['row_order'][:end],
                'observed_labels':full['observed_labels'][:end],'batch_ends':full['batch_ends'][:count],
                'budget':end,'_diagnostic_only':'Size-controlled I/O input, not a retrieval outcome','_diagnostic_padding':''}
            size=len((json.dumps(value,allow_nan=False)+'\n').encode())
            if size<=target:break
            count-=5
        value['_diagnostic_padding']=' '*(target-size)
        path=STORE/f'input_{mib}MiB.json';io.atomic_json(path,value)
        if path.stat().st_size!=target:raise AssertionError('Size-sweep input size mismatch')
        inputs[str(mib)]=path
    tasks=[]
    def add(group,key,method,base,repeats):
        for repeat in range(repeats):
            name=f'{group}_{repeat:02}'
            tasks.append({'name':name,'group':group,'method':method,'input':str(inputs[key]),
                'input_sha256':io.sha256_file(inputs[key]),'input_bytes':inputs[key].stat().st_size,
                'destination':str(base/name)})
    add('full','full','instrumented',STORE,20)
    for mib in [20,40,60,70,80,100]:add(f'size{mib}',str(mib),'instrumented',STORE,10)
    add('native_overlay','full','native',STORE,5)
    add('plain_overlay','full','plain',STORE,5)
    add('instrumented_tmpfs','full','instrumented',RAM,5)
    mounts=[{'mountpoint':s.split()[4],'filesystem':s.split(' - ')[1].split()[0]} for s in Path('/proc/self/mountinfo').read_text().splitlines() if s.split()[4] in ['/','/workspace','/dev/shm','/tmp']]
    io.atomic_json(HERE/'plan.json',{'status':'PRESPECIFIED_BEFORE_TRIALS','tasks':tasks,'source_entry':entry,'mounts':mounts,
        'design':'95 separate serial trials, unique paths, fresh process each; 20 full, 10 per six exact sizes, three controls x5. Failure is an observed endpoint, never retried or relabeled successful. No models. Metadata/input-validation errors stop the investigation.',
        'padding':'20–80 MiB use real round prefixes plus whitespace-string padding; 100 MiB holds the entire real audit plus padding. Tests serialized byte size, not larger genuine census outcomes.',
        'machine':machine(STORE)})
    return tasks


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--child');args=parser.parse_args()
    if args.child:
        task=next(t for t in json.loads((HERE/'plan.json').read_text())['tasks'] if t['name']==args.child)
        return child(task)
    tasks=prepare()
    for task in tasks:
        subprocess.run([sys.executable,str(ROOT/'scripts/capture_command.py'),str(HERE/(task['name']+'.log')),sys.executable,__file__,'--child',task['name']],check=True,cwd=ROOT)
        receipt=json.loads((HERE/(task['name']+'_receipt.json')).read_text())
        if receipt['status']=='PASS':
            if io.sha256_file(receipt['output'])!=task['input_sha256']:
                receipt['status']='FAIL_POST_EXIT';receipt['post_exit_sha256']=io.sha256_file(receipt['output'])
                io.atomic_json(HERE/(task['name']+'_post_exit.json'),receipt)
        if 'Investigation input changed' in receipt.get('error',''):raise AssertionError('Input integrity stop')
        print(json.dumps({'trial':task['name'],'status':receipt['status']}),flush=True)
    print('ALL_TRIALS_FINISHED',flush=True)


if __name__=='__main__':main()
