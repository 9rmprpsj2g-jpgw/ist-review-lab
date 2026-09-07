# Phase 1A: growing batches add committed review through overshoot

Overshoot is committed batch effort minus exact effort at the target crossing. Late growing batches can commit reviewers to documents beyond that crossing. We derive this quantity for each run at 75%, 80% and 90% recall, then compare paired topic means. A censored component censors overshoot; no success-only mean is substituted.

The original recall@1000 difference between AutoTAR and fixed-20 is +0.0276 percentage points (exact sign-flip p=0.875). Committed effort tells a different cost story: AutoTAR minus fixed-20 is +97.6, +132.7 and +193.9 documents at 75%, 80% and 90% targets. At 80% and 90% all five topics agree in direction. These are direction and magnitude observations, NOT statistically significant findings; the five-topic exact two-sided floor is 0.0625.

**Correction to the proposed interpretation:** archived exact effort at 75% is +19.6 documents, percentile 95% interval [-8.07, 51.07], p=0.3125. The supplied -1.06 documents and interval [-1.47, -0.65] do not match the archived exact-effort contrast. The supported decomposition is +97.6 = +19.6 exact effort +78.0 overshoot. This does not show that growing batches cross the target one document earlier.

This amendment is post-outcome analysis of the same five topics, three seeds and seven policies. No learning experiment has been rerun.




## Overshoot by topic and policy

Documents committed beyond crossing; means require all three seeds. Paired tables report method_a minus method_b, both 95% intervals and raw five-topic differences. Exact sign-flip remains primary; neither interval is reliable with five topics.

| Target | Topic | random | seed_similarity | frozen_svm | uncertainty | auto_tar | fixed_20 | explore_10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 75% | C12 | CENSORED | CENSORED | CENSORED | 35.333 | 51.333 | 5.333 | 35.667 |
| 75% | C15 | CENSORED | CENSORED | CENSORED | CENSORED | 177.333 | 8.667 | 317.333 |
| 75% | C16 | CENSORED | CENSORED | CENSORED | 34.000 | 32.667 | 17.000 | 29.000 |
| 75% | C18 | CENSORED | CENSORED | CENSORED | 149.333 | 118.667 | 13.000 | 112.667 |
| 75% | GCRIM | CENSORED | CENSORED | CENSORED | CENSORED | 67.000 | 13.000 | 106.667 |
| 80% | C12 | CENSORED | CENSORED | CENSORED | 171.667 | 40.000 | 9.667 | 53.000 |
| 80% | C15 | CENSORED | CENSORED | CENSORED | CENSORED | 257.333 | 5.000 | 179.667 |
| 80% | C16 | CENSORED | CENSORED | CENSORED | 25.333 | 24.667 | 8.000 | 22.000 |
| 80% | C18 | CENSORED | CENSORED | CENSORED | 237.333 | 117.333 | 12.333 | 170.000 |
| 80% | GCRIM | CENSORED | CENSORED | CENSORED | CENSORED | 49.000 | 9.667 | 114.667 |
| 90% | C12 | CENSORED | CENSORED | CENSORED | CENSORED | 77.333 | 15.000 | 62.333 |
| 90% | C15 | CENSORED | CENSORED | CENSORED | CENSORED | 211.333 | 16.000 | 162.000 |
| 90% | C16 | CENSORED | CENSORED | CENSORED | 133.000 | 133.000 | 8.000 | CENSORED |
| 90% | C18 | CENSORED | CENSORED | CENSORED | CENSORED | 139.667 | 4.667 | 129.000 |
| 90% | GCRIM | CENSORED | CENSORED | CENSORED | CENSORED | 146.667 | 8.333 | 140.000 |


### overshoot_at_75

Units: the named effort/depth metric.

| Pair | Mean | Exact sign-flip p | Percentile 95% | BCa 95% | C12 | C15 | C16 | C18 | GCRIM | Interval diagnostic |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| auto_tar − fixed_20 | 78.000000 | 0.0625 | [35.466667, 131.533333] | [39.733333, 134.243223] | 46.000000 | 168.666667 | 15.666667 | 105.666667 | 54.000000 | BELOW_DIAGNOSTIC_THRESHOLD |
| auto_tar − explore_10 | -30.866667 | 0.5 | [-88.800000, 9.400000] | [-99.866667, 7.000000] | 15.666667 | -140.000000 | 3.666667 | 6.000000 | -39.666667 | BELOW_DIAGNOSTIC_THRESHOLD |
| fixed_20 − explore_10 | -108.866667 | 0.0625 | [-211.200000, -33.200000] | [-249.333333, -40.533333] | -30.333333 | -308.666667 | -12.000000 | -99.666667 | -93.666667 | BELOW_DIAGNOSTIC_THRESHOLD |


### overshoot_at_80

Units: the named effort/depth metric.

| Pair | Mean | Exact sign-flip p | Percentile 95% | BCa 95% | C12 | C15 | C16 | C18 | GCRIM | Interval diagnostic |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| auto_tar − fixed_20 | 88.733333 | 0.0625 | [26.666667, 175.733333] | [33.000000, 205.200000] | 30.333333 | 252.333333 | 16.666667 | 105.000000 | 39.333333 | BELOW_DIAGNOSTIC_THRESHOLD |
| auto_tar − explore_10 | -10.200000 | 0.8125 | [-49.933333, 36.600000] | [-46.800000, 46.245686] | -13.000000 | 77.666667 | 2.666667 | -52.666667 | -65.666667 | BELOW_DIAGNOSTIC_THRESHOLD |
| fixed_20 − explore_10 | -98.933333 | 0.0625 | [-153.933333, -43.933333] | [-150.533333, -42.733333] | -43.333333 | -174.666667 | -14.000000 | -157.666667 | -105.000000 | BELOW_DIAGNOSTIC_THRESHOLD |


### overshoot_at_90

Units: the named effort/depth metric.

