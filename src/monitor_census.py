"""Measure subprocess wall time and sampled process-tree RSS via Linux /proc."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from .census_io import atomic_json
from .durable_io import atomic_file


def processes():
    info={}
    for directory in Path('/proc').iterdir():
        if not directory.name.isdigit():continue
        try:
            status={line.split(':',1)[0]:line.split(':',1)[1].strip() for line in (directory/'status').read_text().splitlines() if ':' in line}
            info[int(directory.name)]=(int(status['PPid']),int(status.get('VmRSS','0 kB').split()[0]),int(status.get('VmHWM','0 kB').split()[0]))
        except (FileNotFoundError,ProcessLookupError,PermissionError):continue
    return info


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--plan',required=True);args=parser.parse_args()
    config=json.loads(Path(args.plan).read_text());dest=Path(config['outputs']['directory']);dest.mkdir(parents=True,exist_ok=True)
    start=time.perf_counter();peak=0;highwaters={};samples=0
    with atomic_file(dest/'run.log', 'w') as log:
        process=subprocess.Popen([sys.executable,'-m','src.census','--plan',args.plan,'--jobs','2'],stdout=log,stderr=subprocess.STDOUT)
        while process.poll() is None:
            info=processes()
            # /proc is mounted from the host PID namespace in this environment.
            # Resolve the direct child by host PPid before following descendants.
            host_parent=int(os.readlink('/proc/self'))
            roots={pid for pid,(parent,_,_) in info.items() if parent==host_parent}
            members=set(roots)
            while True:
                children={pid for pid,(parent,_,_) in info.items() if parent in members}
                if children.issubset(members):break
                members|=children
            peak=max(peak,sum(info.get(pid,(0,0,0))[1] for pid in members))
            for pid in members:highwaters[str(pid)]=max(highwaters.get(str(pid),0),info.get(pid,(0,0,0))[2])
            samples+=1
            time.sleep(.5)
        process.wait()  # Full subprocess exit precedes log publication and hashing.
        status=dict(exit_code=process.returncode,seconds_wall=time.perf_counter()-start,
            sampled_process_tree_peak_rss_kib=peak,process_peak_rss_kib=highwaters,
            samples=samples,sampling_interval_seconds=.5,
            caveat='Tree peak is sampled sum of RSS, counts shared pages per process, may miss sub-interval peaks. Per-process VmHWM observed while alive; worker ru_maxrss also recorded per run.')
        atomic_json(dest/'resources.json',status)
    print(json.dumps(status),flush=True)
    raise SystemExit(process.returncode)


if __name__=='__main__':main()
