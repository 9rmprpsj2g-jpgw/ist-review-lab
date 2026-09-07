"""Summarize convergence findings against already-persisted Phase 1 targets."""
import collections,csv,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
report=json.loads((HERE/'report.json').read_text())
if report['status']!='COMPLETE':raise ValueError('Do not summarize an incomplete diagnostic')
metrics=list(csv.DictReader((ROOT/'phase1_outputs/metrics_by_run.csv').open()))
counts=collections.Counter();failures=[]
for run in report['runs']:
    for line in (ROOT/run['ledger']).read_text().splitlines():
        fit=json.loads(line)
        if fit['converged']:continue
        counts[(fit['topic'],fit['policy'])]+=1
        item={k:fit[k] for k in ('topic','seed','policy','fit_index','round_index','labeled_prefix_end','n_iter')}
        for target in (75,80,90):
            matches=[m for m in metrics if m['topic']==fit['topic'] and int(m['seed'])==fit['seed'] and m['policy']==fit['policy'] and m['metric']==f'effort_at_{target}']
            if len(matches)!=1:raise ValueError('Missing/ambiguous persisted target')
            m=matches[0];item[f'effort_at_{target}']=float(m['value']) if m['status']=='OBSERVED' else None
            item[f'precedes_{target}_target']=(fit['labeled_prefix_end']<float(m['value'])) if m['status']=='OBSERVED' else None
        failures.append(item)
summary={'runs_checked':report['runs_completed'],'fits_checked':report['fits_checked'],
 'nonconverged_fits':report['nonconverged_fits'],'affected_runs':len({(f['topic'],f['seed'],f['policy']) for f in failures}),
 'counts':[{'topic':t,'policy':p,'count':c} for (t,p),c in sorted(counts.items())],
 'failures':failures,'overshoot_interpretation':'Among auto_tar and fixed_20, no flagged fit precedes a 75% or 80% target. C15/11/fixed_20 fit 209 follows 4161 reviews and precedes the 90% crossing at 4283 (committed 4301); the 90% trajectory therefore includes an upstream non-converged fit. A fully converged counterfactual outcome is unknown.'}
original_log=ROOT/'results/run.log'
summary['original_log_sha256']=hashlib.sha256(original_log.read_bytes()).hexdigest()
summary['original_warning_lines']=[{'line':i,'text':line} for i,line in enumerate(original_log.read_text().splitlines(),1) if 'ConvergenceWarning' in line]
(HERE/'findings.json').write_text(json.dumps(summary,indent=2)+'\n')
with (HERE/'nonconverged_fits.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(failures[0]));writer.writeheader();writer.writerows(failures)