| Pair | Mean | Exact sign-flip p | Percentile 95% | BCa 95% | C12 | C15 | C16 | C18 | GCRIM | Interval diagnostic |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| auto_tar − fixed_20 | 131.200000 | 0.0625 | [91.400000, 169.866667] | [91.400000, 169.866667] | 62.333333 | 195.333333 | 125.000000 | 135.000000 | 138.333333 | BELOW_DIAGNOSTIC_THRESHOLD |

## Recall@R and the R+100 companion

Recall@R is fully observed: 0/105 runs and 0/21 policy pairs censored. Recall@(R+100) is also fully observed and is now a reported companion. On C16, R=49: each relevant document changes recall by 100/49 = 2.0408 percentage points. Adding 100 reviews provides a larger startup allowance at low prevalence; it does **not** change that per-document recall resolution or guarantee elimination of ties. Recall@R was selected AFTER outcomes; original recall@1000 remains visible.

AutoTAR minus explore_10 at recall@R is directionally consistent across every topic with a nonzero difference: four positive differences and the C16 tie. Magnitude is about 2 pp (+2.1639 pp), with both intervals excluding zero; the exact test is floored at p=0.125 by that tie. This is not a claim of equivalence or statistical significance.

## Seven-policy comparison

Means weight the five topics equally after averaging all three seeds within each topic. Historical policy names are retained in this Phase 1 reanalysis.


| method | recall_at_R | recall_at_1R_plus_100 | recall_at_1000 |
| --- | --- | --- | --- |
| random | 7.07% | 7.38% | 4.68% |
| seed_similarity | 26.62% | 28.97% | 27.24% |
| frozen_svm | 25.76% | 28.33% | 27.73% |
| uncertainty | 40.67% | 45.03% | 51.02% |
| auto_tar | 65.27% | 69.36% | 66.43% |
| fixed_20 | 64.64% | 70.42% | 66.40% |
| explore_10 | 63.11% | 67.29% | 64.26% |


Uncertainty sampling falls from 51.02% at recall@1000 to 40.67% at recall@R. Frozen SVM and seed similarity swap order: 27.73% versus 27.24% at recall@1000, but 25.76% versus 26.62% at recall@R. Their difference is not resolved by this five-topic study; "indistinguishable" here means no supported separation, not demonstrated equivalence.

## Inferential conventions

Each row is method_a minus method_b, averaging seeds before inference. Exact sign-flip is primary. With at most five nonzero topic differences, the minimum attainable two-sided p-value is 0.0625. Nonsignificance is not equivalence. Both 95% percentile and BCa intervals are sensitivity analyses: neither has trustworthy coverage established here. BCa reuses the same 10,000 topic-bootstrap draws. Material disagreement means different inclusion of zero or an endpoint shift of at least 25% of percentile width; this disclosed post-outcome diagnostic is not a validated threshold. Disagreement challenges interval inference; agreement does not validate it.

Recall differences and interval endpoints below are percentage points. Raw columns are the five seed-averaged paired topic differences, not individual-seed observations.



## Limitation: the 5,000-document budget censors deeper comparisons

The census includes every metric and all recall@4R cutoffs. Each target family includes exact effort, whole-batch effort, depth/N and depth/R. Pair-topic counts overlap. Any censored seed on either side withholds full-topic inference; no complete-case test or success-only effort mean substitutes for it.


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
| overshoot_at_75 | 43 | 105 | 18 | 21 | C12:6; C15:12; C16:7; C18:9; GCRIM:9 | C12:15; C15:18; C16:15; C18:15; GCRIM:18 |
| effort_at_80 | 46 | 105 | 18 | 21 | C12:7; C15:12; C16:8; C18:9; GCRIM:10 | C12:15; C15:18; C16:15; C18:15; GCRIM:18 |
| batch_effort_at_80 | 46 | 105 | 18 | 21 | C12:7; C15:12; C16:8; C18:9; GCRIM:10 | C12:15; C15:18; C16:15; C18:15; GCRIM:18 |
| depth_fraction_at_80 | 46 | 105 | 18 | 21 | C12:7; C15:12; C16:8; C18:9; GCRIM:10 | C12:15; C15:18; C16:15; C18:15; GCRIM:18 |
| depth_per_positive_at_80 | 46 | 105 | 18 | 21 | C12:7; C15:12; C16:8; C18:9; GCRIM:10 | C12:15; C15:18; C16:15; C18:15; GCRIM:18 |
| overshoot_at_80 | 46 | 105 | 18 | 21 | C12:7; C15:12; C16:8; C18:9; GCRIM:10 | C12:15; C15:18; C16:15; C18:15; GCRIM:18 |
| effort_at_90 | 58 | 105 | 20 | 21 | C12:12; C15:12; C16:10; C18:12; GCRIM:12 | C12:18; C15:18; C16:18; C18:18; GCRIM:18 |
| batch_effort_at_90 | 58 | 105 | 20 | 21 | C12:12; C15:12; C16:10; C18:12; GCRIM:12 | C12:18; C15:18; C16:18; C18:18; GCRIM:18 |
| depth_fraction_at_90 | 58 | 105 | 20 | 21 | C12:12; C15:12; C16:10; C18:12; GCRIM:12 | C12:18; C15:18; C16:18; C18:18; GCRIM:18 |
| depth_per_positive_at_90 | 58 | 105 | 20 | 21 | C12:12; C15:12; C16:10; C18:12; GCRIM:12 | C12:18; C15:18; C16:18; C18:18; GCRIM:18 |
| overshoot_at_90 | 58 | 105 | 20 | 21 | C12:12; C15:12; C16:10; C18:12; GCRIM:12 | C12:18; C15:18; C16:18; C18:18; GCRIM:18 |


C15 censors recall@2R; C18 additionally censors the 4R family, and GCRIM joins at 4R+1000. Target-effort comparisons are censored in 18/21 pairs at 75% and 80% recall, and 20/21 at 90%. The 5,000-document budget is too short for most full-topic comparisons at these targets. Partial recall means must name excluded topics; they are not the five-topic result.

