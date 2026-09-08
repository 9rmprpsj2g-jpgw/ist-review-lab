"""Five separately declared syscall-observation controls; no retries."""
import json
from pathlib import Path
import subprocess
import sys
from investigate import ROOT,HERE,STORE,io

plan=json.loads((HERE/'plan.json').read_text())
reference=next(t for t in plan['tasks'] if t['name']=='full_00')
program="import sys,json;sys.path.insert(0,sys.argv[1]);from investigate import child,capture_failures\nwith capture_failures(): child(json.loads(sys.argv[2]))"
for index in range(5):
    name=f'trace_native_{index:02}'
    task={**reference,'name':name,'group':'trace_native','method':'native','destination':str(STORE/name)}
    io.atomic_json(HERE/(name+'_task.json'),task)
    command=['/usr/bin/strace','-f','-qq','-ttt','-yy','-s','64','-e','trace=read,write,newfstatat,openat,close,fsync,rename,renameat,renameat2,unlink,unlinkat,ftruncate,truncate,link,linkat',sys.executable,'-c',program,str(HERE),json.dumps(task)]
    subprocess.run([sys.executable,str(ROOT/'scripts/capture_command.py'),str(HERE/(name+'.strace.log')),*command],cwd=ROOT,check=True)
    receipt=json.loads((HERE/(name+'_receipt.json')).read_text())
    if receipt['status']=='PASS' and io.sha256_file(receipt['output'])!=task['input_sha256']:
        io.atomic_json(HERE/(name+'_post_exit.json'),{'status':'FAIL_POST_EXIT','actual_sha256':io.sha256_file(receipt['output']),'expected_sha256':task['input_sha256']})
    print(name,receipt['status'],flush=True)
