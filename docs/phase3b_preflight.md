# Phase 3B preflight — no experimental runs authorized

All figures below cover five topics times three seeds per policy (180 runs total), N=budget=23,149. Schedules start with one externally supplied positive; fixed schedules start at their named size, growing schedules start at one and add ceil(rate × batch size) after every query. New sweep arms are arithmetic specifications here, not yet added to executable learner policies. Training cannot start until those arms and the separately approved storage routing are implemented and tested.

## Full requested grid

Times are sequential worker-minutes for all 15 runs of each policy. They are extrapolation scenarios, not measured census durations or confidence bounds. Audit MB are decimal, uncompressed, also for all 15 runs.

| Policy | Fits/run | Fits/15 | Worker minutes | Audit MB/15 | Audit + serialization RAM MB/run |
|---|---:|---:|---:|---:|---:|
| random | 0 | 0 | 0.01–0.01 | 28.2–56.3 | 7.5 |
| seed_similarity | 0 | 0 | 0.17–0.19 | 28.2–56.3 | 7.5 |
| seed_only_frozen | 1 | 15 | 0.11–0.12 | 52.3–104.5 | 19.3 |
| uncertainty | 63 | 945 | 1.51–6.15 | 55.0–110.1 | 20.1 |
| auto_tar | 63 | 945 | 0.96–3.93 | 55.0–110.1 | 20.1 |
| fixed_20 | 1,158 | 17,370 | 25.78–207.15 | 494.7–989.4 | 223.7 |
| explore_10 | 63 | 945 | 0.92–3.74 | 61.5–123.1 | 23.3 |
| fixed_10 | 2,315 | 34,725 | 51.53–414.13 | 961.4–1922.7 | 439.8 |
| fixed_50 | 463 | 6,945 | 10.32–82.68 | 214.6–429.3 | 94.0 |
| fixed_100 | 232 | 3,480 | 5.17–41.43 | 121.3–242.6 | 50.7 |
| grow_5pct | 95 | 1,425 | 1.40–6.90 | 66.9–133.8 | 25.5 |
| grow_20pct | 40 | 600 | 0.64–1.95 | 47.7–95.4 | 16.7 |

**Aggregate: 67,395 fits; 98.51–768.38 worker-minutes (1.64–12.81 hours); 2.19–4.37 GB audits.** Ideal two-worker elapsed time is 49.26–384.19 minutes (0.82–6.40 hours), plus startup, audit serialization and I/O, contention and scheduling imbalance. It is not a guaranteed wall-clock range. No measured per-fit census time exists; Phase 3 timing tests were mocked.

## Estimation evidence and limitations

The script reads only committed results/runs.csv. It averages original seconds within policy, uses fixed_20 as the proxy for new fixed arms and auto_tar for new growth arms, and scales by query-round counts, cumulative training rows (reviewed plus up to 100 temporary negatives), and cumulative candidate rows. Endpoints are the minimum/maximum of these scaling scenarios. Random, similarity and frozen use round/candidate scaling only. The original seconds field covers the review loop, not per-fit time or audit writing; no claim of separately measured fitting/ranking cost is possible. Solver convergence, prevalence and growing training sets can violate linear extrapolation; the upper scenario is not a safety bound. This uses original-generation timing as a hardware/workload proxy, not an exact paired trajectory comparison. Script inputs and assumptions are reproducible; no model was run for this estimate.

Audit entry counts follow the schedules. Each SVM round retains min(pool, max(1000, batch)) entries for pure ranking. Exploration uses the conservative union upper count min(pool,1000+batch), without inventing random overlap. Storage uses 24–48 bytes per margin entry, 80–160 per reviewed document, 400–800 per round and 3,000–6,000 per fit; external IDs assumed at most 12 ASCII characters. Byte ranges are planning envelopes, not measured sizes. The recorded candidate count is always the full preselection pool size, even when margins are truncated.

## Peak memory

The table estimates retained Python audit objects plus one JSON serialization string using this runtime's object sizes and the high storage estimate. Worst arm fixed_10: about 440 MB per worker before model/data overhead. Historical results/run.log records 1,739,103 nonzeros and 28,454 features; float64/int32 CSR storage is about 20.96 MB. Adding the full matrix and one census-size training slice brings accounted memory to approximately 482 MB per worker. Two worst-case workers plus a parent's matrix account for approximately 985 MB, **plus unmeasured interpreter, model/solver copies, loader/vectorizer peak, allocator overhead, transient objects and process duplication**. This is a component estimate, not a measured peak RSS or a certified memory bound. Parent plus each worker currently invokes loading independently. No finite total peak bound is established without a profiling run; none is authorized here. Use the single-worker component numbers if parallelism is reduced. On a constrained machine, do not infer that 1 GB RAM is enough from this calculation.

## Capping recommendation — requires approval

Preserve all seven original policies at census, especially the auto_tar/fixed_20 comparison, and protect grow_5pct and grow_20pct because they vary the proposed overshoot mechanism. Among optional fixed arms, retained scientific priority is fixed_50, then fixed_100, then fixed_10; cap in reverse order, exactly as requested. Each can extend the frontier, but none is needed to retain the main comparator or test growth-rate dependence.

Recommend first capping **fixed_10 at 5,000**, leaving all other arms at census. This changes total fits to 40,170 and the historical scenarios to approximately 66.84–374.15 worker-minutes (1.11–6.24 worker-hours; ideal two-worker 0.56–3.12 hours), excluding new I/O. Its 15 runs then need 7,500 fits rather than 34,725. If that remains excessive, next cap fixed_100 at 5,000 (750 rather than 3,480 fits), then fixed_50 at 5,000 (1,500 rather than 6,945). No cap is activated and no policy is dropped.

A capped arm may remain censored at 90% recall, especially on C15. It cannot supply a complete five-topic 90%-recall frontier point; never average only successful topics to hide this. Protecting growth variants and original policies preserves the complete comparisons most relevant to overshoot. A future deeper rerun of a capped arm would create the extra work this combined pass seeks to avoid; full census remains preferable if the available runtime and RAM permit it.
