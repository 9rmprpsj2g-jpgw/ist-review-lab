# Large-write investigation — 8 September 2026

**Investigation completed; census remains blocked.** The unchanged durable helper failed in 6/20 full-audit trials. Every preserved failed payload is an exact prefix of its successful reference: tail loss, not observed mid-stream substitution or a gap. Missing fsync is not a sufficient explanation. The responsible filesystem/runtime layer or external actor is **not conclusively identified**; this is not a claim of a generic Linux overlayfs bug.

## Changes and protocol

Converted both diagnostic resource.getrlimit results to lists before JSON serialization. Strict decoded-value equality is unchanged. Extended diagnostic failure capture to setup and child execution: hard-link files before the existing cleanup removes their names, and retain the exact JSONDecodeError input buffer separately when available. The helper, all its checks, original plans, results and model code are unchanged. Failure capture does not suppress an exception or replace a failed result with a success.

The first new setup failed preparing 80 MiB after publication. Its failed file is preserved. That preparation was not retried: the trial driver used previously successful size inputs, checked against digests already committed in the earlier setup receipt. The original full audit is checked against the unchanged generation manifest. The new plan was written before its 95 trials; setup failure is reported separately rather than silently included or excluded after looking at rates.

Each trial used a fresh child process, unique destination directory and mkstemp path; the parent waited for complete subprocess exit before its independent final hash. No model was fit. Instrumented trials use the original benchmark wrapper; native controls remove it. All retained PASS outputs were read again after the series. Failures were measured endpoints explicitly authorized by the user, never retries. No writer was chunked, streamed differently, relaxed or replaced in production.

## Failure rates

| Group | Intended MiB | Failures / trials | Observed rate |
|---|---:|---:|---:|
| full | 83.716 | 6/20 | 30% |
| size20 | 20.000 | 0/10 | 0% |
| size40 | 40.000 | 0/10 | 0% |
| size60 | 60.000 | 0/10 | 0% |
| size70 | 70.000 | 1/10 | 10% |
| size80 | 80.000 | 3/10 | 30% |
| size100 | 100.000 | 2/10 | 20% |
| native_overlay | 83.716 | 1/5 | 20% |
| plain_overlay | 83.716 | 0/5 | 0% |
| instrumented_tmpfs | 83.716 | 0/5 | 0% |

The 95-trial series has 13 failures. Full size is exactly 87,782,855 bytes (2,315 fits, 23,149 reviews), taken from the retained fixed_10 census audit. The six size inputs are diagnostic copies: real round prefixes plus padding; 100 MiB contains the full audit plus padding. They vary serialized size, not just genuine round count. Sizes were tested sequentially, so time and accumulating cache pressure are confounded with size.

The smallest failing tested size is **70 MiB**. There is **no established hard threshold**: 70 MiB usually succeeded, failures were not monotonic, and ten successes at a smaller size cannot certify reliability. Truncated trial lengths range from 66,534,298 to 71,306,191 bytes. The size association is evidence for this operation in this environment, not a universal cutoff.

Ten separately planned, later application-instrumented native overlay trials also completed: **0/10 failures**, all write counters reported 87,782,855 characters accepted, zero short writes, and post-exit reference hashes matched. Instrumentation changes timing; these successes do not explain the thirteen failures or replace their denominator. Five syscall-traced controls were planned, but ptrace was denied before the first child ran: **zero traced trials executed**. No escalation or bypass was attempted.

## Captured bytes and first divergence

All 13 trial failed files and all 12 available rejected parser buffers are exact prefixes. Each first divergence is the failed file's EOF, with all earlier bytes identical. No observed gap or corrupted middle bytes. The non-parser failure was a final size/hash mismatch, so there was no parser buffer to retain.

