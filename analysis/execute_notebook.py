"""Authorized socket-free fallback; two isolated executions and exact comparison."""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import traceback
import uuid

import nbformat
from src.durable_io import write_notebook
from analysis.artifact_io import atomic_copy, atomic_file, validate_artifacts, cleanup_temporary_files
from analysis.review_report import write_report

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "phase1_outputs"
NOTEBOOK = ROOT / "notebooks/01_results.ipynb"


def check_inputs():
    hashes = json.loads((OUT / "input_fingerprints.json").read_text())
    renames = json.loads((OUT / "authorized_input_renames.json").read_text())
    for name, digest in hashes.items():
        if hashlib.sha256((ROOT / renames.get(name, name)).read_bytes()).hexdigest() != digest:
            raise RuntimeError(f"Protected input changed: {name}")
    return len(hashes)


def worker(destination):
    from IPython.core.interactiveshell import InteractiveShell
    from IPython.utils.capture import capture_output

    check_inputs()
    os.chdir(ROOT)
    destination.mkdir(parents=True, exist_ok=False)
    notebook = nbformat.read(NOTEBOOK, as_version=4)
    nbformat.validate(notebook)
    for cell in notebook.cells:
        if cell.cell_type == "code":
            cell.outputs = []
            cell.execution_count = None
            cell.metadata.pop("execution", None)
    # A newly allocated namespace per worker, never a prior run's globals.
    namespace = {"__name__": "__main__", "PHASE1_OUTPUT_DIR": str(destination)}
    InteractiveShell.instance()  # Rich display capture, without starting a kernel.
    count = 0
    for index, cell in enumerate(notebook.cells):
        if cell.cell_type != "code":
            continue
        count += 1
        cell.execution_count = count
        failure = None
        with capture_output(stdout=True, stderr=True, display=True) as captured:
            try:
                exec(compile(cell.source, f"01_results.ipynb:cell-{index}", "exec"), namespace)
            except Exception as exc:
                failure = exc
                trace = traceback.format_exc().splitlines()
        if captured.stdout:
            cell.outputs.append(nbformat.v4.new_output("stream", name="stdout", text=captured.stdout))
        if captured.stderr:
            cell.outputs.append(nbformat.v4.new_output("stream", name="stderr", text=captured.stderr))
        for output in captured.outputs:
            cell.outputs.append(nbformat.v4.new_output("display_data", data=output.data,
                                                       metadata=output.metadata))
        if failure is not None:
            cell.outputs.append(nbformat.v4.new_output("error", ename=type(failure).__name__,
                                                       evalue=str(failure), traceback=trace))
            write_notebook(notebook, destination / "executed_notebook.ipynb")
            raise failure
        print(f"Completed code cell {count}", flush=True)
    check_inputs()
    nbformat.validate(notebook)
    write_notebook(notebook, destination / "executed_notebook.ipynb")