## What this study can and cannot support

This study supports descriptive comparisons of seven fixed-label retrieval policies on these five RCV1-v2 topics under the original known-positive-seed, 5,000-review protocol, with fully observed recall@R and recall@1000 and transparent topic-level uncertainty. It does not establish superiority across legal matters, equivalence from nonsignificance, reliable bootstrap coverage from five topics, or complete deeper-target cost comparisons where observations are censored. It is a scoped reproduction, not an exact replication of the paper's result tables or independent validation against TARexp; it supplies no stopping certification, legal defensibility guarantee, or evidence about sales conversion. Seed discovery/search cost was excluded in the original plan, and the revised primary metric was chosen after outcomes.

Phase 2 was authorized subject to this Phase 1A review gate; it has not begun. The redundant pool/tail option is withdrawn; exploration-first global sampling remains deferred. After Phase 3 replay passes, Phase 3B must first report fit counts and wall-clock estimates for the combined census/schedule grid and wait for explicit approval before any run. Phase 4 cost rates must come from the user. No experiment.py invocation is permitted in Phase 1A or Phase 2. Figures are presentation artifacts; their size or cross-run identity is not a numerical gate. The execution receipt records completeness, numerical agreement and protected digests separately.



## Appendix: paired inference for recall and effort measures



### recall_at_R

Units: percentage points.

| Pair | Mean | Exact sign-flip p | Percentile 95% | BCa 95% | C12 | C15 | C16 | C18 | GCRIM | Interval diagnostic |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random − seed_similarity | -19.547696 | 0.125 | [-28.489586, -8.618331] | [-28.343023, -7.733030] | -24.934383 | -34.138949 | 0.000000 | -14.363885 | -24.301265 | BELOW_DIAGNOSTIC_THRESHOLD |
| random − frozen_svm | -18.689601 | 0.0625 | [-25.743447, -9.035111] | [-24.495456, -5.810472] | -26.421697 | -23.211295 | -0.680272 | -16.803466 | -26.331274 | BELOW_DIAGNOSTIC_THRESHOLD |
| random − uncertainty | -33.598194 | 0.0625 | [-43.971914, -22.184571] | [-43.953465, -22.166122] | -45.406824 | -20.938023 | -15.646259 | -43.046056 | -42.953810 | BELOW_DIAGNOSTIC_THRESHOLD |
| random − auto_tar | -58.203919 | 0.0625 | [-70.940065, -36.689733] | [-70.161443, -26.354448] | -63.429571 | -69.187206 | -15.646259 | -69.676243 | -73.080318 | MATERIAL |
| random − fixed_20 | -57.572879 | 0.0625 | [-71.879834, -32.918258] | [-71.117817, -21.128193] | -64.391951 | -71.101539 | -8.843537 | -69.858641 | -73.668726 | MATERIAL |
| random − explore_10 | -56.040001 | 0.0625 | [-67.983484, -35.716218] | [-67.174575, -25.898198] | -61.592301 | -66.905958 | -15.646259 | -66.005472 | -70.050015 | MATERIAL |
| seed_similarity − frozen_svm | 0.858096 | 1.0 | [-2.085299, 5.961667] | [-1.894845, 8.444660] | -1.487314 | 10.927654 | -0.680272 | -2.439580 | -2.030009 | MATERIAL |
| seed_similarity − uncertainty | -14.050498 | 0.125 | [-24.069063, 0.459537] | [-22.791096, 4.824306] | -20.472441 | 13.200925 | -15.646259 | -28.682171 | -18.652545 | BELOW_DIAGNOSTIC_THRESHOLD |
| seed_similarity − auto_tar | -38.656223 | 0.0625 | [-49.335602, -26.153217] | [-48.646215, -24.096444] | -38.495188 | -35.048257 | -15.646259 | -55.312358 | -48.779053 | BELOW_DIAGNOSTIC_THRESHOLD |
| seed_similarity − fixed_20 | -38.025183 | 0.0625 | [-50.562864, -22.572133] | [-48.610941, -20.091159] | -39.457568 | -36.962591 | -8.843537 | -55.494756 | -49.367461 | BELOW_DIAGNOSTIC_THRESHOLD |
| seed_similarity − explore_10 | -36.492304 | 0.0625 | [-46.688104, -25.090907] | [-45.509537, -23.272741] | -36.657918 | -32.767010 | -15.646259 | -51.641587 | -45.748750 | BELOW_DIAGNOSTIC_THRESHOLD |
| frozen_svm − uncertainty | -14.908594 | 0.125 | [-22.063259, -5.426260] | [-21.084284, -3.721059] | -18.985127 | 2.273271 | -14.965986 | -26.242590 | -16.622536 | BELOW_DIAGNOSTIC_THRESHOLD |
| frozen_svm − auto_tar | -39.514319 | 0.0625 | [-49.043911, -26.955722] | [-47.664537, -22.547345] | -37.007874 | -45.975911 | -14.965986 | -52.872777 | -46.749044 | BELOW_DIAGNOSTIC_THRESHOLD |
| frozen_svm − fixed_20 | -38.883278 | 0.0625 | [-49.845659, -23.103045] | [-48.591555, -15.998103] | -37.970254 | -47.890245 | -8.163265 | -53.055176 | -47.337452 | MATERIAL |
| frozen_svm − explore_10 | -37.350400 | 0.0625 | [-45.907232, -25.854114] | [-44.810579, -21.813190] | -35.170604 | -43.694664 | -14.965986 | -49.202006 | -43.718741 | BELOW_DIAGNOSTIC_THRESHOLD |
| uncertainty − auto_tar | -24.605725 | 0.125 | [-38.579360, -10.652075] | [-38.579360, -10.652075] | -18.022747 | -48.249182 | 0.000000 | -26.630187 | -30.126508 | BELOW_DIAGNOSTIC_THRESHOLD |
| uncertainty − fixed_20 | -23.974685 | 0.125 | [-39.257652, -6.643402] | [-39.257652, -5.858376] | -18.985127 | -50.163516 | 6.802721 | -26.812585 | -30.714916 | BELOW_DIAGNOSTIC_THRESHOLD |
| uncertainty − explore_10 | -22.441807 | 0.125 | [-36.237097, -9.193587] | [-36.237097, -9.711286] | -16.185477 | -45.967935 | 0.000000 | -22.959416 | -27.096205 | BELOW_DIAGNOSTIC_THRESHOLD |
| auto_tar − fixed_20 | 0.631040 | 1.0 | [-1.343161, 3.771475] | [-1.187165, 5.249701] | -0.962380 | -1.914334 | 6.802721 | -0.182399 | -0.588408 | MATERIAL |
| auto_tar − explore_10 | 2.163918 | 0.125 | [0.973515, 3.175977] | [0.823704, 3.047884] | 1.837270 | 2.281248 | 0.000000 | 3.670771 | 3.030303 | BELOW_DIAGNOSTIC_THRESHOLD |
| fixed_20 − explore_10 | 1.532878 | 0.5 | [-2.682586, 3.943242] | [-4.718435, 3.801021] | 2.799650 | 4.195581 | -6.802721 | 3.853169 | 3.618711 | MATERIAL |


