"""Measure iteration counts for all known capped fits; no production changes."""

import sys as _durable_sys
from pathlib import Path as _DurablePath
_durable_sys.path.insert(0, str(_DurablePath(__file__).resolve().parents[2]))
from src import durable_io as _durable
import hashlib,json,math,sys,warnings,subprocess,platform,time
from pathlib import Path
import numpy as np
from sklearn.svm import LinearSVC
from sklearn.exceptions import ConvergenceWarning
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.data import load_collection
from importlib.util import spec_from_file_location, module_from_spec
# Preserve the exact pre-instrumentation census-warning behavior used by this probe.
_spec = spec_from_file_location('src._iteration_frozen_learner', Path(__file__).with_name('frozen_learner.py'))
_module = module_from_spec(_spec)
_spec.loader.exec_module(_module)
ReviewLearner = _module.ReviewLearner
HERE=Path(__file__).resolve().parent
CEILING=1000000


def main():
    out=ROOT/'audit_store/iteration_requirements_v2'
    if out.exists():raise ValueError('Do not overwrite probe evidence')
    out.mkdir(parents=True)
    import scipy,sklearn
    env=json.loads(subprocess.check_output(['git','show','phase3c-complete:results/environment.json'],cwd=ROOT))
    for key,actual in [('python',platform.python_version()),('numpy',np.__version__),('scipy',scipy.__version__),('scikit_learn',sklearn.__version__)]:
        if actual!=env[key]:raise AssertionError('Runtime mismatch: '+key)
    X,ids,topics,info=load_collection()
    if info['sha256']!=env['data_sha256']:raise AssertionError('Source integrity failure')
    report={'status':'RUNNING','diagnostic_ceiling':CEILING,'headroom_rule':'ceil(2 * observed_max / 1000) * 1000','fits':[],'environment':{k:env[k] for k in ['python','numpy','scipy','scikit_learn']},'source_sha256':info['sha256']}
    def save():_durable.write_text(HERE/'report.json', json.dumps(report,indent=2)+'\n')
    def probe(name,rows,labels,negatives,parameters,metadata):
        train=np.asarray(rows+negatives);target=np.asarray(labels+[0]*len(negatives))
        model=LinearSVC(**{**parameters,'max_iter':CEILING})
        started=time.perf_counter()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always');model.fit(X[train],target)
        elapsed=time.perf_counter()-started
        bad=any(issubclass(w.category,ConvergenceWarning) for w in caught)
        record={**metadata,'fit_seconds':elapsed,'n_iter':int(model.n_iter_),'converged':not bad,
            'diagnostic_ceiling':CEILING,'reviewed':len(rows),'temporary_negatives':len(negatives),
            'original_parameters':parameters,'warnings':[{'category':w.category.__name__,'message':str(w.message)} for w in caught]}
        state={'reviewed_rows':rows,'reviewed_labels':labels,'temporary_negative_rows':negatives,'model_parameters':parameters}
        path=out/f'{name}.json';_durable.write_text(path, json.dumps(state)+'\n')
        record['state_file']=str(path.relative_to(ROOT));record['state_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
        report['fits'].append(record);save();print(json.dumps(record),flush=True)
        if bad:raise RuntimeError('Diagnostic ceiling exhausted; no automatic escalation')
    try:
        original_report=json.loads(subprocess.check_output(['git','show','phase3c-complete:diagnostics/v1_convergence/report.json'],cwd=ROOT))
        verified=json.loads(subprocess.check_output(['git','show','phase3c-complete:phase3c_outputs/verified_ledger_inventory.json'],cwd=ROOT))
        paths={r['run']:r['ledger'] for r in verified['entries']}
        for run in original_report['runs']:
            path=ROOT/paths[f"{run['topic']}_{run['seed']}_{run['policy']}"]
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
        from src.census import feature_digest
        if feature_digest(X,ids)!=failed['feature_matrix_sha256']:raise AssertionError('Census feature matrix integrity failure')
        config=failed['resolved_config'];y=np.asarray(['C15' in t for t in topics],dtype=np.uint8)
        locator_records=[]
        class Located(Exception):pass
        class Locator(ReviewLearner):
            def fit(self):
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter('always');super().fit()
                locator_records.append({'fit_index':self.fit_count,'reviewed':len(self.labels),'n_iter':int(self.model.n_iter_),'warnings':[{'category':w.category.__name__,'message':str(w.message)} for w in caught]})
                print(json.dumps({'locator_fit':self.fit_count,'n_iter':int(self.model.n_iter_),'reviewed':len(self.labels),'warnings':locator_records[-1]['warnings']}),flush=True)
                if any(issubclass(w.category,ConvergenceWarning) for w in caught):raise Located()
        learner=Locator(X,'uncertainty',11,config)
        seed=int(learner.streams['seed_doc'].choice(np.flatnonzero(y)));learner.observe([seed],[1])
        try:
            while len(learner.labels)<config['budget']:
                batch=learner.query(config['budget']-len(learner.labels));learner.observe(batch,y[batch])
        except Located:
            _durable.atomic_json(HERE/'census_locator.json',locator_records)
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
