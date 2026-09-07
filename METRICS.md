# Phase 1 measures

The original declared primary metric, **recall@1000**, is always shown beside the revised measures. The new primary metric, recall@R, was chosen **after outcomes were observed**; see `docs/prespecification.md`.

For topic q, method m, and seed s, let N_q and R_q be the `n` and `positives` values in `results/runs.csv`, L be the logged review count, y_j the recorded label at review position j, and B the recorded batch boundaries. Positions are one-based; the known-positive seed occupies position 1 and counts as a review.

| Measure | Definition |
| --- | --- |
| Gain | G(k) = sum of y_j for j = 1,...,k; defined here only for 1 <= k <= L |
| Recall | Rec(k) = G(k) / R_q |
| Original recall@1000 | Rec(1000); censored if fewer than 1000 positions are logged |
| Revised recall@R | Rec(R_q) |
| Recall@2R | Rec(min(N_q, 2R_q)) |
| Recall@aR+b | Rec(min(N_q, aR_q+b)), for a in {1,2,4}, b in {0,100,1000} |
| Exact target effort | E_t = min{k : G(k) >= ceil(t R_q)}, for t in {0.75,0.80,0.90} |
| Whole-batch target effort | min{b in B : b >= E_t} |
| Normalized target depths | E_t / N_q and E_t / R_q |
| Conditional random-review expectation | (1 + (k-1)(R_q-1)/(N_q-1)) / R_q |
| Ideal bound | min(k/R_q, 1) |

The normalized gain-curve x-coordinate is k/R_q. Targets are computed with integer ceiling arithmetic to avoid floating target-rounding artifacts. Fractional metric numerators and denominators are retained for exact zero-difference detection in statistics.

## Censoring and aggregation

Every unobserved value has status `CENSORED`, a missing numeric value, and a reason. An unobserved target depth has a strict lower bound E_t > L (or L/N_q and L/R_q for normalized variants); the bound is never used as an observed value. A recall cutoff beyond L remains censored even if the final logged curve looks flat. No interpolation or extrapolation beyond L is allowed.

Per-topic means require all seeds to be observed. Full macro means average these topic means with equal weights and require every topic. If a recall macro mean is incomplete, the full mean remains missing; a separate PARTIAL recall mean may be supplied with coverage and excluded topic names. Effort means over successful runs or complete-topic subsets are never supplied. Pairwise tests are not computed on a censored subset.

The original metric is repeated as an anchor in every reader-facing topic/method metric-summary family, including scaled cutoffs, target depths and statistical comparisons. Exhaustive long-form CSV files preserve all rows and status columns.

## Paired statistics

For each unordered pair (a,b) and metric M, d_q = mean_s(M_qsa - M_qsb), averaging all paired seeds first. The sign convention is always method_a minus method_b. Every tested comparison uses the full topic set.

- Paired percentile bootstrap: draw topics with replacement, retaining their paired, seed-averaged differences; 10,000 resamples; 95% interval using the 2.5% and 97.5% quantiles. A stable hash of the analysis seed (20260907), metric and method pair initializes a separate local generator.
- BCa sensitivity uses SciPy `bootstrap(method="BCa", n_resamples=0, bootstrap_result=...)` on the same retained bootstrap distribution. Bias correction and leave-one-topic-out acceleration change endpoints, not draws. Report `bca_ci_low/high` alongside `bootstrap_ci_low/high` (percentile) and all five raw seed-averaged topic differences. Undefined/degenerate BCa is explicitly marked, never replaced by percentile. See [SciPy bootstrap documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html), referencing Efron and Tibshirani (1993), *An Introduction to the Bootstrap*.
- Both intervals are exploratory sensitivities with unreliable coverage at five topics. Exact sign-flip remains primary. Material disagreement means different inclusion of zero or either endpoint moving by at least 25% of percentile interval width. This is a disclosed post-outcome diagnostic chosen before computing BCa, not a validated statistical threshold. The absolute endpoint shift is also reported; agreement does not prove reliable coverage.
- Exact sign-flip: enumerate all signs on nonzero d_q and count absolute sums at least as large as observed. Zero pairs stay in the mean's topic denominator but need no sign enumeration.
- Wilcoxon sensitivity: discard zero differences, average the ranks of tied absolute differences, enumerate their signs, and compare absolute signed-rank sums. This is an exact conditional sign-enumeration test, not an asymptotic normal approximation.
- Report the number m of nonzero topic pairs. The minimum attainable two-sided p-value is min(1, 2/2^m); explicitly state when it exceeds 0.05.

All pairwise tests are exploratory and unadjusted. Five-topic bootstrap intervals may be unstable and can disagree with exact tests; they do not override discrete p-value resolution. Failure to reject is never described as equivalence. Confidence intervals and tests concern variation across these topics, not a guarantee for future legal matters.