### recall_at_1R_plus_100

Units: percentage points.

| Pair | Mean | Exact sign-flip p | Percentile 95% | BCa 95% | C12 | C15 | C16 | C18 | GCRIM | Interval diagnostic |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random − seed_similarity | -21.589712 | 0.0625 | [-29.941916, -13.022959] | [-29.455576, -11.334606] | -27.821522 | -34.338358 | -5.442177 | -14.956680 | -25.389821 | BELOW_DIAGNOSTIC_THRESHOLD |
| random − frozen_svm | -20.946218 | 0.0625 | [-27.202730, -13.757748] | [-26.289015, -12.675132] | -28.783902 | -23.370822 | -7.482993 | -17.555860 | -27.537511 | BELOW_DIAGNOSTIC_THRESHOLD |
| random − uncertainty | -37.649062 | 0.0625 | [-48.650128, -26.407739] | [-48.476069, -26.233679] | -53.455818 | -21.057669 | -23.129252 | -45.736434 | -44.866137 | BELOW_DIAGNOSTIC_THRESHOLD |
| random − auto_tar | -61.974254 | 0.0625 | [-73.450737, -41.798350] | [-72.706795, -32.354989] | -70.078740 | -69.665789 | -22.448980 | -71.979024 | -75.698735 | MATERIAL |
| random − fixed_20 | -63.032668 | 0.0625 | [-74.245073, -43.034178] | [-73.733260, -34.287395] | -71.216098 | -71.412619 | -23.809524 | -72.526220 | -76.198882 | MATERIAL |
| random − explore_10 | -59.909455 | 0.0625 | [-70.822294, -40.835967] | [-70.005403, -31.642473] | -68.416448 | -67.336683 | -22.448980 | -68.559052 | -72.786114 | MATERIAL |
| seed_similarity − frozen_svm | 0.643494 | 1.0 | [-2.306911, 5.868210] | [-2.173864, 8.365866] | -0.962380 | 10.967536 | -2.040816 | -2.599179 | -2.147690 | MATERIAL |
| seed_similarity − uncertainty | -16.059350 | 0.125 | [-27.132126, -0.695861] | [-25.542682, 4.468601] | -25.634296 | 13.280689 | -17.687075 | -30.779754 | -19.476317 | MATERIAL |
| seed_similarity − auto_tar | -40.384542 | 0.0625 | [-51.383947, -27.331351] | [-49.997989, -25.721011] | -42.257218 | -35.327431 | -17.006803 | -57.022344 | -50.308914 | BELOW_DIAGNOSTIC_THRESHOLD |
| seed_similarity − fixed_20 | -41.442957 | 0.0625 | [-52.118388, -28.597072] | [-51.899554, -27.114175] | -43.394576 | -37.074260 | -18.367347 | -57.569539 | -50.809061 | BELOW_DIAGNOSTIC_THRESHOLD |
| seed_similarity − explore_10 | -38.319744 | 0.0625 | [-48.518451, -26.442052] | [-47.277235, -24.922732] | -40.594926 | -32.998325 | -17.006803 | -53.602371 | -47.396293 | BELOW_DIAGNOSTIC_THRESHOLD |
| frozen_svm − uncertainty | -16.702844 | 0.125 | [-24.971980, -6.675743] | [-23.904990, -5.207085] | -24.671916 | 2.313153 | -15.646259 | -28.180575 | -17.328626 | BELOW_DIAGNOSTIC_THRESHOLD |
| frozen_svm − auto_tar | -41.028036 | 0.0625 | [-50.545111, -27.497579] | [-49.292723, -21.605034] | -41.294838 | -46.294967 | -14.965986 | -54.423165 | -48.161224 | MATERIAL |
| frozen_svm − fixed_20 | -42.086451 | 0.0625 | [-51.184967, -29.136552] | [-49.939132, -24.055297] | -42.432196 | -48.041796 | -16.326531 | -54.970360 | -48.661371 | BELOW_DIAGNOSTIC_THRESHOLD |
| frozen_svm − explore_10 | -38.963238 | 0.0625 | [-47.550438, -26.822485] | [-46.427227, -21.022510] | -39.632546 | -43.965861 | -14.965986 | -51.003192 | -45.248603 | MATERIAL |
| uncertainty − auto_tar | -24.325192 | 0.125 | [-37.942807, -9.701644] | [-37.942807, -9.701644] | -16.622922 | -48.608120 | 0.680272 | -26.242590 | -30.832598 | BELOW_DIAGNOSTIC_THRESHOLD |
| uncertainty − fixed_20 | -25.383606 | 0.0625 | [-39.122983, -11.124078] | [-38.941627, -10.615208] | -17.760280 | -50.354949 | -0.680272 | -26.789786 | -31.332745 | BELOW_DIAGNOSTIC_THRESHOLD |
| uncertainty − explore_10 | -22.260393 | 0.125 | [-36.343530, -8.167958] | [-36.343530, -8.720884] | -14.960630 | -46.279014 | 0.680272 | -22.822617 | -27.919976 | BELOW_DIAGNOSTIC_THRESHOLD |
| auto_tar − fixed_20 | -1.058415 | 0.0625 | [-1.470421, -0.646409] | [-1.503041, -0.655818] | -1.137358 | -1.746829 | -1.360544 | -0.547196 | -0.500147 | BELOW_DIAGNOSTIC_THRESHOLD |
| auto_tar − explore_10 | 2.064798 | 0.125 | [0.997375, 2.998859] | [0.798280, 2.897389] | 1.662292 | 2.329106 | 0.000000 | 3.419973 | 2.912621 | BELOW_DIAGNOSTIC_THRESHOLD |
| fixed_20 − explore_10 | 3.123213 | 0.0625 | [2.181434, 3.899795] | [1.936187, 3.788915] | 2.799650 | 4.075935 | 1.360544 | 3.967168 | 3.412768 | BELOW_DIAGNOSTIC_THRESHOLD |


