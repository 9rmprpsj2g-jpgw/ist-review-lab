"""Refit original v1 trajectories without changing any solver parameter."""
import csv,hashlib,importlib.util,json,platform,sys,time,warnings
from pathlib import Path
import numpy as np
import scipy,sklearn
from sklearn.exceptions import ConvergenceWarning
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.data import load_collection


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    output=ROOT/'audit_store/v1_ledger_reconstruction'
    if output.exists():raise ValueError('Do not overwrite diagnostic evidence')
    output.mkdir(parents=True)
    report_dir=ROOT/'diagnostics/ledger_reconstruction'
    report={'status':'RUNNING','runs_completed':0,'fits_checked':0,'nonconverged_fits':0,'runs':[],
        'limitations':'Temporary negatives reconstructed from frozen code/RNG, not archived directly. Warnings and n_iter_ are retrospective observations, not contemporaneous v1 logs.'}
    def save():
        (report_dir/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    env=json.loads((ROOT/'results/environment.json').read_text())
    for key,actual in [('python',platform.python_version()),('numpy',np.__version__),('scipy',scipy.__version__),('scikit_learn',sklearn.__version__)]:
        if actual!=env[key]:raise AssertionError(f'Original runtime version mismatch: {key}')
    source=ROOT/'diagnostics/v1_convergence/source/learner_v1.py'
    import subprocess
    if source.read_bytes()!=subprocess.check_output(['git','show','v1-frozen:src/learner.py'],cwd=ROOT):raise AssertionError('Frozen learner source mismatch')
    report['learner_source_sha256']=sha(source)
    spec=importlib.util.spec_from_file_location('v1_learner',source);v1=importlib.util.module_from_spec(spec);spec.loader.exec_module(v1)
    X,ids,topics,info=load_collection()
    if info['sha256']!=env['data_sha256']:raise AssertionError('Original source checksum mismatch')
    report['environment']={k:env[k] for k in ('python','numpy','scipy','scikit_learn')}
    report['source_sha256']=info['sha256']
    rows=list(csv.DictReader((ROOT/'results/runs.csv').open()))
    rows=[r for r in rows if (r['topic'],int(r['seed']),r['policy']) in {('C12',11,'auto_tar'),('C12',47,'auto_tar'),('C16',47,'auto_tar')}]
    original=json.loads((ROOT/'diagnostics/v1_convergence/report.json').read_text())
    started=time.perf_counter()
    current={}
    try:
        for result in rows:
            topic,seed,policy=result['topic'],int(result['seed']),result['policy']
            current={'topic':topic,'seed':seed,'policy':policy}
            path=ROOT/'results/audits'/f'{topic}_{seed}_{policy}.json';audit=json.loads(path.read_text())
            y=np.asarray([topic in t for t in topics],dtype=np.uint8)
            order=audit['row_order'];ends=audit['batch_ends']
            if len(order)!=int(result['reviewed']) or len(set(order))!=len(order):raise AssertionError('Invalid archived order')
            if y[order].tolist()!=audit['observed_labels']:raise AssertionError('Archived label mismatch')
            initial=int(np.random.default_rng(seed).choice(np.flatnonzero(y)))
            if initial!=order[0] or str(ids[initial])!=str(result['seed_doc_id']):raise AssertionError('Seed mismatch')
            state={'round':0,'failed':0,'iterations':[]}
            ledger=output/f'{topic}_{seed}_{policy}.jsonl'
            with ledger.open('w') as log:
                class ObservedLearner(v1.ReviewLearner):
                    def fit(self):
                        with warnings.catch_warnings(record=True) as caught:
                            warnings.simplefilter('always')
                            super().fit()
                        convergence=[str(w.message) for w in caught if issubclass(w.category,ConvergenceWarning)]
                        record={**current,'fit_index':self.fit_count,'round_index':state['round'],
                            'labeled_prefix_end':len(self.labels),'archive_sha256':sha(path),
                            'temporary_negative_rows':self.last_temporary.tolist(),
                            'temporary_negative_document_ids':[str(ids[i]) for i in self.last_temporary],
                            'model_parameters':self.model.get_params(deep=True),
                            'n_iter':int(self.model.n_iter_),'converged':not bool(convergence),
                            'convergence_warnings':convergence,
                            'other_warnings':[{'category':w.category.__name__,'message':str(w.message)} for w in caught if not issubclass(w.category,ConvergenceWarning)]}
                        log.write(json.dumps(record,allow_nan=False)+'\n');log.flush()
                        state['failed']+=int(bool(convergence));state['iterations'].append(record['n_iter'])
                        report['fits_checked']+=1;report['nonconverged_fits']+=int(bool(convergence))
                learner=ObservedLearner(X,policy,seed);learner.observe([initial],[1]);reviewed=1
                for round_index,end in enumerate(ends[1:],start=1):
                    state['round']=round_index
                    selected=learner.query(len(order)-reviewed)
                    expected=order[reviewed:end]
                    if selected.tolist()!=expected:raise AssertionError(f'Archived batch mismatch: {current}, round {round_index}')
                    learner.observe(expected,audit['observed_labels'][reviewed:end]);reviewed=end
                if reviewed!=len(order) or learner.fit_count!=int(result['fits']):raise AssertionError('Incomplete trajectory or fit-count mismatch')
            record={**current,'reviewed':reviewed,'fits':learner.fit_count,'nonconverged_fits':state['failed'],
                    'max_observed_n_iter':max(state['iterations']) if state['iterations'] else None,
                    'trajectory_match':'EXACT','ledger':str(ledger.relative_to(ROOT)),
                    'ledger_sha256':sha(ledger),'ledger_bytes':ledger.stat().st_size}
            expected=next(r for r in original['runs'] if all(r[k]==current[k] for k in current))
            record['expected_sha256']=expected['ledger_sha256']
            record['digest_match']=record['ledger_sha256']==expected['ledger_sha256']
            report['runs'].append(record);report['runs_completed']+=1
            if not record['digest_match']:raise AssertionError('Reconstructed ledger differs from committed expected digest')
            report['seconds_wall']=time.perf_counter()-started;save()
            print(json.dumps(record),flush=True)
    except BaseException as error:
        report['status']='FAILED_CHECK';report['failed_run']=current;report['error']=repr(error);save();raise
    report['status']='COMPLETE';report['seconds_wall']=time.perf_counter()-started;save()
    print(json.dumps({k:v for k,v in report.items() if k!='runs'}),flush=True)


if __name__=='__main__':main()