def inventory(directory):
    return {str(p.relative_to(directory)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(directory.rglob("*")) if p.is_file() and not p.name.startswith(".writing-")}


def main():
    check_inputs()
    resume = len(sys.argv) == 3 and sys.argv[1] == "--resume"
    session = Path(sys.argv[2]).resolve() if resume else OUT / "reproducibility" / uuid.uuid4().hex
    session.mkdir(parents=True, exist_ok=resume)
    receipt = {
        "status": "RUNNING", "execution_method": "Python compile/exec of sequential code cells in one fresh namespace per run; separate fresh Python subprocess per run; IPython capture_output for stdout/stderr and rich display; nbformat for stored notebook outputs",
        "libraries": {x: importlib.metadata.version(x) for x in ("nbformat", "IPython", "nbclient", "ipykernel", "Pillow", "PyMuPDF")},
        "python": sys.version, "fresh_namespace": True, "fresh_process_per_run": True,
        "nbclient_used": False,
        "fallback_reason": "Installed InProcessKernelManager is not a drop-in nbclient lifecycle implementation (shutdown_kernel(now=...) / cleanup_resources); in-process ipykernel also initializes ZeroMQ IOPub machinery. No socket-free nbclient configuration was established; user explicitly authorized fresh-namespace fallback.",
        "network_transport_unavailable_reason": "Prior normal Jupyter kernel startup failed before the first cell: ZeroMQ Operation not permitted (src/ip_resolver.cpp:542); Kernel died before replying to kernel_info. No new network transport attempt was made.",
        "comparison": "Final user gate: exact bytes for all CSV, JSON, Markdown, HTML and executed notebooks (including gzip CSV); all figures complete and decodable; protected digests unchanged. Figure identity and size are not gates; differences are warnings.",
        "warnings": [],
        "resumed_existing_first_execution": resume,
        "reproducibility_directory": str(session.relative_to(ROOT)),
        "scope": "Phase 1 only; archived consistency, not independent external ground-truth verification"
    }
    receipt_path = OUT / "notebook_execution.json"
    if receipt_path.exists():
        atomic_copy(receipt_path, session / ("previous_execution_record_"+uuid.uuid4().hex+".json"))
    try:
        completeness = {}
        for name in ("run1", "run2"):
            if not (resume and name == "run1"):
                print(f"Starting {name} in a fresh subprocess", flush=True)
                subprocess.run([sys.executable, "-m", "analysis.execute_notebook", "--worker", str(session / name)],
                               cwd=ROOT, check=True, env={**os.environ, "PYTHONHASHSEED": "0"})
            # subprocess.run waits for full exit; no validation or hashing before it.
            removed = cleanup_temporary_files(session / name)
            receipt["warnings"].extend({"run":name, "temporary_litter_removed":x} for x in removed)
            write_report(session / name)
            receipt["warnings"].extend({"run":name, "temporary_litter_removed":x}
                                       for x in cleanup_temporary_files(session / name))
            completeness[name] = validate_artifacts(session / name)
            with atomic_file(session / f"{name}_completeness.json", "w") as handle:
                json.dump(completeness[name], handle, indent=2)
        first, second = inventory(session / "run1"), inventory(session / "run2")
        differences, criteria = [], {}
        for name in sorted(first.keys() | second.keys()):
            if name not in first or name not in second:
                differences.append(name)
                continue
            a, b = session / "run1" / name, session / "run2" / name
            figure = a.suffix in (".png", ".svg", ".pdf")
            criteria[name] = "completeness_only" if figure else "exact_bytes"
            if figure and first[name] != second[name]:
                receipt["warnings"].append({"figure_differs":name})
            equal = figure or first[name] == second[name]
            if not equal:
                differences.append(name)
        with atomic_file(session / "comparison.json", "w") as handle:
            json.dump({"run1":first, "run2":second, "criteria":criteria,
                       "different_files":differences}, handle, indent=2)
        if differences:
            raise RuntimeError("Repeatability FAILURE; differing files: " + repr(differences))
        receipt.update(status="PASSED", runs_completed=2, agreeing_files=len(first),
                       byte_identical_files=sum(first[n] == second[n] for n in first),
                       completeness_checks="PASSED for both runs",
                       different_files=[], timestamps_ignored=False, protected_files_unchanged=check_inputs())
        for name in second:
            source = session / "run2" / name
            target = NOTEBOOK if name == "executed_notebook.ipynb" else OUT / name
            target.parent.mkdir(parents=True, exist_ok=True)
            atomic_copy(source, target)
            if name == "RESULTS.md":
                atomic_copy(source, ROOT / "RESULTS.md")
        atomic_copy(session / "run2/review_results.md", ROOT / "RESULTS.md")
        atomic_copy(session / "run2/review_results.md", OUT / "RESULTS.md")
        validate_artifacts(session / "run2")
        executed = nbformat.read(NOTEBOOK, as_version=4)
        receipt["execution_counts"] = [c.execution_count for c in executed.cells if c.cell_type == "code"]
        receipt["stored_outputs"] = sum(len(c.outputs) for c in executed.cells if c.cell_type == "code")
        receipt["notebook_sha256"] = second["executed_notebook.ipynb"]
    except Exception as exc:
        receipt.update(status="FAILED", error=str(exc))
        raise
    finally:
        with atomic_file(receipt_path, "w") as handle:
            handle.write(json.dumps(receipt, indent=2)+"\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        worker(Path(sys.argv[2]))
    else:
        main()