### recall_at_1000

Units: percentage points.

| Pair | Mean | Exact sign-flip p | Percentile 95% | BCa 95% | C12 | C15 | C16 | C18 | GCRIM | Interval diagnostic |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random − seed_similarity | -22.561121 | 0.0625 | [-30.510124, -14.816350] | [-31.406504, -15.327635] | -37.182852 | -13.791178 | -27.210884 | -11.878705 | -22.741983 | BELOW_DIAGNOSTIC_THRESHOLD |
| random − frozen_svm | -23.046709 | 0.0625 | [-31.908375, -14.556524] | [-34.074426, -15.096708] | -39.807524 | -10.887772 | -26.530612 | -13.588691 | -24.418947 | BELOW_DIAGNOSTIC_THRESHOLD |
| random − uncertainty | -46.342709 | 0.0625 | [-70.614268, -23.577459] | [-70.614268, -23.577459] | -69.116360 | -8.750100 | -84.353741 | -30.893753 | -38.599588 | BELOW_DIAGNOSTIC_THRESHOLD |
| random − auto_tar | -61.751394 | 0.0625 | [-80.935723, -38.958798] | [-77.913337, -32.789431] | -83.902012 | -19.278934 | -84.353741 | -53.055176 | -68.167108 | BELOW_DIAGNOSTIC_THRESHOLD |
| random − fixed_20 | -61.723781 | 0.0625 | [-80.815365, -39.026757] | [-77.822250, -32.828438] | -84.251969 | -19.207147 | -83.673469 | -53.260374 | -68.225949 | BELOW_DIAGNOSTIC_THRESHOLD |
| random − explore_10 | -59.584088 | 0.0625 | [-79.554585, -36.963604] | [-77.056586, -33.085762] | -83.202100 | -17.532105 | -84.353741 | -49.019608 | -63.812886 | BELOW_DIAGNOSTIC_THRESHOLD |
| seed_similarity − frozen_svm | -0.485589 | 0.6875 | [-2.069256, 1.536101] | [-1.958301, 1.569526] | -2.624672 | 2.903406 | 0.680272 | -1.709986 | -1.676964 | BELOW_DIAGNOSTIC_THRESHOLD |
| seed_similarity − uncertainty | -23.781588 | 0.125 | [-42.017248, -7.165064] | [-43.843937, -8.129620] | -31.933508 | 5.041078 | -57.142857 | -19.015048 | -15.857605 | BELOW_DIAGNOSTIC_THRESHOLD |
| seed_similarity − auto_tar | -39.190274 | 0.0625 | [-51.606033, -20.871780] | [-49.780101, -13.734037] | -46.719160 | -5.487756 | -57.142857 | -41.176471 | -45.425125 | BELOW_DIAGNOSTIC_THRESHOLD |
| seed_similarity − fixed_20 | -39.162661 | 0.0625 | [-51.250678, -21.443168] | [-49.689014, -13.746598] | -47.069116 | -5.415969 | -56.462585 | -41.381669 | -45.483966 | MATERIAL |
| seed_similarity − explore_10 | -37.022968 | 0.0625 | [-50.468691, -18.876586] | [-48.693022, -17.100917] | -46.019248 | -3.740927 | -57.142857 | -37.140903 | -41.070903 | BELOW_DIAGNOSTIC_THRESHOLD |
| frozen_svm − uncertainty | -23.295999 | 0.125 | [-40.991018, -7.653316] | [-44.016657, -8.903084] | -29.308836 | 2.137672 | -57.823129 | -17.305062 | -14.180641 | BELOW_DIAGNOSTIC_THRESHOLD |
| frozen_svm − auto_tar | -38.704685 | 0.0625 | [-51.336807, -22.533962] | [-49.447414, -20.821291] | -44.094488 | -8.391162 | -57.823129 | -39.466484 | -43.748161 | BELOW_DIAGNOSTIC_THRESHOLD |
| frozen_svm − fixed_20 | -38.677072 | 0.0625 | [-51.108940, -22.641914] | [-49.268833, -20.860298] | -44.444444 | -8.319375 | -57.142857 | -39.671683 | -43.807002 | BELOW_DIAGNOSTIC_THRESHOLD |
| frozen_svm − explore_10 | -36.537379 | 0.0625 | [-49.658849, -19.751698] | [-48.365870, -18.951571] | -43.394576 | -6.644333 | -57.823129 | -35.430917 | -39.393939 | BELOW_DIAGNOSTIC_THRESHOLD |
| uncertainty − auto_tar | -15.408686 | 0.125 | [-23.654773, -6.538051] | [-23.654773, -6.538051] | -14.785652 | -10.528835 | 0.000000 | -22.161423 | -29.567520 | BELOW_DIAGNOSTIC_THRESHOLD |
| uncertainty − fixed_20 | -15.381073 | 0.125 | [-24.340550, -6.156570] | [-23.824314, -6.002119] | -15.135608 | -10.457047 | 0.680272 | -22.366621 | -29.626361 | BELOW_DIAGNOSTIC_THRESHOLD |
| uncertainty − explore_10 | -13.241380 | 0.125 | [-20.509551, -5.381572] | [-20.152809, -5.269203] | -14.085739 | -8.782005 | 0.000000 | -18.125855 | -25.213298 | BELOW_DIAGNOSTIC_THRESHOLD |
| auto_tar − fixed_20 | 0.027613 | 0.875 | [-0.236656, 0.381481] | [-0.204559, 0.503178] | -0.349956 | 0.071788 | 0.680272 | -0.205198 | -0.058841 | BELOW_DIAGNOSTIC_THRESHOLD |
| auto_tar − explore_10 | 2.167306 | 0.125 | [0.629331, 3.705282] | [0.769313, 3.705282] | 0.699913 | 1.746829 | 0.000000 | 4.035568 | 4.354222 | BELOW_DIAGNOSTIC_THRESHOLD |
| fixed_20 − explore_10 | 2.139693 | 0.125 | [0.482847, 3.796540] | [0.357812, 3.762081] | 1.049869 | 1.675042 | -0.680272 | 4.240766 | 4.413063 | BELOW_DIAGNOSTIC_THRESHOLD |


