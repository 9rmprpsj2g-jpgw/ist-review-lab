"""Run planned independent trials from previously verified immutable I/O references."""
import json
from pathlib import Path
import subprocess
import sys
import traceback
from investigate import HERE,ROOT,STORE,RAM,machine,capture_failures,CAPTURES,io


def main():
    old=json.loads((ROOT/'diagnostics/write_investigation/setup_failure.json').read_text())
    inputs={}
    for entry in old['prepared_size_inputs']:
        path=ROOT/entry['path']
        if io.sha256_file(path)!=entry['sha256'] or path.stat().st_size!=entry['bytes']:raise AssertionError('Reference input integrity mismatch')
        inputs[str(entry['bytes']//2**20)]=path
    manifest=json.loads((ROOT/'audit_manifests/20260907_census_18add1f5ba0e.json').read_text())
    entry=next(e for e in manifest['entries'] if e['filename']=='C12_11_fixed_10.json')
    source=ROOT/'audit_store'/manifest['generation_id']/entry['filename']
    if io.sha256_file(source)!=entry['sha256']:raise AssertionError('Full-audit reference integrity mismatch')
    inputs['full']=source
    tasks=[]
    def add(group,key,method,base,repeats):
        for repeat in range(repeats):
            name=f'{group}_{repeat:02}'
            tasks.append({'name':name,'group':group,'method':method,'input':str(inputs[key]),
                'input_sha256':io.sha256_file(inputs[key]),'input_bytes':inputs[key].stat().st_size,'destination':str(base/name)})
    add('full','full','instrumented',STORE,20)
    for mib in [20,40,60,70,80,100]:add(f'size{mib}',str(mib),'instrumented',STORE,10)
    add('native_overlay','full','native',STORE,5)
    add('plain_overlay','full','plain',STORE,5)
    add('instrumented_tmpfs','full','instrumented',RAM,5)
    mounts=[{'mountpoint':s.split()[4],'filesystem':s.split(' - ')[1].split()[0]} for s in Path('/proc/self/mountinfo').read_text().splitlines() if s.split()[4] in ['/','/workspace','/dev/shm','/tmp']]
    if (HERE/'plan.json').exists():raise ValueError('Never replace a trial plan')
    io.atomic_json(HERE/'plan.json',{'status':'PRESPECIFIED_BEFORE_TRIALS','tasks':tasks,'source_entry':entry,'mounts':mounts,'machine':machine(STORE),
        'design':'95 independent serial trials: 20 full, 10 at each of six sizes, three controls x5. No failed preparation or trial is retried.',
        'reference_provenance':'Previous successful size-input publications, with hashes verified against committed setup_failure.json; full audit verified against original generation manifest.',
        'separate_setup_failure':'80 MiB preparation failed post-publication; captured bytes retained; excluded from predeclared trial denominators.'})
    for task in tasks:
        subprocess.run([sys.executable,str(ROOT/'scripts/capture_command.py'),str(HERE/(task['name']+'.log')),sys.executable,str(HERE/'investigate.py'),'--child',task['name']],check=True,cwd=ROOT)
        receipt=json.loads((HERE/(task['name']+'_receipt.json')).read_text())
        if receipt['status']=='PASS' and io.sha256_file(receipt['output'])!=task['input_sha256']:
            receipt['status']='FAIL_POST_EXIT';receipt['post_exit_sha256']=io.sha256_file(receipt['output'])
            io.atomic_json(HERE/(task['name']+'_post_exit.json'),receipt)
        if 'Investigation input changed' in receipt.get('error',''):raise AssertionError('Input integrity stop')
        print(json.dumps({'trial':task['name'],'status':receipt['status']}),flush=True)
    print('ALL_TRIALS_FINISHED',flush=True)


if __name__=='__main__':
    with capture_failures():
        try:main()
        except BaseException:
            io.atomic_json(HERE/'driver_failure.json',{'traceback':traceback.format_exc(),'captured':CAPTURES})
            raise
