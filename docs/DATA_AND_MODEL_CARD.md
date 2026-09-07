# Data and model card

## Scope and intended use

An educational, scoped Auto TAR reproduction plus a separate experimental matter-signal ranking utility. It helps a BDR understand reviewer feedback and test prioritization on a supplied queue. It is not an IST product or a production review system.

## Benchmark data

RCV1-v2's chronological training partition, distributed by the LIBSVM maintainers as document IDs, original labels and scrambled stemmed tokens. The source has 23,149 rows. The project uses five binary one-topic-versus-rest review tasks, independently preserving their labels. The raw news text is not reconstructed. Exact duplicate token bags are counted in `data/source_lock.json`; retained duplicates can make a review task easier. Near-duplicate stories and topic-label errors have not been comprehensively audited.

Input file URL, size-related metadata and SHA-256 digest are recorded in the lock file. The downloader fails on checksum changes. Benchmark input files are not bundled in the portfolio ZIP; rerunning downloads the public research representation from the source. Reuters material remains subject to its source terms. This project grants no additional rights to the corpus. No private IST or client data was used.

## Evaluation design

All words in the fixed pool are visible for unsupervised feature construction. Only the initial seed and subsequently reviewed judgments are passed into training. The evaluator holds the complete labels to simulate a reviewer and calculate recall. One known positive is chosen using an oracle and charged as one review; the effort to locate that first positive is not measured. These are idealized, error-free review labels.

There is no conventional random train/test split because the object of measurement is the sequence in which labels are discovered in the fixed pool. These results are not future-document classification performance. Hyperparameters and variants were fixed before outcomes. Repeated starts measure starting-seed sensitivity on this same collection, not independent client matters. All 105 planned runs are retained.

## Metrics and uncertainty

Primary endpoint: macro mean of recall at 1,000 reviews, first averaging three starts per topic and then giving each of five topics equal weight. Precision at 20 includes the known-positive seed; it should not be described as an unbiased estimate for an unseeded queue. Review effort includes the seed and all reviewed negatives. Both within-batch threshold positions and whole-batch effort are retained. Recall thresholds not reached by 5,000 reviews remain missing/censored, never zero. Means restricted to successful runs are not used to rank methods.

Reported min-max ranges across starts are sensitivity descriptions, not confidence intervals. The five-topic set and three starts are too small to justify broad reliability or statistical-superiority claims. Runtime describes this CPU execution with two workers and may differ elsewhere.

## Practical model limitations

The BDR utility learns from its supplied labels, not from the benchmark model. Class balancing and confirmed-negative training are operational changes. Sparse word features can miss synonyms, negation, temporal context and complex evidence. Source truth and service need require human verification. Ranking margins are not calibrated probabilities. Dates and source links are carried through for inspection, not validated by the program. Exact duplicates are handled; related matters and accounts still need grouping.

No autonomous discovery, current-event collection, messaging, CRM update, privilege determination or completeness certification is provided. The stopping budget is an experimental budget, not a defensible determination that a legal review is complete.
