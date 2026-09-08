# What was reproduced, and what was changed

Paper: Gordon V. Cormack and Maura R. Grossman, *Autonomy and Reliability of Continuous Active Learning for Technology-Assisted Review* (2015), [arXiv:1504.06868](https://arxiv.org/abs/1504.06868). The methodological reference is section 3.1; the numerical reference below is Table II.

The reference loop starts with a relevant seed, adds 100 temporary presumed negatives, fits an SVM and reviews the highest-scoring batch. It incorporates the judgments, discards temporary labels and repeats with batches growing by the ceiling of one tenth of their current size. The study evaluates legal tasks and broader retrieval benchmarks.

| Component | This project | Reproduction status |
|---|---|---|
| Feedback loop and growing batches | Start at one; retrain after each batch | Preserved |
| Random relevant seed | Same seed across compared methods | Preserved in spirit; search cost excluded |
| Temporary negatives | Sample 100 unreviewed rows afresh per fit | Modified: excludes reviewed rows |
| Classifier | scikit-learn LinearSVC, hinge loss, C=1 | SVMlight replaced; solver/intercept differ |
| Representation | Pre-stemmed tokens, min document frequency 2, Cornell ltc weights fit on this pool | Similar family; subset vocabulary and IDF differ |
| Collection | 23,149 RCV1-v2 training-partition rows; five topics | Smaller scope than full study |
| Controls | Random, seed similarity, frozen SVM and iterative uncertainty | Local controls, not the paper's SAL/SPL implementations |
| Stopping | Fixed 5,000-review budget | No deployed completeness or stopping claim |

The paper reports these 75% recall effort counts for its legal development tasks:

| TREC topic | Paper CAL | Paper Auto TAR, random seed | Reduction from paper CAL |
|---|---:|---:|---:|
| 201 | 3,400 | 2,400 | 29.4% |
| 202 | 9,100 | 8,000 | 12.1% |
| 203 | 4,800 | 4,300 | 10.4% |
| 207 | 9,400 | 8,000 | 14.9% |

Those are published values, not our measurements. The reductions are calculations from Table II: `(CAL - Auto TAR) / CAL`. Our RCV1 subset has different topics, size, prevalence and controls; placing its effort counts against this table does not provide a replication error or a valid numerical superiority comparison. We reproduce the core protocol and test whether its behavior carries into a smaller benchmark. Exact replication of the published numbers remains uncompleted.

## Additional experiments

`fixed_20` holds the review batch at 20. It tests whether more frequent feedback is worth the additional training. `explore_10` spends 10% of sufficiently large batches on random unexplored documents. It tests whether broader exploration compensates for reading fewer high-ranked documents. Both were specified in `experiment_plan.json` before model outcomes were examined. Negative results are retained.

The operational BDR queue is a separate adaptation: it trains a class-balanced SVM using confirmed positive and negative judgments. It does not use temporary negatives. During a smoke test on a tiny fictional queue, labeling nearly the whole unseen pool temporarily negative made margins collapse near -1; using confirmed labels avoids that specific bootstrap behavior. This change has not been validated on actual IST outcomes.

## Sources

- [Selected Auto TAR paper](https://arxiv.org/abs/1504.06868)
- [RCV1 benchmark paper](https://jmlr.org/papers/v5/lewis04a.html)
- [LIBSVM RCV1 data and preprocessing description](https://www.csie.ntu.edu.tw/~cjlin/libsvmtools/datasets/multilabel.html)
- [LinearSVC documentation](https://scikit-learn.org/stable/modules/generated/sklearn.svm.LinearSVC.html)


## Measured solver-budget divergence (post-outcome diagnostic)

The substituted LinearSVC dual solver reached its 10,000-iteration limit in eight archived v1 fits, all in C15, within the original 5,000-review budget. This is not a census-depth-only phenomenon. Refit counts ranged from 10,190 to 20,005 under identical archived training rows, labels, temporary negatives and model parameters except the diagnostic ceiling. A reconstruction of the failed census C15/11/uncertainty trajectory reached its first warning at fit 47; that fit required 10,959 iterations with a high ceiling. No saved failure-round state existed to independently authenticate the ninth fit's identity.

Production max_iter is now 41,000, using the recorded ceil(2*observed_max/1000)*1000 headroom rule. C=1, hinge loss, dual=True and tol=1e-4 remain unchanged. This changes the available optimization work, not the stated objective or review policy. It can affect rankings where earlier optimization was incomplete; fit-209's separately measured zero downstream selection effect is not generalized to other failures. Permanent per-fit convergence/iteration/warning records make the substitution's numerical behavior reviewable. The concentration in C15 and varying training sets suggest a composition-related issue but do not isolate prevalence as the cause. Mac-native solver behavior is a further environment change that will be logged, not assumed bitwise identical.

Complete observations: diagnostics/iteration_requirements_v2/report.json and post_exit_verification.json. No new census outcome or Phase 4 conclusion is claimed here.