## Figures

Phase 1A adds `overshoot_at_t = batch_effort_at_t - effort_at_t` for t=75/80/90. Compute within each run first, then apply the existing paired seed/topic aggregation and exact sign-flip, percentile and BCa methods. Censor if either component is censored. An unobserved overshoot has the trivial nonnegative lower bound 0, not the review budget: subtracting two censored effort bounds does not identify the difference. Store `censor_reason=component_censored`; never replace a censored value by zero. Report per-policy topic means and paired per-topic differences. No significance claim is made from these five-topic results.

Recall@(R+100), already fully observed, is a reported low-prevalence companion to recall@R. C16's R=49 gives 2.0408 pp per relevant document. The companion extends startup review allowance; its recall denominator and per-document resolution remain unchanged. Ties need not disappear. The original recall@1000 remains visible. The report now leads with overshoot; complete observation is a measurement property, not the headline criterion.

Reproduce the analysis-only amendment with `python -m analysis.phase1a`. It reads immutable archived inputs, verifies that every preexisting metric CSV record remains identical, checks overshoot's component identity and censoring, and writes `phase1a_outputs/`. It neither invokes the learner nor creates hand-ground-truth fixtures. The approved Phase 1 outputs and notebook remain historical evidence; the amended RESULTS.md is backed by the separate Phase 1A tables.

The full gain CSV retains every logged prefix. Compact figures display 128 rounded log-spaced review positions plus endpoints and observed 1000/R/2R cutoffs, removing duplicates. Step lines connect these samples; intervening jumps are visually coarsened and cannot reconstruct exact effort. Normalized plots use those same observed positions divided by R. Conditional-random and ideal references accompany thin seed curves and thick within-topic means. No curve extends beyond observed data. Raster output has explicit 100 dpi; axes, labels, and legends remain vector in SVG/PDF. The former 500 KB target is withdrawn; there is no figure size threshold. Target-effort panels retain every run and censor arrows. Exploitation-first within-batch ordering remains a confound; whole-batch costs remain comparable.

## Reproduce

Use a Python environment with `requirements-phase1.txt`, then run from the project root:

```bash
python -m analysis.execute_notebook
```

The executor uses the user-authorized socket-free fallback: Python compile/exec in one newly allocated namespace per run, two separate fresh subprocesses, IPython rich-output capture, and nbformat serialization. It does not use nbclient or claim kernel execution. The installed in-process manager is not a drop-in nbclient lifecycle implementation; the previous normal ZeroMQ kernel failed before its first cell. The execution receipt records versions and the failure reason. The authored notebook uses explicit display/print; this fallback does not implement IPython magics or implicit last-expression display.

Both executions regenerate tables and figures from immutable inputs in separate directories under `phase1_outputs/reproducibility/`; `--resume SESSION` reuses an already completed first execution and launches only run2. Each figure uses a temporary file, flush, fsync, close, then os.replace, with finally cleanup. The parent waits for full subprocess exit, removes stray .writing-* files and logs their names/sizes as housekeeping warnings. PNGs pass Pillow verification and full decoding; SVGs parse as XML; JSON/notebooks parse (notebooks also pass nbformat validation); CSV rows parse with strict field counts, including complete gzip decompression/CRC. PDFs must end with %%EOF, open without repair, and decode all pages. HTML requires its closing marker.

The FINAL user gate requires exact bytes for CSV (including compressed gain CSV), JSON, executed notebooks, Markdown and HTML; all figures complete and decodable; protected-file digests unchanged. No cross-run figure byte/pixel identity or size threshold is required. Figure byte differences are logged by filename as warnings. Both raw SHA-256 inventories and per-file criteria are retained. Stop-on-failure applies only to scientific assertions, numerical comparisons, integrity/digest checks and input validation. Figure rendering, size and housekeeping get warnings and may be repaired without reopening the scientific gate; completeness is still necessary before claiming PASS. SVG/PDF dates remain omitted, SVG IDs use a fixed salt, and gzip mtime is zero. The authorized input-record rename retains its original expected digest. The abandoned scratch-file stop was housekeeping litter, not lost output or analytical nondeterminism.

After notebook execution, `analysis.review_report` independently renders each run's persisted tables into `review_results.md`; that file must also match exactly. Its passing copy becomes root RESULTS.md and phase1_outputs/RESULTS.md. The notebook's earlier RESULTS.md is retained within each run; the published reader version expands inference details without changing any numerical result.

`censoring_census.csv` reports each metric's censored runs (out of 105) and censored full-topic policy comparisons (out of 21), with per-topic drivers. A pair is censored whenever either policy has any censored seed on any topic. Pair counts by topic overlap. Recall@1000 is retained throughout.

This analysis does not supply Phase 4 hand-computed fixtures or assert external validation of the original learner.
