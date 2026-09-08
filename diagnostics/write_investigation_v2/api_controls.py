"""Application-call observation controls; verifier code and conditions unchanged."""
from contextlib import contextmanager
import importlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time
from investigate import ROOT,HERE,STORE,io,capture_failures,CAPTURES


def state(path):
    try:
        s=os.stat(path);return {'bytes':s.st_size,'inode':s.st_ino,'device':s.st_dev,'mtime_ns':s.st_mtime_ns}
    except FileNotFoundError:return {'missing':True}


def child(name):
    task=next(t for t in json.loads((HERE/'plan.json').read_text())['tasks'] if t['name']=='full_00')
    source=Path(task['input']);destination=STORE/name;destination.mkdir(exist_ok=False)
    from src.data import load_collection
    X,ids,topics,info=load_collection()
    if io.sha256_file(source)!=task['input_sha256']:raise AssertionError('Reference changed')
    with source.open() as f:value=json.load(f)
    events=[];counts={'write_calls':0,'characters_requested':0,'characters_returned':0,'short_writes':0}
    record={'name':name,'reference_sha256':task['input_sha256'],'events':events,'counts':counts,'status':'RUNNING'}
    def event(kind,**details):events.append({'kind':kind,'time_ns':time.monotonic_ns(),**details})
    originals={k:getattr(io,k) for k in ['atomic_file','parse_count','sha256_file']}
    old_replace,old_fsync=os.replace,os.fsync
    def replace(source,target):
        event('replace_before',source=str(source),target=str(target),source_state=state(source),target_state=state(target))
        result=old_replace(source,target)
        event('replace_returned',source_state=state(source),target_state=state(target))
        return result
    def fsync(fd):
        s=os.fstat(fd);event('fsync_before',fd=fd,bytes=s.st_size,inode=s.st_ino)
        result=old_fsync(fd)
        s=os.fstat(fd);event('fsync_returned',fd=fd,bytes=s.st_size,inode=s.st_ino)
        return result
    def observed(kind,fn,path,*args):
        event(kind+'_before',path=str(path),state=state(path))
        try:
            result=fn(path,*args)
            event(kind+'_returned',path=str(path),state=state(path),result=result)
            return result
        except BaseException as e:
            event(kind+'_raised',path=str(path),state=state(path),error=repr(e));raise
    class Stream:
        def __init__(self,stream):self.stream=stream
        def write(self,text):
            counts['write_calls']+=1;counts['characters_requested']+=len(text)
            n=self.stream.write(text);counts['characters_returned']+=n
            counts['short_writes']+=int(n!=len(text))
            return n
        def __getattr__(self,name):return getattr(self.stream,name)
    @contextmanager
    def atomic(*args,**kwargs):
        validate=kwargs['validator'];kwargs['validator']=lambda p:observed('value_check',validate,p)
        with originals['atomic_file'](*args,**kwargs) as stream:
            yield Stream(stream)
            event('serialization_returned',counts=dict(counts))
    io.atomic_file=atomic
    io.parse_count=lambda p,k:observed('parse_count',originals['parse_count'],p,k)
    io.sha256_file=lambda p:observed('hash',originals['sha256_file'],p)
    os.replace=replace;os.fsync=fsync
    try:
        with capture_failures():
            digest=io.atomic_json(destination/'artifact.json',value)
        if digest!=task['input_sha256']:raise AssertionError('Reference byte mismatch')
        record.update(status='PASS',sha256=digest,output=str(destination/'artifact.json'))
    except BaseException as e:
        record.update(status='FAIL',error=repr(e))
        if isinstance(e,json.JSONDecodeError):
            payload=e.doc.encode('utf-8');record['decode_position']=e.pos
        else:payload=None
    finally:
        os.replace=old_replace;os.fsync=old_fsync
        importlib.reload(io)
        record['preserved']=list(CAPTURES);record['peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if record['status']=='FAIL' and payload is not None:
        io.write_bytes(destination/'rejected_read_buffer.bin',payload)
        record['rejected_read_buffer']=str(destination/'rejected_read_buffer.bin')
    io.atomic_json(HERE/(name+'_api.json'),record)
    print(name,record['status'],flush=True)


def main():
    if len(sys.argv)>1:return child(sys.argv[1])
    io.atomic_json(HERE/'api_control_plan.json',{'trials':10,'purpose':'Record standard API return values and metadata around unchanged verification; no ptrace capability, no bypass attempt, no retries. Writer proxy only counts existing write requests and returned lengths.','source':'original full audit','production_verifier_modified':False})
    for index in range(10):
        name=f'api_{index:02}'
        subprocess.run([sys.executable,str(ROOT/'scripts/capture_command.py'),str(HERE/(name+'.log')),sys.executable,__file__,name],check=True,cwd=ROOT)
        r=json.loads((HERE/(name+'_api.json')).read_text())
        if r['status']=='PASS':
            io.atomic_json(HERE/(name+'_postcheck.json'),{'sha256':io.sha256_file(r['output']),'matches_reference':io.sha256_file(r['output'])==r['reference_sha256']})
        print(name,r['status'],flush=True)


if __name__=='__main__':main()
