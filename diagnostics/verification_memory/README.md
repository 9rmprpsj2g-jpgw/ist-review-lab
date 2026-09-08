# Verification-memory benchmark: stopped on integrity failure

The actual largest retained fixed_10 census audit was used: C12/11, 23,149 reviews, 2,315 fits, 2,265,300 retained margin entries, 87,782,855 bytes (83.716 MiB). Its committed failed-generation manifest digest matches before and after the benchmark. It uses batch_plus_100_min_1000_plus_selected; fixed-10 resolves max(1000,10+100) to 1,000 until the candidate pool shrinks. This is a completed audit from the failed generation, used only as benchmark input, not reused as a new census result.

Actual quarter/half trajectory prefixes provide the size sweep. Each measurement ran in a fresh Python process holding the real feature matrix and decoded audit. No model fit was run. Instrumentation wraps the unchanged shared helper's operations; all existing parse/count/value/digest checks remain active. JSON-loaded audits do not preserve the producer's shared string references, so this is a conservative representation of the producer's live audit, not a measurement of a complete training worker. The resident feature matrix occupies 20,961,836 bytes. Filesystem cache was warm; no cold-disk throughput claim is made.

| Audit size (MiB) | Rounds | Successful repetitions | Peak RSS during verification (MiB) | Verification wall time (s) |
|---:|---:|---:|---:|---:|
| 21.355 | 578 | 2 | 382.75–382.77 | 1.137–1.160 |
| 42.735 | 1,157 | 2 | 535.16–536.81 | 2.600–2.616 |
| 83.716 | 2,315 | 1 of 2 attempted | 889.52 | 5.614 |

Verification time sums parse/count, full-value comparison and on-disk hash operations. The full audit took 5.618 s after serialization including flush/fsync/rename and 8.401 s for writing plus verification. RSS before verification was 487.73 MiB; peak increased to 889.52 MiB, about 401.79 MiB extra, and settled to approximately 546.48 MiB. The ru_maxrss high-water increased during verification in every completed measurement, so it is not merely an inherited larger initialization peak. This measures the current duplicate-decoding implementation; json.load also temporarily allocates the serialized text. All operation receipts retain raw RSS/time values.

Scaling over these three sizes is approximately linear with a process baseline: the peak rises about 507 MiB as artifact size rises about 62.4 MiB; verification rises about 4.47 s. These few warm-cache observations are not an upper bound. Full-size RSS is 2.23 times the previously observed 398 MiB per worker; that earlier figure does not cover the new duplicate verification stage.

The cgroup memory ceiling is 15,032,385,536 bytes (14 GiB), with about 1.855 GiB in use at benchmark launch. Two measured full-size peaks sum to about 1.74 GiB, or about 2.29 GiB after adding the previously measured 568 MiB parent high-water. This arithmetic does not predict simultaneous concurrency exactly and excludes new optimizer allocations, but it does not indicate a need to reduce worker count for memory. Preliminary recommendation: retain two workers and full verification, with resource monitoring. No streaming threshold or weaker check has been implemented. The second full-size failure prevents declaring this a passed operational gate regardless of memory headroom.

## Integrity failure on the second full-size repetition

The helper's first staged parse/count returned, but the next full-value verifier raised JSONDecodeError: Expecting ',' delimiter, line 1 column 70109137 (character 70109136). This was BEFORE atomic replacement. No final size2_repeat1.json exists. The helper correctly refused publication; this was not an OOM report. The exact underlying cause is unresolved. The failed temporary file was removed by the existing finally cleanup, so its bad bytes are not available for forensic inspection. No successful sixth timing/RSS receipt is claimed.

All seven benchmark logs (outer plus six children) were read in full. The outer log records five successful measurements and the failed subprocess; the last child log contains the JSONDecodeError traceback. No convergence warnings or fits occurred. Earlier published benchmark outputs passed their independent post-exit digest/size checks. The source audit remains unchanged. These results are partial evidence, not a passing benchmark.

Under AGENTS.md, the parse/content-integrity failure stops further execution. No retry, assertion alteration, fixture/digest update, production writer modification or max_iter increase followed. The iteration_requirements_v2/probe.py driver was prepared using the Phase 3C verified ledger path inventory and original committed digest values, but it was NOT executed. Nine iteration requirements, production max_iter, permanent convergence logging, full-grid replacement and Phase 4 remain uncompleted. No old generation was relabeled complete or reused.