| Trial | Captured bytes | Missing tail bytes | First difference, zero-based |
|---|---:|---:|---:|
| full_03 | 66,649,114 | 21,133,741 | 66,649,114 (EOF) |
| full_08 | 68,100,439 | 19,682,416 | 68,100,439 (EOF) |
| full_09 | 69,272,862 | 18,509,993 | 69,272,862 (EOF) |
| full_10 | 67,961,053 | 19,821,802 | 67,961,053 (EOF) |
| full_11 | 67,477,272 | 20,305,583 | 67,477,272 (EOF) |
| full_19 | 69,977,969 | 17,804,886 | 69,977,969 (EOF) |
| size70_05 | 68,338,194 | 5,062,126 | 68,338,194 (EOF) |
| size80_02 | 68,895,717 | 14,990,363 | 68,895,717 (EOF) |
| size80_08 | 70,363,304 | 13,522,776 | 70,363,304 (EOF) |
| size80_09 | 66,534,298 | 17,351,782 | 66,534,298 (EOF) |
| size100_03 | 71,306,191 | 33,551,409 | 71,306,191 (EOF) |
| size100_07 | 69,445,047 | 35,412,553 | 69,445,047 (EOF) |
| native_overlay_00 | 67,903,655 | 19,879,200 | 67,903,655 (EOF) |

Representative full_03 has SHA-256 `43e9591d8c8d0f4cc1a310ff687a99419f27a279e51cdd4b51991238136938c3`; its retained file and rejected parser buffer are identical. The complete full-audit reference has SHA-256 `47b73e2cc08173ae906c6a7556193e43aa5987af31c0904f58d24046f3cbcedf`. It was successfully written by other trials, matches the original committed digest, and is 87,782,855 bytes long.

At requested zero-based offset **70,109,136**, the complete full-audit reference contains comma `,` (hex `2c`, decimal 44). The preceding 48 characters are `0928435, -1.636483778592468, -1.6362939387274635`; the following 48 are ` -1.6286461779537718, -1.6525248279426548, -1.65`. That offset is **past EOF in every captured failed full-audit trial**: no byte exists there. The original benchmark's failed temporary was deleted before capture was added, so its particular byte cannot be recovered or asserted identical. Full per-file ASCII/hex contexts, digests and offsets are in `trial_byte_forensics.json`; size-input contexts differ from the full reference where their content differs.

The separate setup 80 MiB failure retained 69,953,367 bytes, an exact prefix missing 13,932,713 bytes. Setup cleanup also exposed a 34,459,735-byte prefix of the 40 MiB input, plus complete 60/70 MiB scratch files; these are recorded in `setup_byte_analysis.json`. The 40 MiB final input itself was complete. They are preserved cleanup observations, not additional failed trials.

## Where the checks caught the problem

Of the 13 trial failures, one (size100_03) occurred at staged full-value verification, after the earlier staged parse/count had returned. Twelve occurred after staged full-value verification and replacement: size70_05 at the final size/hash check, the other eleven during the subsequent final parse after the immediately preceding size/hash comparison had passed. This follows directly from the unchanged helper's control flow and captured tracebacks; it is not inferred from a successful exit. The separate setup failure also occurred at final parse.

Thus the premise that this guard always failed before replace is incorrect. Detected invalid final files were removed by the unchanged cleanup, with evidence hard-linked first. A complete read followed by a truncated read is the key observation. JSON serialization cannot, by itself, explain why a full-value check succeeds and a later read loses its suffix with no project write to that path between them.

Some API success records additionally show the source temporary absent immediately after rename, yet present under a different inode during cleanup. These observations do not establish who recreated it; they reinforce the need for filesystem/runtime visibility investigation. Application records are not kernel tracing.

## Candidate causes: evidence and limits