### batch_effort_at_75

Units: the named effort/depth metric.

| Pair | Mean | Exact sign-flip p | Percentile 95% | BCa 95% | C12 | C15 | C16 | C18 | GCRIM | Interval diagnostic |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| auto_tar − fixed_20 | 97.600000 | 0.125 | [30.600000, 173.800000] | [34.266667, 186.000000] | 76.666667 | 244.666667 | -11.000000 | 119.333333 | 58.333333 | BELOW_DIAGNOSTIC_THRESHOLD |
| auto_tar − explore_10 | -125.466667 | 0.125 | [-250.000000, -30.266667] | [-271.600000, -36.800000] | 0.000000 | -368.000000 | -19.000000 | -113.333333 | -127.000000 | BELOW_DIAGNOSTIC_THRESHOLD |
| fixed_20 − explore_10 | -223.066667 | 0.0625 | [-429.466667, -66.666667] | [-460.666667, -84.666667] | -76.666667 | -612.666667 | -8.000000 | -232.666667 | -185.333333 | BELOW_DIAGNOSTIC_THRESHOLD |


### batch_effort_at_80

Units: the named effort/depth metric.

| Pair | Mean | Exact sign-flip p | Percentile 95% | BCa 95% | C12 | C15 | C16 | C18 | GCRIM | Interval diagnostic |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| auto_tar − fixed_20 | 132.733333 | 0.0625 | [53.266667, 251.866667] | [60.933333, 294.914293] | 94.666667 | 359.333333 | 28.333333 | 122.666667 | 58.666667 | BELOW_DIAGNOSTIC_THRESHOLD |
| auto_tar − explore_10 | -94.800000 | 0.125 | [-157.800000, -24.933333] | [-156.800000, -23.933333] | -25.666667 | -135.000000 | 13.666667 | -187.000000 | -140.000000 | BELOW_DIAGNOSTIC_THRESHOLD |
| fixed_20 − explore_10 | -227.533333 | 0.0625 | [-376.066667, -93.733333] | [-383.533333, -109.400000] | -120.333333 | -494.333333 | -14.666667 | -309.666667 | -198.666667 | BELOW_DIAGNOSTIC_THRESHOLD |


### batch_effort_at_90

Units: the named effort/depth metric.

| Pair | Mean | Exact sign-flip p | Percentile 95% | BCa 95% | C12 | C15 | C16 | C18 | GCRIM | Interval diagnostic |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| auto_tar − fixed_20 | 193.933333 | 0.0625 | [107.800000, 302.333333] | [115.466667, 314.866667] | 67.333333 | 397.000000 | 122.000000 | 160.333333 | 223.000000 | BELOW_DIAGNOSTIC_THRESHOLD |


### depth_fraction_at_75

Units: the named effort/depth metric.

| Pair | Mean | Exact sign-flip p | Percentile 95% | BCa 95% | C12 | C15 | C16 | C18 | GCRIM | Interval diagnostic |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| auto_tar − fixed_20 | 0.000847 | 0.3125 | [-0.000389, 0.002206] | [-0.000308, 0.002272] | 0.001325 | 0.003283 | -0.001152 | 0.000590 | 0.000187 | BELOW_DIAGNOSTIC_THRESHOLD |
| auto_tar − explore_10 | -0.004087 | 0.0625 | [-0.007136, -0.001417] | [-0.007972, -0.001754] | -0.000677 | -0.009849 | -0.000979 | -0.005155 | -0.003773 | BELOW_DIAGNOSTIC_THRESHOLD |
| fixed_20 − explore_10 | -0.004933 | 0.125 | [-0.009429, -0.001480] | [-0.009820, -0.001881] | -0.002002 | -0.013132 | 0.000173 | -0.005745 | -0.003960 | BELOW_DIAGNOSTIC_THRESHOLD |


### depth_fraction_at_80

Units: the named effort/depth metric.

| Pair | Mean | Exact sign-flip p | Percentile 95% | BCa 95% | C12 | C15 | C16 | C18 | GCRIM | Interval diagnostic |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| auto_tar − fixed_20 | 0.001901 | 0.0625 | [0.000674, 0.003482] | [0.000726, 0.003799] | 0.002779 | 0.004622 | 0.000504 | 0.000763 | 0.000835 | BELOW_DIAGNOSTIC_THRESHOLD |
| auto_tar − explore_10 | -0.003655 | 0.125 | [-0.006797, -0.000671] | [-0.007254, -0.000875] | -0.000547 | -0.009187 | 0.000475 | -0.005803 | -0.003211 | BELOW_DIAGNOSTIC_THRESHOLD |
| fixed_20 − explore_10 | -0.005555 | 0.0625 | [-0.010264, -0.002007] | [-0.010912, -0.002295] | -0.003326 | -0.013809 | -0.000029 | -0.006566 | -0.004046 | BELOW_DIAGNOSTIC_THRESHOLD |


