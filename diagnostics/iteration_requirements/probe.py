"""Measure iteration counts for all known capped fits; no production changes."""

import sys as _durable_sys
from pathlib import Path as _DurablePath
_durable_sys.path.insert(0, str(_DurablePath(__file__).resolve().parents[2]))
from src import durable_io as _durable
import hashlib,json,math,sys,warnings
from pathlib import Path
import numpy as np
from sklearn.svm import LinearSVC
from sklearn.exceptions import ConvergenceWarning
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.data import load_collection
from src.learner import ReviewLearner
HERE=Path(__file__).resolve().parent
CEILING=1000000


def main():
    out=ROOT/'audit_store/iteration_requirements'
    if out.exists():raise ValueError('Do not overwrite probe evidence')
    out.mkdir(parents=True)
    X,ids,topics,info=load_collection()
    report={'status':'RUNNING','diagnostic_ceiling':CEILING,'headroom_rule':'ceil(2 * observed_max / 1000) * 1000','fits':[]}
    def save():_durable.write_text(HERE/'report.json', json.dumps(report,indent=2)+'\n')
    def probe(name,rows,labels,negatives,parameters,metadata):
        train=np.asarray(rows+negatives);target=np.asarray(labels+[0]*len(negatives))
        model=LinearSVC(**{**parameters,'max_iter':CEILING})
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always');model.fit(X[train],target)
        bad=any(issubclass(w.category,ConvergenceWarning) for w in caught)
        record={**metadata,'n_iter':int(model.n_iter_),'converged':not bad,
            'diagnostic_ceiling':CEILING,'reviewed':len(rows),'temporary_negatives':len(negatives),
            'original_parameters':parameters,'warnings':[{'category':w.category.__name__,'message':str(w.message)} for w in caught]}
        state={'reviewed_rows':rows,'reviewed_labels':labels,'temporary_negative_rows':negatives,'model_parameters':parameters}
        path=out/f'{name}.json';_durable.write_text(path, json.dumps(state)+'\n')
        record['state_file']=str(path.relative_to(ROOT));record['state_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        report['fits'].append(record);save();print(json.dumps(record),flush=True)
        if bad:raise RuntimeError('Diagnostic ceiling exhausted; no automatic escalation')
    try:
        original_report=json.loads((ROOT/'diagnostics/v1_convergence/report.json').read_text())
        for run in original_report['runs']:
            path=ROOT/run['ledger']
            if hashlib.sha256(path.read_bytes()).hexdigest()!=run['ledger_sha256']:raise AssertionError('v1 ledger integrity failure')
            for line in path.read_text().splitlines():
                fit=json.loads(line)
                if fit['converged']:continue
                audit_path=ROOT/'results/audits'/f'{fit["topic"]}_{fit["seed"]}_{fit["policy"]}.json'
                if hashlib.sha256(audit_path.read_bytes()).hexdigest()!=fit['archive_sha256']:raise AssertionError('v1 audit integrity failure')
                audit=json.loads(audit_path.read_text());n=fit['labeled_prefix_end']
                probe(f'v1_{fit["topic"]}_{fit["seed"]}_{fit["policy"]}_{fit["fit_index"]}',
                      audit['row_order'][:n],audit['observed_labels'][:n],fit['temporary_negative_rows'],fit['model_parameters'],
                      {'generation':'v1','topic':fit['topic'],'seed':fit['seed'],'policy':fit['policy'],'fit_index':fit['fit_index']})
        failed=json.loads((ROOT/'audit_manifests/20260907_census_18add1f5ba0e.json').read_text())
        config=failed['resolved_config'];y=np.asarray(['C15' in t for t in topics],dtype=np.uint8)
        class Located(Exception):pass
        class Locator(ReviewLearner):
            def fit(self):
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter('always');super().fit()
                if any(issubclass(w.category,ConvergenceWarning) for w in caught):raise Located()
        learner=Locator(X,'uncertainty',11,config)
        seed=int(learner.streams['seed_doc'].choice(np.flatnonzero(y)));learner.observe([seed],[1])
        try:
            while len(learner.labels)<config['budget']:
                batch=learner.query(config['budget']-len(learner.labels));learner.observe(batch,y[batch])
        except Located:
            probe('census_C15_11_uncertainty',list(learner.labels),list(learner.labels.values()),
                learner.last_temporary.tolist(),learner.model.get_params(),
                {'generation':'failed_census','topic':'C15','seed':11,'policy':'uncertainty','fit_index':learner.fit_count,
                 'baseline_n_iter':int(learner.model.n_iter_),
                 'reconstruction_limit':'First warning under identical failed-generation config; no saved failure-round state exists for independent comparison.'})
        else:raise AssertionError('Failed census warning did not reproduce')
        maximum=max(f['n_iter'] for f in report['fits']);minimum=min(f['n_iter'] for f in report['fits'])
        report.update(status='COMPLETE',observed_max=maximum,observed_min=minimum,
                      proposed_production_max_iter=math.ceil(2*maximum/1000)*1000)
        save()
    except BaseException as error:
        report.update(status='STOPPED',error=repr(error));save();raise


if __name__=='__main__':main()
