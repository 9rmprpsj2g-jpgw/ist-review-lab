# Prespecification and outcome visibility

## Historical record

`experiment_plan.json` is immutable. It declares `primary_metric = "recall_at_1000"`, five topics (C12, C15, C16, C18, GCRIM), three seeds (11, 29, 47), seven methods, and a budget of 5,000 reviews. Its secondary measures are precision@20, recall@500, recall@5000, effort@75%, and effort@90%.

Its status asserts that the plan was written before outcomes were examined, and describes it as an exploratory benchmark, not an external preregistration. That assertion is part of the historical record; file contents alone do not independently establish its timing.

Its `seeding` field already states that the positive seed counts as one review and **discovery/search cost is excluded**. This was disclosed in the plan claiming advance specification. This reanalysis must not present the exclusion as a newly discovered undisclosed assumption.

## Post-outcome revision

On 2026-09-07, AFTER outcomes from the original 105 runs had been observed and discussed, the user authorized a revised metric suite. `experiment_plan_v2.json` records the revision; it does not overwrite the original plan.

The revised primary metric is recall@R. The original recall@1000 remains mandatory alongside the new summary measures. Additions are recall@2R, recall@aR+b for a in {1,2,4} and b in {0,100,1000}, full observed gain curves, exact and whole-batch effort at 75/80/90% recall, normalized target depths, and topic-level paired inference.

Reason: a fixed cutoff imposes topic-dependent recall ceilings and gives different budgets relative to the number of relevant documents. Recall@R also has limitations for rare topics because its absolute startup allowance is small; offset cutoffs and target-depth measures must remain visible.

The new primary metric is a **post-outcome analysis choice**. It is not a confirmatory test prespecified before results, and the original primary result must not disappear if another metric changes a comparison. All new pairwise statistics are exploratory; no significance result is evidence of a prespecified discovery. Nonsignificance does not establish equivalence.

## Unchanged inputs and scope

Phase 1 uses `n` and `positives` from `results/runs.csv` as N and R, and the recorded judgments/order/boundaries from `results/audits/`. It never calls `load_collection()` or runs new experiments. Source, original plan, and existing results are protected by before/after SHA-256 checks in `phase1_outputs/input_fingerprints.json`.

Inference averages seeds within topics, then treats topics as units. Five topics from one collection remain a limited evidence base. Censoring is not repaired by extrapolation or by dropping unsuccessful runs. Full macro means require all topics and all their seeds; labelled partial means are allowed only for recall, with excluded topics named. Effort and statistical tests are withheld if any required contribution is censored.

Phase 1 stops for user review. It does not implement RNG changes, rename policies, add probability estimation, validate against external ground truth, or establish novelty.
# Subsequent Phase 1 amendment — 2026-09-07

Phase 1A was requested AFTER the approved Phase 1 results were examined. Overshoot at 75/80/90 and promotion of recall@(R+100) are outcome-informed additions. The headline shift toward committed review cost is explicitly exploratory; neither the new metric nor the schedule hypothesis was advance-prespecified. Original experiment_plan.json remains unchanged. New schedule experiments require the later Phase 3B estimate/approval gate.

After the original results and percentile analysis had been observed, the user requested BCa intervals alongside percentile intervals and all five raw topic differences. Exact sign-flip remains the primary inferential statement. The material-disagreement reporting diagnostic (different zero inclusion or endpoint shift at least 25% of percentile width) was chosen before computing BCa, but AFTER original outcomes. This is not advance prespecification or proof of interval coverage. No original plan field is edited.


## Phase 2 implementation revision

The post-outcome v2 plan now names seed_only_frozen, resolves epsilon=0.1 and directs future outputs to phase2_outputs. Experiment execution remains disabled pending Phase 3B approval. Original experiment_plan.json is unchanged at v1-frozen. Exploration carry is defined over review slots in batches passing the intentional size>=10 gate; the seed and gated batches are excluded. A global one-document bound would contradict that gate. Independent RNG streams change realized trajectories, so they cannot be exactly paired with v1-frozen draws. These are implementation corrections, not newly prespecified findings.
