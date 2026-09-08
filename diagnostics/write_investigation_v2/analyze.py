"""Read-only byte comparisons and trial counts; never a verifier relaxation."""
import collections
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from src.durable_io import atomic_json,sha256_file
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def difference(a,b):
    if a==b:return None
    if a.startswith(b) or b.startswith(a):return min(len(a),len(b))
    for start in range(0,min(len(a),len(b)),1024*1024):
        aa,bb=a[start:start+1024*1024],b[start:start+1024*1024]
        if aa!=bb:
            return start+next(i for i,(x,y) in enumerate(zip(aa,bb)) if x!=y)


def inspect(path,reference):
    a=reference.read_bytes();b=path.read_bytes();d=difference(a,b);offset=70109136
    context=lambda payload,p:{'start':max(0,p-64),'end':min(len(payload),p+65),'ascii':payload[max(0,p-64):p+65].decode('ascii',errors='backslashreplace'),'hex':payload[max(0,p-64):p+65].hex()}
    return {'file':str(path),'reference':str(reference),'bytes':len(b),'reference_bytes':len(a),'sha256':sha256_file(path),
        'first_divergence_zero_based':d,'exact_prefix':a.startswith(b),
        'classification':'identical' if a==b else 'tail truncation; retained prefix identical' if a.startswith(b) else 'non-prefix difference',
        'missing_tail_bytes':len(a)-len(b) if a.startswith(b) else None,
        'byte_70109136':b[offset] if offset<len(b) else None,'reference_byte_70109136':a[offset] if offset<len(a) else None,
        'requested_offset_is_past_EOF':offset>=len(b),'failed_context_at_requested_offset':context(b,offset),
        'reference_context_at_requested_offset':context(a,offset),
        'failed_tail':context(b,len(b)),'reference_at_first_divergence':context(a,d) if d is not None else None}


def main():
    plan=json.loads((HERE/'plan.json').read_text());groups=collections.defaultdict(list);forensics=[];rechecks=[]
    for task in plan['tasks']:
        p=HERE/(task['name']+'_receipt.json')
        if not p.exists():raise ValueError('Trial incomplete: '+task['name'])
        r=json.loads(p.read_text());groups[task['group']].append(r)
        if r['status']=='PASS':
            output=Path(r['output']);actual=sha256_file(output)
            rechecks.append({'trial':task['name'],'actual_sha256':actual,'expected_sha256':task['input_sha256'],'matches':actual==task['input_sha256']})
        else:
            paths=[Path(i['path']) for i in r['preserved']]
            if r.get('rejected_read_buffer'):paths.append(Path(r['rejected_read_buffer']))
            for path in paths:forensics.append({'trial':task['name'],**inspect(path,Path(task['input']))})
    counts=[]
    for group,rs in groups.items():
        counts.append({'group':group,'trials':len(rs),'failures':sum(r['status']!='PASS' for r in rs),'failure_fraction':sum(r['status']!='PASS' for r in rs)/len(rs),
            'bytes':rs[0]['task']['input_bytes'],'minimum_disk_available_bytes':min(r['before']['disk_available_bytes'] for r in rs),
            'max_peak_rss_kib':max(r['after']['peak_rss_kib'] for r in rs),
            'memory_event_snapshots':sorted(set(r['after']['memory_events'] for r in rs)),
            'rlimit_fsize':rs[0]['before']['rlimit_fsize'],'rlimit_as':rs[0]['before']['rlimit_as'],
            'failed_trials':[r['task']['name'] for r in rs if r['status']!='PASS']})
    atomic_json(HERE/'rates.json',counts)
    atomic_json(HERE/'trial_byte_forensics.json',forensics)
    atomic_json(HERE/'successful_trial_recheck.json',rechecks)
    print(json.dumps(counts,indent=2))
    print('Later changed published files:',[r['trial'] for r in rechecks if not r['matches']])


if __name__=='__main__':main()