### depth_fraction_at_90

Units: the named effort/depth metric.

| Pair | Mean | Exact sign-flip p | Percentile 95% | BCa 95% | C12 | C15 | C16 | C18 | GCRIM | Interval diagnostic |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| auto_tar − fixed_20 | 0.002710 | 0.125 | [0.000253, 0.005933] | [0.000605, 0.006943] | 0.000216 | 0.008712 | -0.000130 | 0.001094 | 0.003657 | BELOW_DIAGNOSTIC_THRESHOLD |


### depth_per_positive_at_75

Units: the named effort/depth metric.

| Pair | Mean | Exact sign-flip p | Percentile 95% | BCa 95% | C12 | C15 | C16 | C18 | GCRIM | Interval diagnostic |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| auto_tar − fixed_20 | -0.086474 | 1.0 | [-0.322128, 0.050928] | [-0.431737, 0.039572] | 0.080490 | 0.018186 | -0.544218 | 0.009348 | 0.003825 | MATERIAL |
| auto_tar − explore_10 | -0.143394 | 0.0625 | [-0.303879, -0.051908] | [-0.380980, -0.058192] | -0.041120 | -0.054559 | -0.462585 | -0.081623 | -0.077081 | MATERIAL |
| fixed_20 − explore_10 | -0.056920 | 0.25 | [-0.103696, 0.014645] | [-0.099201, 0.047112] | -0.121610 | -0.072745 | 0.081633 | -0.090971 | -0.080906 | MATERIAL |


### depth_per_positive_at_80

Units: the named effort/depth metric.

| Pair | Mean | Exact sign-flip p | Percentile 95% | BCa 95% | C12 | C15 | C16 | C18 | GCRIM | Interval diagnostic |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| auto_tar − fixed_20 | 0.092340 | 0.0625 | [0.016780, 0.180041] | [0.018488, 0.182702] | 0.168854 | 0.025604 | 0.238095 | 0.012084 | 0.017064 | BELOW_DIAGNOSTIC_THRESHOLD |
| auto_tar − explore_10 | -0.003427 | 1.0 | [-0.074901, 0.114923] | [-0.067919, 0.166470] | -0.033246 | -0.050889 | 0.224490 | -0.091883 | -0.065608 | MATERIAL |
| fixed_20 − explore_10 | -0.095767 | 0.0625 | [-0.154328, -0.045491] | [-0.162847, -0.053809] | -0.202100 | -0.076494 | -0.013605 | -0.103967 | -0.082671 | BELOW_DIAGNOSTIC_THRESHOLD |


### depth_per_positive_at_90

Units: the named effort/depth metric.

| Pair | Mean | Exact sign-flip p | Percentile 95% | BCa 95% | C12 | C15 | C16 | C18 | GCRIM | Interval diagnostic |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| auto_tar − fixed_20 | 0.018442 | 0.375 | [-0.023618, 0.057113] | [-0.030644, 0.050927] | 0.013123 | 0.048257 | -0.061224 | 0.017328 | 0.074728 | BELOW_DIAGNOSTIC_THRESHOLD |


### effort_at_75

Units: the named effort/depth metric.

| Pair | Mean | Exact sign-flip p | Percentile 95% | BCa 95% | C12 | C15 | C16 | C18 | GCRIM | Interval diagnostic |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| auto_tar − fixed_20 | 19.600000 | 0.3125 | [-8.066667, 51.066667] | [-6.200000, 52.600000] | 30.666667 | 76.000000 | -26.666667 | 13.666667 | 4.333333 | BELOW_DIAGNOSTIC_THRESHOLD |
| auto_tar − explore_10 | -94.600000 | 0.0625 | [-165.200000, -32.800000] | [-178.133333, -37.800000] | -15.666667 | -228.000000 | -22.666667 | -119.333333 | -87.333333 | BELOW_DIAGNOSTIC_THRESHOLD |
| fixed_20 − explore_10 | -114.200000 | 0.125 | [-210.000000, -34.266667] | [-227.333333, -43.533333] | -46.333333 | -304.000000 | 4.000000 | -133.000000 | -91.666667 | BELOW_DIAGNOSTIC_THRESHOLD |


### effort_at_80

Units: the named effort/depth metric.

| Pair | Mean | Exact sign-flip p | Percentile 95% | BCa 95% | C12 | C15 | C16 | C18 | GCRIM | Interval diagnostic |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| auto_tar − fixed_20 | 44.000000 | 0.0625 | [15.600000, 80.600000] | [15.933333, 80.933333] | 64.333333 | 107.000000 | 11.666667 | 17.666667 | 19.333333 | BELOW_DIAGNOSTIC_THRESHOLD |
| auto_tar − explore_10 | -84.600000 | 0.125 | [-157.000000, -15.533333] | [-167.933333, -20.266667] | -12.666667 | -212.666667 | 11.000000 | -134.333333 | -74.333333 | BELOW_DIAGNOSTIC_THRESHOLD |
| fixed_20 − explore_10 | -128.600000 | 0.0625 | [-225.933333, -46.200000] | [-252.600000, -53.133333] | -77.000000 | -319.666667 | -0.666667 | -152.000000 | -93.666667 | BELOW_DIAGNOSTIC_THRESHOLD |


### effort_at_90

Units: the named effort/depth metric.

| Pair | Mean | Exact sign-flip p | Percentile 95% | BCa 95% | C12 | C15 | C16 | C18 | GCRIM | Interval diagnostic |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| auto_tar − fixed_20 | 62.733333 | 0.125 | [5.866667, 137.333333] | [16.133333, 166.400000] | 5.000000 | 201.666667 | -3.000000 | 25.333333 | 84.666667 | BELOW_DIAGNOSTIC_THRESHOLD |


