# Build the project in eight understandable tasks

This project was built with AI assistance. Use these tasks to understand, change and defend it yourself before presenting it as your portfolio work. Estimated learning times below are planning estimates, not measured implementation times.

| Task | What you do | Finished when | File to study | Learning time |
|---|---|---|---|---|
| 1. Define the decision | Explain what makes one item relevant; distinguish topic relevance from buying intent. | You can label five borderline examples consistently. | `docs/IST_PLAYBOOK.md` | 45-60 min |
| 2. Read the paper | Read the abstract, section 3.1 and Table II. Write the review loop in your own words. | You can explain how feedback changes the next batch. | `docs/PAPER_COMPARISON.md` | 60-90 min |
| 3. Represent text | Inspect the log-frequency, inverse-frequency and normalization calculation. | You can explain why common words receive less weight. | `src/data.py` | 60-90 min |
| 4. Build three simple controls | Run random review, similarity to the seed, and a frozen SVM. | You can explain what each control isolates. | `src/learner.py` | 90 min |
| 5. Implement the learning loop | Trace query, reveal labels, retrain, repeat. | You can show that hidden labels never reach the learner. | `src/experiment.py` | 2-3 hr |
| 6. Measure fairly | Calculate recall, precision, review effort and censoring by hand. | Your calculation agrees with one audit file. | `src/metrics.py`, `src/verify_results.py` | 90 min |
| 7. Change one thing | Compare 20-item batches and 10% exploration with the unchanged method. | You retain the losses as well as the wins. | `experiment_plan.json` | 2 hr |
| 8. Transfer carefully | Label real public matter signals and evaluate on later dates and different accounts. | You have a dated, independently judged test set. | `src/bdr_queue.py` | 2-4 weeks for a meaningful pilot |

## The method in plain English

Imagine a pile of 23,149 cards. Only some cards concern the topic you want. Someone gives you one known useful card. You use its words to start a ranking. You read the top cards and mark each useful or not useful. The program trains again on these judgments and changes the order of the unread cards. That feedback loop is continuous active learning.

The classifier here is a linear support vector machine, or SVM. Each word has a learned weight. A document's ranking score is the weighted sum of its word features plus an intercept. The training procedure adjusts weights to separate reviewed relevant and non-relevant examples while discouraging unnecessarily large weights. It minimizes a hinge-loss objective with regularization. You do not need a neural network or a paid language-model API to do this.

In the benchmark, the initial single positive example is supplemented with temporary assumed-negative examples to make initial training possible. These assumptions are discarded after each fit. They never become real reviewer labels. The program can later review one of them and learn that it is actually positive.

The fixed collection can be vectorized before review because reading the words does not reveal the relevance labels. This is a transductive review experiment: we measure how efficiently the system discovers labels in an existing pool. We are not reporting accuracy on future documents. A future-document classifier would need a separate held-out evaluation.

## One calculation to understand

Suppose a collection contains 100 relevant documents. After reviewing 200 documents you found 75 relevant ones. Precision is 75 / 200 = 37.5%. Recall is 75 / 100 = 75%. Your 75% recall effort is 200 documents. You know the denominator of recall only because this is an offline benchmark with complete topic labels. In your real prospect queue, you do not know the total number of useful items until you independently judge or sample the remaining pool.

If the collection has 1,000 documents, work saved over random sampling at 75% recall is approximately 0.75 - 200 / 1,000 = 0.55, or 55 percentage points. It is not automatically an estimate of money saved, and it does not account for different reading times.

## Questions you should be able to answer in an interview

1. Why is accuracy a poor primary metric when useful items are rare?
2. Why do we use the same starting positive for all methods in each comparison?
3. How do the learner and evaluator avoid sharing hidden labels?
4. Why does a score of 0.2 not mean a 20% probability of buying?
5. Why might random exploration make this particular benchmark worse?
6. What changes when you move from old news topics to current IST buying signals?
7. Why is the strongest result still not an exact replication of the full paper?
8. What does a missing effort-at-90 value mean, and why must you not replace it with zero?

## How to run your next experiment

Copy the project before changing settings so the reference results remain intact. Write a hypothesis and one changed parameter first. For example: 'A 50-item batch reduces retraining time without losing more than two percentage points of recall at 1,000 reviews.' Use new random seeds for confirmation. Keep the same budget, representation and starting documents for both variants. Report per-topic differences, time and adverse results. Do not keep tuning against the same five topics and call the final result independent validation.
