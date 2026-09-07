"""Create the approved 60 independently extractable ZIP transfer packages."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import zipfile
from .census_io import atomic_json,sha256_file
from .data import ROOT


def main():
    parser=argparse.ArgumentParser();parser.add_argument('generation_id');args=parser.parse_args()
    source=ROOT/'audit_store'/args.generation_id
    manifest_path=ROOT/'audit_manifests'/f'{args.generation_id}.json'
    manifest=json.loads(manifest_path.read_text())
    if manifest['status']!='COMPLETE' or manifest['completed']!=len(manifest['expected_grid']):
        raise ValueError('Cannot package an incomplete generation')
    groups=defaultdict(list)
    for entry in manifest['entries']:groups[(entry['policy'],entry['topic'])].append(entry)
    expected={(run['policy'],run['topic']) for run in manifest['expected_grid']}
    if set(groups)!=expected:raise AssertionError('Package coverage mismatch')
    destination=ROOT/'transfer_packages'/args.generation_id
    destination.mkdir(parents=True,exist_ok=True)
    index=dict(generation_id=args.generation_id,status='PACKAGED_NOT_YET_DELIVERED',
               extraction='Extract all independent ZIPs into the same directory. Run python3 verify_audits.py audit_manifests/'+args.generation_id+'.json',
               archives=[])
    for (policy,topic),entries in sorted(groups.items()):
        name=f'{args.generation_id}_{policy}_{topic}.zip';path=destination/name
        if path.exists():raise ValueError('Refusing to overwrite a transfer archive')
        for entry in entries:
            audit=source/entry['filename']
            if audit.stat().st_size!=entry['byte_size'] or sha256_file(audit)!=entry['sha256']:
                raise AssertionError('Audit changed before packaging')
        with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as archive:
            for entry in sorted(entries,key=lambda e:e['seed']):
                archive.write(source/entry['filename'],f'audit_store/{args.generation_id}/{entry["filename"]}')
            archive.write(manifest_path,f'audit_manifests/{args.generation_id}.json')
            archive.write(ROOT/'scripts/verify_audits.py','verify_audits.py')
        # Validate compressed data/CRC only after archive close.
        with zipfile.ZipFile(path) as archive:
            bad=archive.testzip()
            if bad is not None:raise AssertionError(f'Corrupt ZIP member: {bad}')
        item=dict(filename=name,byte_size=path.stat().st_size,sha256=sha256_file(path),
                  policy=policy,topic=topic,seeds=sorted(e['seed'] for e in entries),
                  audit_filenames=[e['filename'] for e in entries])
        index['archives'].append(item)
        print(json.dumps(item),flush=True)
    atomic_json(destination/'transfer_index.json',index)
    # Repo keeps checksums/provenance, never archive bytes.
    manifest['archive_status']='PACKAGED_NOT_YET_DELIVERED';manifest['archives']=index['archives']
    atomic_json(manifest_path,manifest)
    atomic_json(ROOT/'phase3b_outputs'/args.generation_id/'transfer_index.json',index)


if __name__=='__main__':main()
