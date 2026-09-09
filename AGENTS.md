# ist-review-lab

Reproduction study of AutoTAR (Cormack & Grossman 2015, arXiv:1504.06868) —
continuous active learning for technology-assisted review. Intended for
publication. Correctness beats speed. A silent wrong answer is far worse
than a stop-and-ask.

## Current state

Phase 1 and Phase 1A passed. Phases 2, 3, 3B preflight and 3C are
complete and committed. The Linux handoff is committed on `local-census`
at 48c9ca1b52b26c93ed31ec17ca303e1246583be9; the user reports all
35 tests pass locally.

Phase 3B census execution is not complete. The earlier sandbox generation
failed after 38 completed audits and is superseded for production. The
full 180-run census is authorized only on an external Linux host after
its preflight and storage gates pass. No census ran on the Mac.
Phase 4 remains unauthorized.

Read `CHANGES.md` before doing anything and summarize it back.

Collection: 23,149-document chronological partition of RCV1-v2.
Topics and R: C12=381, C15=4179, C16=49, C18=1462, GCRIM=1133. N=23,149.

## The finding this project exists to establish

At recall@1000 the growing batch schedule and fixed-20 differ by
+0.028 pp, p=0.875. At committed batch effort they differ substantially,
and the difference decomposes.

At the 75% target:

    +97.6 committed  =  +19.6 exact effort  +  78.0 overshoot

Exact effort is **unresolved**: interval [-8.07, 51.07] spans zero,
p=0.3125, topic signs mixed (C16 -26.7, C15 +76.0). This does not
establish that the schedules cross at the same position. It establishes
that this study cannot resolve the difference.

Overshoot carries the signal — roughly 80% of the committed-effort gap
at 75%, all five topics agreeing at every target, both intervals
excluding zero:

| target | overshoot diff | percentile 95% | BCa 95% |
|---|---|---|---|
| 75% | +78.0 docs | [35.5, 131.5] | [39.7, 134.2] |
| 80% | +88.7 docs | [26.7, 175.7] | [33.0, 205.2] |
| 90% | +131.2 docs | [91.4, 169.9] | [91.4, 169.9] |

Mechanism: late growing batches are large, and the whole batch is
committed, so crossing a target costs an oversized commitment. Fixed-20
overshoots by at most 19. This is a review-cost versus compute-cost
tradeoff the original efficiency argument does not account for.

## Standing prohibitions — all phases, no exceptions

- Never modify an assertion, tolerance, or expected value to make a test
  pass. Report the failure and stop.
- Never compute a ground-truth fixture value yourself. The user supplies
  those by hand. Write the assertion around the number they give.
- Never claim statistical significance. With five topics the exact
  sign-flip floor is 0.0625 and several results sit at it. Report
  direction, magnitude, both intervals, per-topic agreement. Never
  `p < 0.05`.
- **Never convert nonsignificance into equivalence.** A wide interval
  means unresolved, not equal, not indistinguishable, not "the same."
  Say unresolved. This rule has been violated once by a reviewer and
  once by an assistant; enforce it against anyone, including whoever is
  instructing you.
- Never manufacture probabilities by passing hinge-loss SVM margins
  through a sigmoid. Log margins only.
- Never change the semantics of the `auto_tar` arm. It is the
  reproduction arm and it is frozen.
- Never state that a paper says something without opening the paper.
  Snippets and abstracts are not the paper. Report "could not access."
- Never invent or complete a citation. Full author list, venue, year,
  DOI or arXiv ID, or nothing.
- Never fill in a missing number, not even as a placeholder.
- Never edit `experiment_plan.json`. It is the historical
  prespecification record. Revisions go in `experiment_plan_v2.json`
  with reasoning in `docs/prespecification.md`.
- Do not refactor, rename, or tidy anything outside the current phase.

## Stop-on-failure scope

Applies to: scientific assertions, numerical comparisons,
integrity/digest checks, input validation.

Not to: figure rendering, file sizes, artifact housekeeping. Those are
warnings — log and continue.

## Phase gates

Never begin a phase without explicit authorization in the current
session. "Continue" resumes the current phase, never enters the next.
Report and stop at each gate, and commit at each gate.

Before Phase 3B runs anything: report a compute estimate and wait.
fixed_20 needed 250 fits at budget 5,000, so census is roughly 1,157
fits per run and fixed_10 is double. If the total is large, propose
which arms to cap. Do not decide unilaterally or drop an arm silently.

## Version control

The project is under git. `v1-frozen` tags the pre-Phase-2 state and
replaces the old `audits_v1_frozen` copy and the 129-file SHA-256
manifest. Do not create `audits_v1_frozen`. Keep the manifest through
Phase 2 as a cross-check, then propose retiring it.

Commit at every phase gate with a message naming what changed.

## Layout

```
analysis/          pure functions, no filesystem side effects
src/               original research implementation
notebooks/         owns all I/O for analysis outputs
results/           v1 artifacts — never write here
results/audits/    original 105 run audits — read-only input
phase1_outputs/    Phase 1 and 1A tables, figures, receipts
docs/              prespecification, fidelity, limitations, phase plan
CHANGES.md         contemporaneous record — append, never rewrite
```

