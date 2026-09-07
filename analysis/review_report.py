"""Reader report derived independently from each execution's persisted tables."""
import csv
from pathlib import Path
from analysis.artifact_io import atomic_file


def table(rows, columns):
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(c, "")).replace("|", ";") for c in columns) + " |")
    return "\n".join(lines)


def write_report(directory):
    directory = Path(directory)
    def read(name):
        with (directory/name).open(newline="") as handle:
            return list(csv.DictReader(handle))
    core = read("primary_metrics_display.csv")
    stats = read("paired_statistics.csv")
    census = read("censoring_census.csv")
    parts = ["""# Phase 1A: growing batches add committed review through overshoot

Overshoot is committed batch effort minus exact effort at the target crossing. Late growing batches can commit reviewers to documents beyond that crossing. We derive this quantity for each run at 75%, 80% and 90% recall, then compare paired topic means. A censored component censors overshoot; no success-only mean is substituted.

The original recall@1000 difference between AutoTAR and fixed-20 is +0.0276 percentage points (exact sign-flip p=0.875). Committed effort tells a different cost story: AutoTAR minus fixed-20 is +97.6, +132.7 and +193.9 documents at 75%, 80% and 90% targets. At 80% and 90% all five topics agree in direction. These are direction and magnitude observations, NOT statistically significant findings; the five-topic exact two-sided floor is 0.0625.

**Correction to the proposed interpretation:** archived exact effort at 75% is +19.6 documents, percentile 95% interval [-8.07, 51.07], p=0.3125. The supplied -1.06 documents and interval [-1.47, -0.65] do not match the archived exact-effort contrast. The supported decomposition is +97.6 = +19.6 exact effort +78.0 overshoot. This does not show that growing batches cross the target one document earlier.

This amendment is post-outcome analysis of the same five topics, three seeds and seven policies. No learning experiment has been rerun.

## Recall@R and the R+100 companion

Recall@R is fully observed: 0/105 runs and 0/21 policy pairs censored. Recall@(R+100) is also fully observed and is now a reported companion. On C16, R=49: each relevant document changes recall by 100/49 = 2.0408 percentage points. Adding 100 reviews provides a larger startup allowance at low prevalence; it does **not** change that per-document recall resolution or guarantee elimination of ties. Recall@R was selected AFTER outcomes; original recall@1000 remains visible.

AutoTAR minus explore_10 at recall@R is directionally consistent across every topic with a nonzero difference: four positive differences and the C16 tie. Magnitude is about 2 pp (+2.1639 pp), with both intervals excluding zero; the exact test is floored at p=0.125 by that tie. This is not a claim of equivalence or statistical significance.

## Seven-policy comparison

Means weight the five topics equally after averaging all three seeds within each topic. Historical policy names are retained in this Phase 1 reanalysis.
""", table(core, ["method", "recall_at_R", "recall_at_1R_plus_100", "recall_at_1000"]), """
Uncertainty sampling falls from 51.02% at recall@1000 to 40.67% at recall@R. Frozen SVM and seed similarity swap order: 27.73% versus 27.24% at recall@1000, but 25.76% versus 26.62% at recall@R. Their difference is not resolved by this five-topic study; "indistinguishable" here means no supported separation, not demonstrated equivalence.

## Inferential conventions

Each row is method_a minus method_b, averaging seeds before inference. Exact sign-flip is primary. With at most five nonzero topic differences, the minimum attainable two-sided p-value is 0.0625. Nonsignificance is not equivalence. Both 95% percentile and BCa intervals are sensitivity analyses: neither has trustworthy coverage established here. BCa reuses the same 10,000 topic-bootstrap draws. Material disagreement means different inclusion of zero or an endpoint shift of at least 25% of percentile width; this disclosed post-outcome diagnostic is not a validated threshold. Disagreement challenges interval inference; agreement does not validate it.

Recall differences and interval endpoints below are percentage points. Raw columns are the five seed-averaged paired topic differences, not individual-seed observations.
"""]
    appendix = []
    overshoot_sections = []
    order = ["overshoot_at_75","overshoot_at_80","overshoot_at_90","recall_at_R","recall_at_1R_plus_100","recall_at_1000"]
    order += sorted({r["metric"] for r in stats} - set(order))
    for metric in order:
        selected = [r for r in stats if r["metric"] == metric and r["status"] == "OBSERVED"]
        if not selected:
            continue
        rows = []
        scale = 100 if metric.startswith("recall_") else 1
        for r in selected:
            def number(k):
                return f"{float(r[k])*scale:.6f}" if r.get(k) else "UNDEFINED"
            rows.append({"Pair":r["method_a"]+" − "+r["method_b"],
                "Mean":number("mean_difference"), "Exact sign-flip p":r["exact_sign_flip_p"],
                "Percentile 95%":"["+number("bootstrap_ci_low")+", "+number("bootstrap_ci_high")+"]",
                "BCa 95%":"["+number("bca_ci_low")+", "+number("bca_ci_high")+"]",
                **{q:number("difference_"+q) for q in ["C12","C15","C16","C18","GCRIM"]},
                "Interval diagnostic":r["interval_disagreement"]})
        destination = overshoot_sections if metric.startswith("overshoot_") else appendix
        destination += ["\n### "+metric+"\n\n"+("Units: percentage points." if scale==100 else "Units: the named effort/depth metric."), table(rows, list(rows[0]))]
    topic_values = read("metrics_by_topic.csv")
    policy_names = [r["method"] for r in core]
    topic_rows = []
    for target in (75,80,90):
        for q in ("C12","C15","C16","C18","GCRIM"):
            row = {"Target":str(target)+"%", "Topic":q}
            for policy in policy_names:
                found = next(r for r in topic_values if r["metric"]==f"overshoot_at_{target}" and r["topic"]==q and r["policy"]==policy)
                row[policy] = f"{float(found['value']):.3f}" if found["status"]=="OBSERVED" else "CENSORED"
            topic_rows.append(row)
    intro, rest = parts[0].split("## Recall@R", 1)
    parts[0] = intro
    parts.insert(1, "\n## Overshoot by topic and policy\n\nDocuments committed beyond crossing; means require all three seeds. Paired tables report method_a minus method_b, both 95% intervals and raw five-topic differences. Exact sign-flip remains primary; neither interval is reliable with five topics.\n\n"+table(topic_rows,list(topic_rows[0]))+"\n\n"+"\n\n".join(overshoot_sections))
    parts.insert(2, "## Recall@R"+rest)
    parts += ["""
## Limitation: the 5,000-document budget censors deeper comparisons

The census includes every metric and all recall@4R cutoffs. Each target family includes exact effort, whole-batch effort, depth/N and depth/R. Pair-topic counts overlap. Any censored seed on either side withholds full-topic inference; no complete-case test or success-only effort mean substitutes for it.
""", table(census,list(census[0])), """
C15 censors recall@2R; C18 additionally censors the 4R family, and GCRIM joins at 4R+1000. Target-effort comparisons are censored in 18/21 pairs at 75% and 80% recall, and 20/21 at 90%. The 5,000-document budget is too short for most full-topic comparisons at these targets. Partial recall means must name excluded topics; they are not the five-topic result.

## What this study can and cannot support

This study supports descriptive comparisons of seven fixed-label retrieval policies on these five RCV1-v2 topics under the original known-positive-seed, 5,000-review protocol, with fully observed recall@R and recall@1000 and transparent topic-level uncertainty. It does not establish superiority across legal matters, equivalence from nonsignificance, reliable bootstrap coverage from five topics, or complete deeper-target cost comparisons where observations are censored. It is a scoped reproduction, not an exact replication of the paper's result tables or independent validation against TARexp; it supplies no stopping certification, legal defensibility guarantee, or evidence about sales conversion. Seed discovery/search cost was excluded in the original plan, and the revised primary metric was chosen after outcomes.

Phase 2 was authorized subject to this Phase 1A review gate; it has not begun. The redundant pool/tail option is withdrawn; exploration-first global sampling remains deferred. After Phase 3 replay passes, Phase 3B must first report fit counts and wall-clock estimates for the combined census/schedule grid and wait for explicit approval before any run. Phase 4 cost rates must come from the user. No experiment.py invocation is permitted in Phase 1A or Phase 2. Figures are presentation artifacts; their size or cross-run identity is not a numerical gate. The execution receipt records completeness, numerical agreement and protected digests separately.
"""]
    parts += ["\n## Appendix: paired inference for recall and effort measures\n"] + appendix
    with atomic_file(directory/"review_results.md", "w") as handle:
        handle.write("\n\n".join(parts)+"\n")
