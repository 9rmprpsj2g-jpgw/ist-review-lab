"""Capture a command log durably after full exit, preserving its exit status."""
import argparse
from pathlib import Path
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.durable_io import atomic_file


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('log',type=Path)
    parser.add_argument('command',nargs=argparse.REMAINDER)
    args=parser.parse_args()
    if not args.command:parser.error('command required')
    with atomic_file(args.log,'wb') as stream:
        process=subprocess.Popen(args.command,stdout=stream,stderr=subprocess.STDOUT)
        status=process.wait()
    raise SystemExit(status)


if __name__=='__main__':main()
