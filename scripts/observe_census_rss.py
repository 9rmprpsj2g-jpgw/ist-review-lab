"""Host-PID-aware sidecar observer; does not signal or alter the census."""
import json
from pathlib import Path
import time
import sys

root_pid=int(sys.argv[1]);destination=Path(sys.argv[2]);expected='-m src.census --plan configs/census.json --jobs 2'
cmd=(Path('/proc')/str(root_pid)/'cmdline').read_bytes().replace(b'\0',b' ').decode()
if expected not in cmd:raise ValueError('Unexpected observation target')
started=time.time();peak=0;high={};samples=0
while (Path('/proc')/str(root_pid)).exists():
    info={}
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():continue
        try:
            fields={line.split(':',1)[0]:line.split(':',1)[1].strip() for line in (p/'status').read_text().splitlines() if ':' in line}
            info[int(p.name)]=(int(fields['PPid']),int(fields.get('VmRSS','0 kB').split()[0]),int(fields.get('VmHWM','0 kB').split()[0]))
        except (OSError,ProcessLookupError):continue
    members={root_pid}
    while True:
        children={pid for pid,(parent,_,_) in info.items() if parent in members}
        if children.issubset(members):break
        members|=children
    peak=max(peak,sum(info.get(pid,(0,0,0))[1] for pid in members))
    for pid in members:high[str(pid)]=max(high.get(str(pid),0),info.get(pid,(0,0,0))[2])
    samples+=1
    result=dict(host_root_pid=root_pid,started_unix=started,elapsed_seconds=time.time()-started,
        sampled_tree_peak_rss_kib=peak,per_process_hwm_kib=high,samples=samples,
        caveat='Started after launch; per-process lifetime VmHWM includes earlier peaks. Sampled tree sum includes shared pages multiple times and can miss sub-interval peaks.')
    if samples%10==1:destination.write_text(json.dumps(result,indent=2)+'\n')
    time.sleep(.5)
result['status']='COMPLETE';destination.write_text(json.dumps(result,indent=2)+'\n')
