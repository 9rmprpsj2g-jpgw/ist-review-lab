# Phase 1 results tables

POST-OUTCOME revision: original recall@1000; revised recall@R.

## Original and revised metrics

| method | recall_at_1000 | recall_at_R | recall_at_2R |
| --- | --- | --- | --- |
| random | 4.68% | 7.07% | CENSORED ; PARTIAL 7.38% (4/5; excludes C15) |
| seed_similarity | 27.24% | 26.62% | CENSORED ; PARTIAL 29.67% (4/5; excludes C15) |
| frozen_svm | 27.73% | 25.76% | CENSORED ; PARTIAL 32.27% (4/5; excludes C15) |
| uncertainty | 51.02% | 40.67% | CENSORED ; PARTIAL 58.23% (4/5; excludes C15) |
| auto_tar | 66.43% | 65.27% | CENSORED ; PARTIAL 73.89% (4/5; excludes C15) |
| fixed_20 | 66.40% | 64.64% | CENSORED ; PARTIAL 74.16% (4/5; excludes C15) |
| explore_10 | 64.26% | 63.11% | CENSORED ; PARTIAL 73.19% (4/5; excludes C15) |

## Censoring census

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

## Target 75%

| method | recall_at_1000 | effort_at_75 | batch_effort_at_75 | depth_fraction_at_75 | depth_per_positive_at_75 |
| --- | --- | --- | --- | --- | --- |
| random | 4.68% | CENSORED (topics: C12,C15,C16,C18,GCRIM); no mean | CENSORED (topics: C12,C15,C16,C18,GCRIM); no mean | CENSORED (topics: C12,C15,C16,C18,GCRIM); no mean | CENSORED (topics: C12,C15,C16,C18,GCRIM); no mean |
| seed_similarity | 27.24% | CENSORED (topics: C12,C15,C16,C18,GCRIM); no mean | CENSORED (topics: C12,C15,C16,C18,GCRIM); no mean | CENSORED (topics: C12,C15,C16,C18,GCRIM); no mean | CENSORED (topics: C12,C15,C16,C18,GCRIM); no mean |
| frozen_svm | 27.73% | CENSORED (topics: C12,C15,C16,C18,GCRIM); no mean | CENSORED (topics: C12,C15,C16,C18,GCRIM); no mean | CENSORED (topics: C12,C15,C16,C18,GCRIM); no mean | CENSORED (topics: C12,C15,C16,C18,GCRIM); no mean |
| uncertainty | 51.02% | CENSORED (topics: C15,GCRIM); no mean | CENSORED (topics: C15,GCRIM); no mean | CENSORED (topics: C15,GCRIM); no mean | CENSORED (topics: C15,GCRIM); no mean |
| auto_tar | 66.43% | 1,310.533 | 1,399.933 | 0.057 | 1.919 |
| fixed_20 | 66.40% | 1,290.933 | 1,302.333 | 0.056 | 2.005 |
| explore_10 | 64.26% | 1,405.133 | 1,525.400 | 0.061 | 2.062 |

## Target 80%

| method | recall_at_1000 | effort_at_80 | batch_effort_at_80 | depth_fraction_at_80 | depth_per_positive_at_80 |
| --- | --- | --- | --- | --- | --- |
| random | 4.68% | CENSORED (topics: C12,C15,C16,C18,GCRIM); no mean | CENSORED (topics: C12,C15,C16,C18,GCRIM); no mean | CENSORED (topics: C12,C15,C16,C18,GCRIM); no mean | CENSORED (topics: C12,C15,C16,C18,GCRIM); no mean |
| seed_similarity | 27.24% | CENSORED (topics: C12,C15,C16,C18,GCRIM); no mean | CENSORED (topics: C12,C15,C16,C18,GCRIM); no mean | CENSORED (topics: C12,C15,C16,C18,GCRIM); no mean | CENSORED (topics: C12,C15,C16,C18,GCRIM); no mean |
| frozen_svm | 27.73% | CENSORED (topics: C12,C15,C16,C18,GCRIM); no mean | CENSORED (topics: C12,C15,C16,C18,GCRIM); no mean | CENSORED (topics: C12,C15,C16,C18,GCRIM); no mean | CENSORED (topics: C12,C15,C16,C18,GCRIM); no mean |
| uncertainty | 51.02% | CENSORED (topics: C15,GCRIM); no mean | CENSORED (topics: C15,GCRIM); no mean | CENSORED (topics: C15,GCRIM); no mean | CENSORED (topics: C15,GCRIM); no mean |
| auto_tar | 66.43% | 1,468.067 | 1,565.733 | 0.063 | 2.341 |
| fixed_20 | 66.40% | 1,424.067 | 1,433.000 | 0.062 | 2.249 |
| explore_10 | 64.26% | 1,552.667 | 1,660.533 | 0.067 | 2.344 |

## Target 90%

| method | recall_at_1000 | effort_at_90 | batch_effort_at_90 | depth_fraction_at_90 | depth_per_positive_at_90 |
| --- | --- | --- | --- | --- | --- |
| random | 4.68% | CENSORED (topics: C12,C15,C16,C18,GCRIM); no mean | CENSORED (topics: C12,C15,C16,C18,GCRIM); no mean | CENSORED (topics: C12,C15,C16,C18,GCRIM); no mean | CENSORED (topics: C12,C15,C16,C18,GCRIM); no mean |
| seed_similarity | 27.24% | CENSORED (topics: C12,C15,C16,C18,GCRIM); no mean | CENSORED (topics: C12,C15,C16,C18,GCRIM); no mean | CENSORED (topics: C12,C15,C16,C18,GCRIM); no mean | CENSORED (topics: C12,C15,C16,C18,GCRIM); no mean |
| frozen_svm | 27.73% | CENSORED (topics: C12,C15,C16,C18,GCRIM); no mean | CENSORED (topics: C12,C15,C16,C18,GCRIM); no mean | CENSORED (topics: C12,C15,C16,C18,GCRIM); no mean | CENSORED (topics: C12,C15,C16,C18,GCRIM); no mean |
| uncertainty | 51.02% | CENSORED (topics: C12,C15,C18,GCRIM); no mean | CENSORED (topics: C12,C15,C18,GCRIM); no mean | CENSORED (topics: C12,C15,C18,GCRIM); no mean | CENSORED (topics: C12,C15,C18,GCRIM); no mean |
| auto_tar | 66.43% | 2,582.667 | 2,724.267 | 0.112 | 15.725 |
| fixed_20 | 66.40% | 2,519.933 | 2,530.333 | 0.109 | 15.706 |
| explore_10 | 64.26% | CENSORED (topics: C16); no mean | CENSORED (topics: C16); no mean | CENSORED (topics: C16); no mean | CENSORED (topics: C16); no mean |

Complete per-topic, per-seed, scaled-cutoff and statistical tables are regenerated by the notebook and exported as CSV/HTML. No full effort mean is computed when any contributing seed/topic is censored.