Two timestamp generations exist in `results/`: 07:17–07:36 is the
original study, 16:24–16:43 is Phase 1. `notebook_execution_v1_original.json`
belongs to the original study and describes a different notebook.

## Known blockers, carried forward

- **TARexp validation:** selection ties break on numeric row indices,
  but document IDs are strings, so lexical and row order need not agree.
  Reconcile before attempting an exact match. Target commit
  `d23724a73175cfacbaa95dbaf160a34bc17a1ac0`. TARexp's `SklearnRanker`
  fallback indexes `decision_function(X)[:,1]`, one-dimensional for
  binary LinearSVC; its one-class fallback inserts a zero-vector
  negative rather than sampled negatives. Adapt, don't report as bugs
  in our code.
- **Within-batch ordering confound:** exploration is appended after
  exploitation, so position correlates with operator. Within-batch
  ordering comparisons are invalid. Whole-batch costs remain comparable.
- **tail/global exploration:** withdrawn. Under exploit-first selection
  the ranked tail already equals the residual unreviewed pool, so the
  two are one operator named twice. A distinct version requires drawing
  exploration slots before exploit selection. Deferred.
- **Metric resolution:** C16 has R=49, so recall@R has 2.04 pp of
  resolution per document. That produces exact 0.000000 differences and
  caps the sign test at four nonzero pairs. Report
  `recall_at_1R_plus_100` (0/105 censored) as a companion.

## Metric definitions

`G(k)` = cumulative relevant in first k reviewed. `Rec(k) = G(k)/R_q`.

- `recall@R`, `recall@2R`, `recall@aR+b` for a in {1,2,4}, b in {0,100,1000}
- `effort_at_t` = min{k : G(k) >= ceil(t·R_q)} — exact crossing position
- `batch_effort_at_t` = first batch boundary at or after `effort_at_t` —
  committed cost
- `overshoot_at_t` = `batch_effort_at_t − effort_at_t`
- `depth_fraction` = effort/N, `depth_per_positive` = effort/R

Censoring: if the budget ends before the target is reached the value is
CENSORED with an explicit marker. Never substitute the budget value,
never interpolate, never average across topics when any contributing
topic is censored, never average effort over successes only.

Random-review reference is not k/N. With a free known positive at
position 1: `E[Rec(k)] = (1 + (k−1)(R_q−1)/(N_q−1)) / R_q`.

## Statistics

The experimental unit is the TOPIC. n = 5, not 105. Seeds are
repetitions nested within topic. Average seeds within a topic before
inference.

Exact paired sign-flip is primary — no distributional assumption, and
the only test worth publishing at this sample size. Percentile and BCa
intervals are sensitivity analyses; report both and treat disagreement
as evidence the interval is untrustworthy. Always report the number of
nonzero pairs alongside any p-value.

## Mandatory phase-gate log inspection

Every phase gate must inspect run logs and captured warnings, not only test results and numerical outputs. A passing test suite is not evidence that nothing went wrong. Record the logs inspected and any warnings, their attribution where known, and their resolution or explicit unresolved status before reporting the gate. Do not infer absence of warnings from a log tail or from successful exit status.


## Durable artifact publication (Phase 3C)

All new application artifact writers must use src/durable_io.py. Supply expected record counts for tabular/ledger streams and immutable reference digests where available. Do not hash an in-memory representation as a claim about a published file. Wait for full worker exit, then independently reopen/parse/count/hash final artifacts. Capture run logs through scripts/capture_command.py or src/monitor_census.py; bare shell redirection is not a durable publication path. Publication or content-verification failure is an integrity stop. Immutable historical evidence is not rewritten to migrate an old embedded writer.


## Patch handoff base

Base each patch or replacement-file handoff on the latest commit the user explicitly confirms, and state its full SHA in the handoff. Latest confirmed base: **48c9ca1b52b26c93ed31ec17ca303e1246583be9** on `local-census`. Use this base until the user confirms a newer commit. Do not assume the user's SHA equals an assistant commit after transferring changes; inspect origin and ask if the base remains uncertain. The Linux handoff reached this commit through verified complete-file transfer, not patch application. Census runs only on an external Linux host after its required gates pass. No sandbox census or Phase 4 is authorized.

### Linux handoff supersedes the macOS routing (2026-09-08)

The Linux handoff was prepared from **95cafe313c1861b41004cd5cfbc1c72fd2750c40** on `local-census`; the latest confirmed base is recorded above. The Mac has 8 GiB, not the user-supplied 14 GB used in prior sizing. Both available-memory gates failed; no storage trial or census ran there. Preserve the attempt record. Do not lower the 4 GiB threshold or offer a smaller Mac configuration. Census now runs only on a separately obtained external Linux VM or Slurm allocation, after the unchanged gates pass there. Two workers, max_iter=41,000, convergence logging and full verification remain unchanged. No sandbox census and no Phase 4.