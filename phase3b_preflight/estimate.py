"""Read-only historical timing extrapolation and schedule arithmetic. No experiments."""

import sys as _durable_sys
from pathlib import Path as _DurablePath
_durable_sys.path.insert(0, str(_DurablePath(__file__).resolve().parents[1]))
from src import durable_io as _durable
import csv,json,math,statistics,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
POLICIES=['random','seed_similarity','seed_only_frozen','uncertainty','auto_tar','fixed_20','explore_10','fixed_10','fixed_50','fixed_100','grow_5pct','grow_20pct']

def schedule(policy,budget):
    fixed=int(policy.split('_')[1]) if policy.startswith('fixed_') else None
    pct=5 if policy=='grow_5pct' else 20 if policy=='grow_20pct' else 10
    k,b,rounds,entries,train,pool,max_batch=1,fixed or 1,0,0,0,0,0
    while k<budget:
        candidates=23149-k;size=min(b,budget-k)
        rounds+=1;pool+=candidates;train+=k+min(100,candidates)
        # For exploration, this is an upper bound on the retained union;
        # avoids inventing realized random overlap or carry values.
        entries+=min(candidates,1000+size) if policy=='explore_10' else min(candidates,max(1000,size))
        max_batch=max(max_batch,size);k+=size
        if not fixed:b+=math.ceil(b*pct/100)
    svm=policy not in ('random','seed_similarity')
    return dict(rounds=rounds,entries=entries if svm else 0,train=train,pool=pool,max_batch=max_batch,
                fits=(1 if policy=='seed_only_frozen' else rounds) if svm else 0)

historical=list(csv.DictReader((ROOT/'results/runs.csv').open()))
rows=[]
for p in POLICIES:
    source='fixed_20' if p.startswith('fixed_') else 'auto_tar' if p.startswith('grow_') else 'frozen_svm' if p=='seed_only_frozen' else p
    mean=statistics.mean(float(r['seconds']) for r in historical if r['policy']==source)
    base=schedule('seed_only_frozen' if source=='frozen_svm' else source,5000);s=schedule(p,23149)
    if p in ('random','seed_similarity','seed_only_frozen'):
        scales=[s['rounds']/base['rounds'],s['pool']/base['pool']]
    else:scales=[s['rounds']/base['rounds'],s['train']/base['train'],s['pool']/base['pool']]
    lo=s['entries']*24+23149*80+s['rounds']*400+s['fits']*3000
    hi=2*lo
    # Explicit Python representation estimate for accumulated audit objects:
    # one float/int/string + three list references per margin, plus metadata.
    per_entry=sys.getsizeof(0.)+sys.getsizeof(0)+sys.getsizeof('000000000000')+3*8
    audit_ram=s['entries']*per_entry+23149*160+s['rounds']*800+s['fits']*6000
    rows.append(dict(policy=p,**s,source_timing_policy=source,historical_mean_seconds=mean,
        fits_all_15=s['fits']*15,worker_minutes_low=mean*min(scales)*15/60,
        worker_minutes_high=mean*max(scales)*15/60,audit_MB_all_15_low=lo*15/1e6,
        audit_MB_all_15_high=hi*15/1e6,retained_audit_plus_serialization_MB=(audit_ram+hi)/1e6))
result={'method':'Historical scaling scenarios, not confidence bounds. Times exclude new audit serialization/I/O and startup. Sequential sum is worker time; ideal two-worker elapsed is half, not a guarantee.',
        'rows':rows,'total_fits':sum(r['fits_all_15'] for r in rows),
        'worker_minutes':[sum(r['worker_minutes_'+x] for r in rows) for x in ('low','high')],
        'audit_GB':[sum(r['audit_MB_all_15_'+x] for r in rows)/1000 for x in ('low','high')],
        'matrix_CSR_bytes_float64_int32':1739103*12+(23149+1)*4,
        'peak_memory_caveat':'Retained audit and serialization estimate only. Add feature matrix, train slices, solver allocations, interpreter, loader peak and parent/worker duplication. No measured RSS available.'}
_durable.write_text(ROOT/'phase3b_preflight/estimates.json', json.dumps(result,indent=2)+'\n')
for r in rows:print(r['policy'],r['fits'],r['fits_all_15'],*[round(r[k],2) for k in ('worker_minutes_low','worker_minutes_high','audit_MB_all_15_low','audit_MB_all_15_high','retained_audit_plus_serialization_MB')],r['max_batch'])
print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))
