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
