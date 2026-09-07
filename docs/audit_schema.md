# Phase 3 audit schema and gate

Schema version 3 retains `row_order`, `batch_ends`, and `observed_labels` for compatibility and adds `rounds` and resolved `audit_config`. Round zero is the supplied seed, with no model fit or margins. Subsequent round indices are contiguous. `fit_index` is one-based and references the model used that round; it is null for non-SVM policies. A frozen model retains its fit index. The nested `fit` object is present only when that round performs a fit, so summing its `fit_seconds` counts each fit once.

Each round records selected numeric rows, external string document IDs and aligned operators (seed, random, exploit, explore), and scheduled batch size immediately before and after growth. The length of selected_rows is the actual clipped batch size. Growth is recorded even for the final budget-clipped batch, matching existing behavior. Temporary-negative external IDs list only draws made that round, with numeric rows inside the fit record. Each fit stores the actual model get_params(deep=True) before fitting. Wall-clock time uses perf_counter around model.fit only, excluding matrix slicing, model construction, ranking, audit serialization and other overhead. It is not total computational runtime; Phase 4 must name this boundary.

Candidate margins contain aligned rows, external IDs and raw decision_function values in numeric candidate-row order. Uncertainty's negative-absolute-value ranking transformation does not change the logged margins. Random and seed_similarity have no SVM margins; null plus policy_has_no_svm records that absence. Seed margins are null with seed_before_ranking. There are no probabilities. Resolved config defaults audit.margin_scope to full; other scopes are rejected until an explicitly approved truncation design is implemented. No experiment-plan file was changed.

`src.audit.replay_row_order` reconstructs selections from round records without consulting the flat row_order field, data loader, labels or model. It validates schema, contiguous round indices, aligned selections, unique identities and selection operators. The experiment writer checks exact equality with its observed order before writing. The test round-trips JSON for all seven policies, omits flat row_order entirely, forbids model construction during replay, and compares the complete reconstructed order to selections captured during the mocked learner loop. Additional contracts cover raw candidate-margin alignment, actual parameters, temporary IDs, fit counts and timing. These are instrumentation contracts, not independent retrieval ground-truth validation or an exact TARexp match. No real collection or fitted classifier was used.

## Storage planning (decimal MB, uncompressed)

| Policy | Budget 5,000 | Budget 23,149 |
|---|---:|---:|
| random / seed_similarity | 0.42–0.84 | 1.88–3.75 |
| seed_only_frozen | 25.42–50.84 | 31.18–62.35 |
| uncertainty / auto_tar / explore_10 | 25.56–51.12 | 31.36–62.72 |
| fixed_20 | 125.20–250.40 | 327.56–655.13 |

These are planning estimates, not measured per-run files. The executable arithmetic-only estimator and its assumptions are in phase3_outputs/estimate_audit_size.py and audit_size_estimates.json. Candidate counts follow the unchanged schedules with one seed and N=23,149. The envelope assumes 24–48 bytes per aligned margin entry including its row and external ID, IDs at most 12 ASCII characters, plus declared selection/round/fit overhead. Compression is not assumed. Python object memory can substantially exceed serialized size. Actual file sizes remain unmeasured because experimental runs are prohibited.

Fixed-20 has 250 query rounds at 5,000 and 1,158 at census, including the clipped final batch. Its census full-margin files alone would total roughly 4.9–9.8 GB for 15 topic/seed runs. Proposed, NOT activated: retain the top 1,000 by the policy's ranking plus every selected document's margin, with explicit recorded scope, candidate count and truncation. This would bound fixed-20 logged candidates to about 1,000 per round while preserving selected-document diagnostics. It would omit lower-ranked candidate scores and therefore cannot support later full-pool margin analysis or score-based independent selection verification. Audit-only replay would remain exact because it uses recorded selections. User approval and explicit config design are needed before adopting this tradeoff; no N was silently chosen.

## Deferred

Numeric-row versus lexical-string-ID tie order still blocks exact TARexp matching. Exploit-first/explore-last remains a within-batch confound; tail/global sampling is not implemented. Probability-based stopping belongs to a distinct future logistic-regression arm. Phase 3B requires separate compute estimates and approval before any experiment, schedule sweep or census run.

## Approved margin scope amendment

The default for API callers remains full for compatibility. experiment_plan_v2.json explicitly chooses audit.margin_scope="top_1000_plus_selected". Both values are accepted. Every query round records margin_scope and candidate_count before selection. Round zero records the same configured scope and N−1 unreviewed documents after the supplied seed; it is not a scored candidate set. Retained rows stay in numeric candidate order; membership is the union of the first 1,000 under the policy's actual ranking and all selected rows. Uncertainty therefore uses closeness to zero for membership while logging raw signed margins. Exploration selections outside the top 1,000 are retained. No ranking, tie-breaking or selection behavior changes.

This supersedes the earlier full-only restriction and unapproved top-N proposal. Full-pool margin distribution analysis is no longer available directly in truncated audit files. Refit-based recovery requires the same feature matrix, ordered training set (recoverable from prior selections, observed_labels and temporary-negative rows), parameters, RNG/environment and solver behavior. Exact margin regeneration is not tested here and cross-platform bit identity is not guaranteed.

The user's rationale that every study batch is below 1,000 does not extend to census: the arithmetic maximum actual batch is 2,070 for 10% growth, 1,096 for 5%, and 3,373 for 20%. All-selected retention covers these. Logged top/selected scores permit internal consistency checks but cannot independently establish that no omitted score exceeds the cutoff. That stronger check needs recomputation or full scores; even a purported top-N list relies on correct instrumentation. Selection replay is unchanged and does not depend on scores.