| Candidate | Evidence | Assessment |
|---|---|---|
| Disk exhaustion at staging path | Every failing trial's before/after snapshots retained many GiB of available space; first full failure began with 28,192,288,768 bytes available. No ENOSPC or inode exhaustion recorded. | No evidence of exhaustion; cannot exclude an unobserved transient external event between snapshots. |
| Per-file/process size limit | RLIMIT_FSIZE and RLIMIT_AS were both unlimited; same 100 MiB payload succeeded in 8/10 trials. No EFBIG, SIGXFSZ or MemoryError. | A fixed limit at approximately 70 MB is contradicted. |
| Sandbox filesystem / runtime visibility | Stage validation succeeded before twelve later failures; actual retained files are shorter, not merely parser-buffer artifacts. Native overlay failed 1/5; tmpfs 0/5. | Environment/persistence behavior is a leading explanation. Small control samples and denied syscall tracing prevent naming a proven layer or excluding an external mutator. Census here is not cleared. |
| json.dump buffering versus timing wrapper | Native unwrapped helper also failed. Benchmark wrapper only measures calls and yields the original stream. Complete staged-value checks preceded most losses. Later API controls accepted every character without short writes, but all passed. | Timing wrapper is not necessary for failure. Serialization/buffering alone is inconsistent with the post-validation losses; precise interaction remains unproven. Plain comparator 0/5 is not proof of a fix. |
| Multiprocessing/concurrent same-path writer | Each child ran serially, parent waited, destinations and temporaries were unique. Helper closes the serializer before validation. Capture hook links/deletes only during cleanup. | Concurrent project trial writers to the same path excluded by execution design; unrelated platform/external mutation cannot be excluded. |
| Memory pressure during serialization | Largest trial process peak RSS 961,452 KiB (about 939 MiB), no OOM or OOM-kill events. First full failure occurred at about 4.4 GiB cgroup usage with all memory-event counters zero. Later retained outputs drove cgroup usage near its 14 GiB ceiling and memory.max event counts rose. | OOM and sustained cgroup ceiling pressure are not necessary causes. Later trials did experience memory reclaim pressure; do not claim all memory pressure was ruled out or infer that RSS measures total cgroup use. |

No exact historical root cause is proved. Earlier ledger failures were approximately 99 KB and a truncated Phase 1 PNG was below 1 MB, so the proposed claim that all previous failures were above 70 MB is false. A size association here cannot by itself unify those incidents.

## Could an already-published artifact be wrong?

**Yes, a past successful verification cannot guarantee that storage remains correct later.** These trials demonstrate full checks followed by later suffix loss inside the same operation. All thirteen target failures were detected before the helper returned success; no false PASS was observed among the 82 successful primary trials or ten later API controls, including post-exit rechecks. That does not establish an enduring guarantee after the last read.

Current comparisons against unchanged trusted references found no mismatch: 125 original results/plan files, 38 completed audits from the failed generation, all 105 verified original/recovered v1 ledgers, and 88 retained artifacts from the passed Phase 1 comparison. Separately, all 408 phase3c-complete tracked-file contents matched their Git blob hashes, excluding the authorized CHANGES.md log append. Categories overlap and are not an independent sample count. Intentionally omitted regenerable figures/tables are not silently replaced. Historical superseded deficient ledgers remain deficient in their original locations, as recorded in their recovery history.

These checks support the currently retained bytes, not correctness of an originally wrong in-memory result or of files outside the checked inventories. No expected digest was recomputed to make a regenerated result pass.

## Gate and deliverables

All investigation logs were read in full; `log_inspection.json` records their hashes and error/warning lines. Thirteen trial failures, one setup failure and the denied tracing attempt remain explicit. No convergence warnings were generated because no model fits ran. No test assertion or production verification condition changed. This is an investigation completion, **not a passed storage reliability gate**.

Raw failed files are retained outside Git. Transfer archives group evidence by failed trial/setup capture and share successful reference inputs separately; this is delivery packaging after the investigation, not a chunked write workaround or a changed test. Their manifest maps raw members to observed digests and original paths. Model probes, census, production parameter changes and Phase 4 remain unperformed and blocked. Recommended next diagnostic location is the user's machine with the same unchanged verifier and references; no relocation or run is initiated here.
