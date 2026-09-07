# IST Review Lab: Phase 1 results

Recall@R is fully observed: **0/105 runs and 0/21 policy comparisons censored**.
This is the reportable core across five topics, three seeds and seven policies.
The original declared recall@1000 remains fully observed and visible alongside it.
Recall@R became the revised primary AFTER outcomes were observed; this is exploratory reanalysis,
not advance prespecification or an exact replication of the paper's result tables.

## Fully observed measures

Topic means require all three seeds; the macro mean weights all five topics equally.

| method | recall_at_R | recall_at_1000 |
| --- | --- | --- |
| random | 7.07% | 4.68% |
| seed_similarity | 26.62% | 27.24% |
| frozen_svm | 25.76% | 27.73% |
| uncertainty | 40.67% | 51.02% |
| auto_tar | 65.27% | 66.43% |
| fixed_20 | 64.64% | 66.40% |
| explore_10 | 63.11% | 64.26% |

The exact sign-flip test on five seed-averaged topic differences is the primary inferential statement.
With at most five nonzero topic differences its smallest attainable two-sided p-value is 0.0625.
Neither nonsignificance nor close means establish equivalence.
Every contrast table reports both 95% percentile and BCa intervals and the raw five differences.
Agreement between the two intervals does not establish reliable coverage at this sample size.

Material BCa/percentile disagreement occurs in 27 of the 112 fully observed metric/pair contrasts (metric aliases included). 
Material means different zero inclusion or a maximum endpoint shift of at least 25% of the percentile interval width.
This diagnostic was selected in the post-outcome amendment, before computing BCa.
Disagreement is evidence that interval inference is not trustworthy here.

## Censored measures: the 5,000-document budget

| metric | censored_runs | total_runs | censored_policy_pairs | total_policy_pairs | run_censor_topics | pair_censor_topics |
| --- | --- | --- | --- | --- | --- | --- |
| recall_at_1000 | 0 | 105 | 0 | 21 |  |  |
| recall_at_R | 0 | 105 | 0 | 21 |  |  |
| recall_at_2R | 21 | 105 | 21 | 21 | C15:21 | C15:21 |
| recall_at_1R_plus_0 | 0 | 105 | 0 | 21 |  |  |
| recall_at_1R_plus_100 | 0 | 105 | 0 | 21 |  |  |
| recall_at_1R_plus_1000 | 21 | 105 | 21 | 21 | C15:21 | C15:21 |
| recall_at_2R_plus_0 | 21 | 105 | 21 | 21 | C15:21 | C15:21 |
| recall_at_2R_plus_100 | 21 | 105 | 21 | 21 | C15:21 | C15:21 |
| recall_at_2R_plus_1000 | 21 | 105 | 21 | 21 | C15:21 | C15:21 |
| recall_at_4R_plus_0 | 42 | 105 | 21 | 21 | C15:21; C18:21 | C15:21; C18:21 |
| recall_at_4R_plus_100 | 42 | 105 | 21 | 21 | C15:21; C18:21 | C15:21; C18:21 |
| recall_at_4R_plus_1000 | 63 | 105 | 21 | 21 | C15:21; C18:21; GCRIM:21 | C15:21; C18:21; GCRIM:21 |
| effort_at_75 | 43 | 105 | 18 | 21 | C12:6; C15:12; C16:7; C18:9; GCRIM:9 | C12:15; C15:18; C16:15; C18:15; GCRIM:18 |
| batch_effort_at_75 | 43 | 105 | 18 | 21 | C12:6; C15:12; C16:7; C18:9; GCRIM:9 | C12:15; C15:18; C16:15; C18:15; GCRIM:18 |
| depth_fraction_at_75 | 43 | 105 | 18 | 21 | C12:6; C15:12; C16:7; C18:9; GCRIM:9 | C12:15; C15:18; C16:15; C18:15; GCRIM:18 |
| depth_per_positive_at_75 | 43 | 105 | 18 | 21 | C12:6; C15:12; C16:7; C18:9; GCRIM:9 | C12:15; C15:18; C16:15; C18:15; GCRIM:18 |
| effort_at_80 | 46 | 105 | 18 | 21 | C12:7; C15:12; C16:8; C18:9; GCRIM:10 | C12:15; C15:18; C16:15; C18:15; GCRIM:18 |
| batch_effort_at_80 | 46 | 105 | 18 | 21 | C12:7; C15:12; C16:8; C18:9; GCRIM:10 | C12:15; C15:18; C16:15; C18:15; GCRIM:18 |
| depth_fraction_at_80 | 46 | 105 | 18 | 21 | C12:7; C15:12; C16:8; C18:9; GCRIM:10 | C12:15; C15:18; C16:15; C18:15; GCRIM:18 |
| depth_per_positive_at_80 | 46 | 105 | 18 | 21 | C12:7; C15:12; C16:8; C18:9; GCRIM:10 | C12:15; C15:18; C16:15; C18:15; GCRIM:18 |
| effort_at_90 | 58 | 105 | 20 | 21 | C12:12; C15:12; C16:10; C18:12; GCRIM:12 | C12:18; C15:18; C16:18; C18:18; GCRIM:18 |
| batch_effort_at_90 | 58 | 105 | 20 | 21 | C12:12; C15:12; C16:10; C18:12; GCRIM:12 | C12:18; C15:18; C16:18; C18:18; GCRIM:18 |
| depth_fraction_at_90 | 58 | 105 | 20 | 21 | C12:12; C15:12; C16:10; C18:12; GCRIM:12 | C12:18; C15:18; C16:18; C18:18; GCRIM:18 |
| depth_per_positive_at_90 | 58 | 105 | 20 | 21 | C12:12; C15:12; C16:10; C18:12; GCRIM:12 | C12:18; C15:18; C16:18; C18:18; GCRIM:18 |

Recall@2R is unobserved for every C15 run; any four-topic recall mean must explicitly exclude C15.
The recall@4R family additionally censors C18, and at 4R+1000 also GCRIM.
Most target-effort policy comparisons are censored: 18/21 at 75% and 80%, 20/21 at 90%.
Every topic contributes. The 5,000-document budget is too short for these complete five-topic
comparisons. No success-only effort mean or complete-case inference replaces them.

The five full gain trajectories per topic/policy/seed remain available at every observed review
position in gain_curves.csv.gz. Figures use log-spaced display positions for compact rendering;
this changes presentation only. Seed acquisition cost was excluded in the original plan.

## Scope and deferred work

No learning experiment was rerun. No load_collection() or experiment.py was invoked.
Phase 2 will split RNG streams; no redundant pool/tail option will be implemented.
After Phase 3 instrumentation passes exact replay, a new-generation run must cover all five topics
to budget=N=23,149 with the new streams. Do not perform that run in Phase 1 or Phase 2.
This study concerns fixed-label document retrieval, not sales conversion or stopping certification.
The whole Phase 1 gate status is recorded separately in notebook_execution.json; this table report
alone does not certify artifact completeness or repeatability.
