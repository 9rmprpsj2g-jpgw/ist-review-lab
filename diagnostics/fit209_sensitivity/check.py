"""Isolate the effect of completing v1 C15/11/fixed_20 fit 209."""

import sys as _durable_sys
from pathlib import Path as _DurablePath
_durable_sys.path.insert(0, str(_DurablePath(__file__).resolve().parents[2]))
from src import durable_io as _durable
import copy,csv,hashlib,importlib.util,json,math,platform,subprocess,sys,warnings
from pathlib import Path
import numpy as np
import scipy,sklearn
from scipy.stats import spearmanr
from sklearn.exceptions import ConvergenceWarning
from sklearn.svm import LinearSVC
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.data import load_collection
HERE=Path(__file__).resolve().parent


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    out=ROOT/'audit_store/fit209_sensitivity'
    if out.exists():raise ValueError('Refusing to overwrite diagnostic evidence')
    out.mkdir(parents=True)
    report={'status':'RUNNING','intervention':'Only fit 209 max_iter changes to 100000; subsequent fits retain original 10000.'}
    def save():_durable.write_text(HERE/'report.json', json.dumps(report,indent=2,allow_nan=False)+'\n')
    try:
        env=json.loads((ROOT/'results/environment.json').read_text())
        for key,value in [('python',platform.python_version()),('numpy',np.__version__),('scipy',scipy.__version__),('scikit_learn',sklearn.__version__)]:
            if value!=env[key]:raise AssertionError(f'Runtime mismatch: {key}')
        original=ROOT/'results/audits/C15_11_fixed_20.json';audit=json.loads(original.read_text())
        ledger_path=ROOT/'audit_store/v1_convergence_check/C15_11_fixed_20.jsonl'
        prior=json.loads((ROOT/'diagnostics/v1_convergence/report.json').read_text())
        locked=next(r for r in prior['runs'] if r['topic']=='C15' and r['seed']==11 and r['policy']=='fixed_20')
        if digest(ledger_path)!=locked['ledger_sha256']:raise AssertionError('Reconstructed v1 ledger changed')
        ledger=[json.loads(line) for line in ledger_path.read_text().splitlines()]
        target=next(r for r in ledger if r['fit_index']==209)
        if digest(original)!=target['archive_sha256']:raise AssertionError('Original archive changed')
        X,ids,topics,info=load_collection();y=np.asarray(['C15' in ts for ts in topics],dtype=np.uint8)
        if info['sha256']!=env['data_sha256']:raise AssertionError('Source data mismatch')
        if y[audit['row_order']].tolist()!=audit['observed_labels']:raise AssertionError('Original labels mismatch')
        params=target['model_parameters'];prefix=target['labeled_prefix_end'];old_order=audit['row_order']
        reviewed=old_order[:prefix];negatives=target['temporary_negative_rows']
        train=np.asarray(reviewed+negatives);train_y=np.asarray(audit['observed_labels'][:prefix]+[0]*len(negatives))
        candidates=np.setdiff1d(np.arange(X.shape[0]),reviewed)
        train_X=X[train];candidate_X=X[candidates]
        def fit_model(parameters):
            model=LinearSVC(**parameters)
            with warnings.catch_warnings(record=True) as messages:
                warnings.simplefilter('always');model.fit(train_X,train_y)
            captured=[{'category':w.category.__name__,'message':str(w.message)} for w in messages]
            status={'max_iter':parameters['max_iter'],'n_iter':int(model.n_iter_),
                    'convergence_warning':any(issubclass(w.category,ConvergenceWarning) for w in messages),'warnings':captured}
            return model,status
        baseline,bstatus=fit_model(params)
        if bstatus['n_iter']!=target['n_iter'] or bstatus['convergence_warning']!=(not target['converged']):
            raise AssertionError('Baseline convergence diagnostic does not reproduce')
        low=baseline.decision_function(candidate_X);low_rank=candidates[np.lexsort((candidates,-low))]
        expected=old_order[prefix:audit['batch_ends'][209]]
        if low_rank[:20].tolist()!=expected:raise AssertionError('Baseline selected batch differs from archive')
        high_params={**params,'max_iter':100000}
        converged,hstatus=fit_model(high_params)
        report.update(topic='C15',seed=11,policy='fixed_20',fit_index=209,reviewed_before_fit=prefix,
            candidates=len(candidates),baseline=bstatus,probe=hstatus,original_parameters=params,
            archive_sha256=digest(original),ledger_sha256=digest(ledger_path))
        save()
        if hstatus['convergence_warning']:raise RuntimeError('Diagnostic ceiling exhausted; do not raise again')
        high=converged.decision_function(candidate_X);high_rank=candidates[np.lexsort((candidates,-high))]
        selected=high_rank[:20].tolist()
        correlation=float(spearmanr(low,high).statistic)
        if not math.isfinite(correlation):raise ValueError('Undefined rank correlation')
        report.update(spearman_rank_correlation=correlation,
            removed_rows=sorted(set(expected)-set(selected)),added_rows=sorted(set(selected)-set(expected)),
            ordered_batch_positions_changed=sum(a!=b for a,b in zip(expected,selected)),
            ordered_batch_identical=selected==expected)
        with _durable.atomic_file(out/'candidate_margins.npz', 'wb', expected_count=3) as stream:
            np.savez_compressed(stream,rows=candidates,baseline=low,converged=high)
        # Recover RNG state through the audited temporary-negative draw for fit 209.
        source=ROOT/'diagnostics/v1_convergence/source/learner_v1.py'
        if source.read_bytes()!=subprocess.check_output(['git','show','v1-frozen:src/learner.py'],cwd=ROOT):raise AssertionError('Frozen source changed')
        spec=importlib.util.spec_from_file_location('v1_fixed20',source);v1=importlib.util.module_from_spec(spec);spec.loader.exec_module(v1)
        rng=np.random.default_rng(11)
        for record in ledger[:209]:
            remaining=np.setdiff1d(np.arange(X.shape[0]),old_order[:record['labeled_prefix_end']])
            draw=rng.choice(remaining,min(100,len(remaining)),replace=False)
            if draw.tolist()!=record['temporary_negative_rows']:raise AssertionError('Historical negative-draw reconstruction mismatch')
        fit_records=[]
        class ProbeLearner(v1.ReviewLearner):
            def fit(self):
                with warnings.catch_warnings(record=True) as messages:
                    warnings.simplefilter('always');super().fit()
                record={'fit_index':self.fit_count,'reviewed_before_fit':len(self.labels),
                    'n_iter':int(self.model.n_iter_),'max_iter':self.model.max_iter,
                    'temporary_negative_rows':self.last_temporary.tolist(),
                    'warnings':[{'category':w.category.__name__,'message':str(w.message)} for w in messages],
                    'convergence_warning':any(issubclass(w.category,ConvergenceWarning) for w in messages)}
                fit_records.append(record)
                if record['convergence_warning']:raise RuntimeError('Downstream nonconvergence encountered; stop without raising its limit')
        learner=ProbeLearner(X,'fixed_20',11);learner.rng.bit_generator.state=copy.deepcopy(rng.bit_generator.state)
        learner.observe(reviewed,audit['observed_labels'][:prefix]);learner.observe(selected,y[selected])
        learner.fit_count=209;learner.model=converged
        order=reviewed+selected;ends=audit['batch_ends'][:209]+[len(order)]
        while len(order)<len(old_order):
            batch=learner.query(len(old_order)-len(order));learner.observe(batch,y[batch]);order.extend(batch.tolist());ends.append(len(order))
        truth_count=int(next(r['positives'] for r in csv.DictReader((ROOT/'results/runs.csv').open()) if r['topic']=='C15' and r['seed']=='11' and r['policy']=='fixed_20'))
        crossing=int(np.flatnonzero(np.cumsum(y[order])>=math.ceil(.9*truth_count))[0]+1)
        committed=next(end for end in ends if end>=crossing)
        persisted=[r for r in csv.DictReader((ROOT/'phase1_outputs/metrics_by_run.csv').open()) if r['topic']=='C15' and r['seed']=='11' and r['policy']=='fixed_20']
        old_exact=float(next(r['value'] for r in persisted if r['metric']=='effort_at_90'))
        old_committed=float(next(r['value'] for r in persisted if r['metric']=='batch_effort_at_90'))
        report.update(downstream_fits=len(fit_records),downstream_nonconverged_fits=sum(r['convergence_warning'] for r in fit_records),
            complete_row_order_identical=order==old_order,review_positions_changed=sum(a!=b for a,b in zip(order,old_order)),
            effort_at_90=crossing,batch_effort_at_90=committed,original_effort_at_90=old_exact,original_batch_effort_at_90=old_committed,
            isolated_change_in_five_topic_three_seed_mean_contrast=-(committed-old_committed)/15,
            status='COMPLETE')
        _durable.write_text(out/'replayed_trajectory.json', json.dumps({'row_order':order,'batch_ends':ends,'observed_labels':y[order].tolist(),'downstream_fits':fit_records},allow_nan=False)+'\n')
        save();print(json.dumps(report,indent=2),flush=True)
    except BaseException as error:
        report['status']='STOPPED';report['error']=repr(error);save();raise


if __name__=='__main__':main()