### recall_at_1R_plus_0

Units: percentage points.

| Pair | Mean | Exact sign-flip p | Percentile 95% | BCa 95% | C12 | C15 | C16 | C18 | GCRIM | Interval diagnostic |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random − seed_similarity | -19.547696 | 0.125 | [-28.489586, -9.700567] | [-28.343023, -7.733030] | -24.934383 | -34.138949 | 0.000000 | -14.363885 | -24.301265 | BELOW_DIAGNOSTIC_THRESHOLD |
| random − frozen_svm | -18.689601 | 0.0625 | [-25.743447, -9.053196] | [-24.479966, -5.810472] | -26.421697 | -23.211295 | -0.680272 | -16.803466 | -26.331274 | BELOW_DIAGNOSTIC_THRESHOLD |
| random − uncertainty | -33.598194 | 0.0625 | [-43.971914, -22.184571] | [-43.953465, -22.166122] | -45.406824 | -20.938023 | -15.646259 | -43.046056 | -42.953810 | BELOW_DIAGNOSTIC_THRESHOLD |
| random − auto_tar | -58.203919 | 0.0625 | [-70.940065, -36.689733] | [-70.063636, -26.452255] | -63.429571 | -69.187206 | -15.646259 | -69.676243 | -73.080318 | MATERIAL |
| random − fixed_20 | -57.572879 | 0.0625 | [-71.879834, -32.918258] | [-71.117817, -21.046558] | -64.391951 | -71.101539 | -8.843537 | -69.858641 | -73.668726 | MATERIAL |
| random − explore_10 | -56.040001 | 0.0625 | [-67.983484, -35.716218] | [-67.174575, -25.898198] | -61.592301 | -66.905958 | -15.646259 | -66.005472 | -70.050015 | MATERIAL |
| seed_similarity − frozen_svm | 0.858096 | 1.0 | [-2.085299, 6.014536] | [-1.894845, 8.444660] | -1.487314 | 10.927654 | -0.680272 | -2.439580 | -2.030009 | MATERIAL |
| seed_similarity − uncertainty | -14.050498 | 0.125 | [-24.433042, 0.459537] | [-22.791096, 4.824306] | -20.472441 | 13.200925 | -15.646259 | -28.682171 | -18.652545 | BELOW_DIAGNOSTIC_THRESHOLD |
| seed_similarity − auto_tar | -38.656223 | 0.0625 | [-49.952876, -26.153217] | [-48.646215, -24.096444] | -38.495188 | -35.048257 | -15.646259 | -55.312358 | -48.779053 | BELOW_DIAGNOSTIC_THRESHOLD |
| seed_similarity − fixed_20 | -38.025183 | 0.0625 | [-50.562864, -23.071128] | [-48.610941, -20.091159] | -39.457568 | -36.962591 | -8.843537 | -55.494756 | -49.367461 | BELOW_DIAGNOSTIC_THRESHOLD |
| seed_similarity − explore_10 | -36.492304 | 0.0625 | [-46.688104, -25.849634] | [-45.748750, -23.272741] | -36.657918 | -32.767010 | -15.646259 | -51.641587 | -45.748750 | BELOW_DIAGNOSTIC_THRESHOLD |
| frozen_svm − uncertainty | -14.908594 | 0.125 | [-22.394568, -5.426260] | [-21.084284, -4.622432] | -18.985127 | 2.273271 | -14.965986 | -26.242590 | -16.622536 | BELOW_DIAGNOSTIC_THRESHOLD |
| frozen_svm − auto_tar | -39.514319 | 0.0625 | [-49.043911, -26.955722] | [-47.819164, -22.547345] | -37.007874 | -45.975911 | -14.965986 | -52.872777 | -46.749044 | BELOW_DIAGNOSTIC_THRESHOLD |
| frozen_svm − fixed_20 | -38.883278 | 0.0625 | [-49.845659, -23.103045] | [-48.591555, -16.108661] | -37.970254 | -47.890245 | -8.163265 | -53.055176 | -47.337452 | MATERIAL |
| frozen_svm − explore_10 | -37.350400 | 0.0625 | [-45.907232, -25.854114] | [-44.805763, -20.716537] | -35.170604 | -43.694664 | -14.965986 | -49.202006 | -43.718741 | MATERIAL |
| uncertainty − auto_tar | -24.605725 | 0.125 | [-38.579360, -10.652075] | [-38.579360, -9.649836] | -18.022747 | -48.249182 | 0.000000 | -26.630187 | -30.126508 | BELOW_DIAGNOSTIC_THRESHOLD |
| uncertainty − fixed_20 | -23.974685 | 0.125 | [-39.257652, -7.423868] | [-39.257652, -6.643402] | -18.985127 | -50.163516 | 6.802721 | -26.812585 | -30.714916 | BELOW_DIAGNOSTIC_THRESHOLD |
| uncertainty − explore_10 | -22.441807 | 0.125 | [-36.237097, -9.193587] | [-36.237097, -9.711286] | -16.185477 | -45.967935 | 0.000000 | -22.959416 | -27.096205 | BELOW_DIAGNOSTIC_THRESHOLD |
| auto_tar − fixed_20 | 0.631040 | 1.0 | [-1.377556, 3.771475] | [-1.187165, 5.059310] | -0.962380 | -1.914334 | 6.802721 | -0.182399 | -0.588408 | MATERIAL |
| auto_tar − explore_10 | 2.163918 | 0.125 | [0.973515, 3.136679] | [0.823704, 3.047884] | 1.837270 | 2.281248 | 0.000000 | 3.670771 | 3.030303 | BELOW_DIAGNOSTIC_THRESHOLD |
| fixed_20 − explore_10 | 1.532878 | 0.5 | [-2.751069, 3.943242] | [-4.718435, 3.806278] | 2.799650 | 4.195581 | -6.802721 | 3.853169 | 3.618711 | MATERIAL |
