"""Package captured evidence after trials; never a writer mitigation or retry."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile
from investigate import HERE, ROOT, STORE, capture_failures, io

DELIVERY = STORE/'delivery'


def verify_archive(path, members):
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise AssertionError('Evidence ZIP CRC failure')
        if sorted(archive.namelist()) != sorted([*members, 'manifest.json']):
            raise AssertionError('Evidence ZIP member mismatch')
        for name, record in members.items():
            data = archive.read(name)
            if len(data) != record['bytes'] or hashlib.sha256(data).hexdigest() != record['sha256']:
                raise AssertionError('Captured evidence changed during packaging')


def main():
    DELIVERY.mkdir(exist_ok=False)
    plan = json.loads((HERE/'plan.json').read_text())
    forensic = json.loads((HERE/'trial_byte_forensics.json').read_text())
    setup = json.loads((HERE/'setup_byte_analysis.json').read_text())
    groups = {}
    seen = set()
    for task in plan['tasks']:
        if task['input_sha256'] in seen:
            continue
        seen.add(task['input_sha256'])
        name = 'reference_full' if task['group'] == 'full' else 'reference_'+task['group']
        groups[name] = [{'file': task['input'], 'sha256': task['input_sha256'], 'bytes': task['input_bytes']}]
    for record in forensic:
        groups.setdefault('failed_'+record['trial'], []).append(record)
    for i, record in enumerate(setup):
        groups['setup_capture_'+str(i)] = [{**record, 'file': str(ROOT/record['file'])}]
    inventory = []
    for name, records in groups.items():
        members = {}
        for r in records:
            path = Path(r['file'])
            if path.stat().st_size != r['bytes'] or io.sha256_file(path) != r['sha256']:
                raise AssertionError('Evidence input differs from existing forensic/reference record')
            key = r['sha256']+'.bin'
            if key not in members:
                members[key] = {'sha256': r['sha256'], 'bytes': r['bytes'], 'original_paths': []}
            members[key]['original_paths'].append(str(path))
        target = DELIVERY/(name+'.zip')
        with io.atomic_file(target, 'w+b', expected_count=len(members)+1,
                            validator=lambda p: verify_archive(p, members)) as stream:
            with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
                archive.writestr('manifest.json', json.dumps({'case': name, 'members': members}, indent=2)+'\n')
                for key, member in members.items():
                    archive.write(member['original_paths'][0], key)
        inventory.append({'archive': str(target), 'bytes': target.stat().st_size,
                          'sha256': io.sha256_file(target), 'members': members})
        print(name, target.stat().st_size, flush=True)
    io.atomic_json(HERE/'evidence_package_manifest.json', {
        'purpose': 'Lossless delivery of already-captured raw evidence. Identical rejected buffers and staged bytes stored once with both original paths. Production/trial writes unchanged.',
        'archives': inventory})


if __name__ == '__main__':
    with capture_failures():
        main()
