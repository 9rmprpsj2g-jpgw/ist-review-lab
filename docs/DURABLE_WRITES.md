# Phase 3C: durable artifact publication

One implementation, `src/durable_io.py`, owns publication. `src/census_io.py` and `analysis/artifact_io.py` re-export it for compatibility. A temporary file in the destination directory is serialized, flushed, fsynced, closed, parsed and counted before atomic replace. The containing directory is fsynced on supported POSIX filesystems. Final-path bytes are reopened, hashed, parsed, counted and validated; a second final-path hash must agree. The producer's returned digest comes from the final file, not a memory buffer. Expected committed digests are compared verbatim and never rewritten.

Byte counts also compare the completed stream position against its synced file size. JSON value equality verifies every intended field/list element; CSV and JSONL callers provide expected record counts, and ZIP writers provide expected member counts. Copying binds the target to the source disk digest/count. Census workers return their final-path digest and the parent compares it against its independently validated audit digest. Existing census order, boundary, margin and fit completeness assertions remain in force.

An exception before publication preserves the old complete destination or leaves no destination. Detected post-publication corruption raises and removes the invalid new destination. A hard-killed process may leave an unpublished `.writing-*` temporary file; it cannot expose that temporary as the final artifact. One writer per destination is required. Atomic replace and fsync cannot guarantee correct behavior from a filesystem that violates their contracts, or prevent a later external modification. Parent post-exit checks and immutable reference digests remain necessary.

## Writer inventory

| Writer | Artifacts and durable route |
|---|---|
| `src/experiment.py` | Audits via atomic_json with full value verification; resolved config, actual parameters and environment via write_text; results table via write_csv. |
| `src/census.py` | Incremental/final manifests via atomic_json; result table via write_csv; compares worker/parent final audit hashes. |
| `src/census_io.py` | Compatibility imports only; no separate writer implementation. |
| `src/monitor_census.py` | Log through atomic_file after child wait; resource receipt via atomic_json. Live log is a scratch file until child exit. |
| `src/package_audits.py` | ZIP stream under atomic_file, expected members = audits + manifest + verifier; CRC check; manifests/index through atomic_json. |
| `src/data.py` | Download through write_bytes with existing source digest when available and 23,149 decoded records; source lock through write_text. |
| `src/bdr_queue.py` | CSV and metadata through write_csv/write_text. |
| `src/summarize.py` | CSVs through write_csv, figures through save_figure, Markdown through write_text. Historical results destinations remain; this legacy command is not authorized for execution. |
| `src/build_report.py` | ReportLab writes to an atomic_file stream; final PDF decodability verified. Not executed. |
| `src/verify_results.py`, `src/replay.py` | JSON receipts through write_text; legacy results destinations remain and were not invoked. |
| `analysis/artifact_io.py` | Shared atomic_file; atomic_copy verifies source disk digest/count. |
| `analysis/execute_notebook.py` | Executed notebooks through write_notebook; receipts/comparisons through shared atomic_file; copies through atomic_copy. |
| `analysis/phase1a.py` | CSV streams with expected frame row counts; receipt/copies through shared helper. |
| `analysis/review_report.py` | Existing atomic_file Markdown stream now resolves to the shared helper. |
| `notebooks/01_results.ipynb` | CSV row counts, gzip CSV, JSON, HTML, Markdown and figure streams route through shared helper. Source edited only; stored historical outputs explicitly labeled, no new notebook execution. |
| `scripts/observe_census_rss.py` | Incremental/final resource JSON through write_text. |
| `scripts/capture_command.py` | New wrapper for durable combined stdout/stderr logs; waits for full child exit, then publishes, preserving child exit status. |
| `diagnostics/v1_convergence/check.py`, `diagnostics/ledger_reconstruction/reconstruct.py` | JSONL streams with archived expected fit counts; reports through write_text. Previous ledgers/reports are not overwritten. |
| `diagnostics/v1_convergence/summarize.py` | Findings JSON and CSV with expected failure record count. Not executed. |
| `diagnostics/fit209_sensitivity/check.py` | Report/replay JSON through write_text; NPZ atomic stream with three expected array members. Not executed. |
| `diagnostics/iteration_requirements/probe.py` | State/report JSON through write_text. Not executed; prior integrity stop preserved. |
| `diagnostics/durable_reconstruction/reconstruct.py` | One C12/11 reconstruction; 47-record expectation and committed SHA-256 enforced before publication and independently after exit. |
| `phase3_outputs/estimate_audit_size.py`, `phase3b_preflight/estimate.py`, `phase3b_outputs/estimate_storage.py` | Estimate JSON through write_text. Not executed. |

No active project-owned artifact serializer is intentionally left on a separate write implementation. Formats without a formal record schema (Markdown, plain text, logs, HTML) are UTF-8 decoded and checked against staged line/byte counts; write_text also verifies full intended bytes. This does not prove that an external child emitted every message it should have emitted. PNG/SVG/PDF use decoding/parsing rather than scientific record counts. Opaque bytes use size/digest checks. Large JSON verification temporarily allocates another decoded audit; extra I/O and memory are not benchmarked here and must be accounted for before census resumes.

Exceptions: immutable `results/`, historical executed notebooks under `phase1_outputs/reproducibility/`, prior receipts and the extracted frozen learner remain unchanged. Historical notebook source embedded in those evidence copies is not a live writer to migrate. Git/editor operations and dependency-managed caches are outside the application artifact writer; stdout/stderr redirection by an external shell cannot be intercepted by this helper, so future recorded runs must use capture_command or monitor_census. Test-only raw writes intentionally inject corruption. No legacy analysis command was executed.

## Verification and reconstruction

Twenty unit tests pass, including six publication contracts: killed/unflushed child, valid JSONL with only 41 of 47 records, fsync failure with old destination preservation, post-replace corruption rejection/removal, complete 47-record publication with independent child digest, and CSV/gzip/JSON roundtrips. Original scientific assertions, tolerances and expected digests are unchanged.

C12/11 produced 47 records / 99,218 bytes. Producer and independent post-exit digest both equal the original committed value:

`038cb83c785ae7a2abe366668eae61925f22b615389763db693344369ba1a23c`

All 47 fits converged (maximum n_iter 2,920), including the missing six. All 105 ledgers are now verified through the explicit original/recovered path inventory: 5,880 records, eight known non-converged fits, zero unknown statuses. The earlier deficient ledgers and contradictory receipts remain intact as diagnostic history. The restored ledgers reside outside git; the inventory records where to obtain verified bytes without changing any original expectation.

The repaired path resolves the observed retention failure for this reconstruction. Earlier truncation is consistent with a deficient publication path, but this experiment does not identify why precisely three files lost tails or prove a particular filesystem failure mechanism. No generator loss was observed under the repaired path. Previously, census JSON already used file fsync and replace; its missing protections were directory fsync, full post-write value verification and producer-versus-parent digest comparison. The ledger writer had bypassed it entirely.

Full unit-test and reconstruction logs and all per-fit captured warning arrays were inspected. No new fit warnings occurred. The verified inventory retains all eight historical C15 warnings. One editing invocation initially used a Python interpreter without nbformat: notebook publication failed before replace, leaving the old notebook intact; the edit was completed in the existing notebook environment without changing a validation rule. No scientific assertion or integrity check failed in Phase 3C.

No max-iteration probes, census rerun, Phase 4 analysis or new solver setting. Stop at Phase 3C review.
