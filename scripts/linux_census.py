"""Explicit external-Linux entry point over the unchanged gate/runner checks."""
import argparse
import json
import os
from pathlib import Path
import signal
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.local_runtime import check_environment, paths, stable_identity


def interrupt(signum, frame):
    # Let the existing KeyboardInterrupt path stop workers, wait and publish
    # INTERRUPTED. Ignore subsequent termination signals during that cleanup.
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    signal.signal(signal.SIGUSR1, signal.SIG_IGN)
    raise KeyboardInterrupt(f'External scheduler/operator signal {signum}')


def invoke(module, generation):
    previous = sys.argv
    try:
        sys.argv = [module.__file__, '--generation', generation]
        module.main()
    finally:
        sys.argv = previous


def gates(generation):
    """First allocation runs both gates; later allocations verify, never replace."""
    from scripts import preflight_local, check_local_storage
    audit, output = paths(generation)
    environment = check_environment(generation)
    for name, module in (('preflight.json', preflight_local), ('storage_check.json', check_local_storage)):
        receipt_path = output/name
        if receipt_path.exists():
            receipt = json.loads(receipt_path.read_text())
            identity = stable_identity(receipt) if name == 'preflight.json' else receipt['environment']
            if receipt['status'] != 'PASS' or identity != stable_identity(environment):
                raise AssertionError('Prior gate failed or environment changed; preserve evidence and stop: '+name)
            if name == 'storage_check.json' and (len(receipt['trials']) != 20 or receipt['audit_device'] != audit.stat().st_dev):
                raise AssertionError('Prior storage gate lacks twenty trials on this device')
            print('GATE_REUSED '+name+' (identity checked)', flush=True)
        else:
            if name == 'storage_check.json' and any(audit.glob('storage-check-*')):
                raise RuntimeError('An earlier storage check has no completion receipt; inspect it, no automatic retry')
            invoke(module, generation)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('preflight', 'storage', 'gates', 'run'))
    parser.add_argument('--generation', required=True)
    args = parser.parse_args()
    os.environ['IST_CENSUS_HOST'] = 'external-linux'
    # Shared workers inherit the explicit target; default Mac commands stay Mac-only.
    if args.action == 'gates':
        return gates(args.generation)
    from scripts import preflight_local, check_local_storage, local_census
    module = {'preflight': preflight_local, 'storage': check_local_storage, 'run': local_census}[args.action]
    if args.action != 'run':
        audit, output = paths(args.generation)
        filename = 'preflight.json' if args.action == 'preflight' else 'storage_check.json'
        if (output/filename).exists() or (args.action == 'storage' and any(audit.glob('storage-check-*'))):
            raise RuntimeError('Gate evidence already exists; use gates to validate a PASS, never overwrite or retry')
    else:
        signal.signal(signal.SIGTERM, interrupt)
        signal.signal(signal.SIGUSR1, interrupt)
    invoke(module, args.generation)


if __name__ == '__main__':
    main()