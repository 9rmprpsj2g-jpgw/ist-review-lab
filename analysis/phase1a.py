"""Phase 1A archived-input reanalysis only. Never imports the learning runner."""

import sys as _durable_sys
from pathlib import Path as _DurablePath
_durable_sys.path.insert(0, str(_DurablePath(__file__).resolve().parents[1]))
from src import durable_io as _durable
import csv
import hashlib
import json
from pathlib import Path

from analysis.artifact_io import atomic_file, atomic_copy
from analysis.execute_notebook import check_inputs
from analysis.phase1 import (validate_inputs, run_metrics, topic_metrics, method_metrics,
                            paired_statistics, summary_display, CENSORED)
from analysis.review_report import write_report


def main():
    root = Path(__file__).resolve().parents[1]
    out = root / "phase1a_outputs"
    out.mkdir(exist_ok=True)
    check_inputs()
    original = json.loads((root/"experiment_plan.json").read_text())
    plan = json.loads((root/"experiment_plan_v2.json").read_text())
    with (root/"results/runs.csv").open(newline="") as handle:
        records = validate_inputs(list(csv.DictReader(handle)),
            {p.name:json.loads(p.read_text()) for p in sorted((root/"results/audits").glob("*.json"))}, original)
    metrics = run_metrics(records)
    topics = topic_metrics(metrics)
    methods = method_metrics(topics)
    stats, differences = paired_statistics(topics, original["policies"],
        bootstrap_resamples=plan["analysis"]["bootstrap_resamples"], analysis_seed=plan["analysis"]["analysis_seed"])
    def export(frame, name, missing=()):
        shown = frame.copy()
        for column in missing:
            if column in shown:
                shown[column] = shown[column].astype(object).where(shown[column].notna(), CENSORED)
        with atomic_file(out/name, "w", expected_count=len(shown)) as handle:
            _durable.write_csv(shown, handle, index=False)
    export(metrics,"metrics_by_run.csv",("value",))
    export(topics,"metrics_by_topic.csv",("value",))
    export(methods,"metrics_by_method.csv",("full_mean",))
    export(stats,"paired_statistics.csv")
    export(differences,"paired_topic_differences.csv",("difference",))
    export(summary_display(methods,["recall_at_R","recall_at_1R_plus_100","recall_at_1000","recall_at_2R"],original["policies"]),"primary_metrics_display.csv")
    # Exact archived CSV field comparison for every preexisting metric, not a fixture.
    def rows(path):
        with path.open(newline="") as handle:
            return list(csv.DictReader(handle))
    approved = rows(root/"phase1_outputs/metrics_by_run.csv")
    unchanged = [r for r in rows(out/"metrics_by_run.csv") if not r["metric"].startswith("overshoot_")]
    if approved != unchanged:
        raise RuntimeError("Scientific comparison FAILED: preexisting metric records changed")
    # Overshoot is derived per run, not inferred by subtracting unrelated intervals.
    lookup = {(r.topic,r.seed,r.policy,r.metric):r for r in metrics.itertuples()}
    for row in metrics[metrics.metric.str.startswith("overshoot_")].itertuples():
        target = row.metric.rsplit("_",1)[1]
        a = lookup[(row.topic,row.seed,row.policy,"batch_effort_at_"+target)]
        b = lookup[(row.topic,row.seed,row.policy,"effort_at_"+target)]
        complete = a.status != CENSORED and b.status != CENSORED
        if (row.status != CENSORED) != complete:
            raise RuntimeError("Scientific comparison FAILED: overshoot censoring differs from components")
        if complete and (row.value != a.value-b.value or row.value < 0):
            raise RuntimeError("Scientific comparison FAILED: overshoot identity/nonnegativity")
    census = []
    for metric in metrics.metric.drop_duplicates():
        missing = metrics[(metrics.metric==metric) & metrics.status.eq(CENSORED)]
        pairs = stats[stats.metric.eq(metric)]
        withheld = pairs[pairs.status.ne("OBSERVED")]
        census.append(dict(metric=metric,censored_runs=len(missing),total_runs=len(records),
            censored_policy_pairs=len(withheld),total_policy_pairs=len(pairs),
            run_censor_topics="; ".join(f"{q}:{n}" for q,n in missing.groupby("topic").size().items()),
            pair_censor_topics="; ".join(f"{q}:{sum(q in str(x).split(',') for x in withheld.censored_topics)}"
                for q in original["topics"] if any(q in str(x).split(',') for x in withheld.censored_topics))))
    import pandas as pd
    export(pd.DataFrame(census),"censoring_census.csv")
    if not (out/"approved_phase1_RESULTS.md").exists():
        atomic_copy(root/"RESULTS.md",out/"approved_phase1_RESULTS.md")
    write_report(out)
    protected = check_inputs()
    receipt = {"status":"PASSED", "phase":"1A analysis amendment; awaiting review before Phase 2",
        "learning_experiments_run":0, "ground_truth_fixtures_computed":False,
        "protected_digests_unchanged":protected, "existing_metric_records_identical":len(approved),
        "overshoot_records_checked":int(metrics.metric.str.startswith("overshoot_").sum()),
        "metric_records":len(metrics), "contrast_records":len(stats),
        "checks":["archived input validation", "unchanged original metric CSV fields", "overshoot component identity and censoring", "protected digests"],
        "analysis_seed":plan["analysis"]["analysis_seed"],
        "report_sha256":hashlib.sha256((out/"review_results.md").read_bytes()).hexdigest()}
    with atomic_file(out/"verification.json","w") as handle:
        json.dump(receipt,handle,indent=2)
    atomic_copy(out/"review_results.md",root/"RESULTS.md")
    atomic_copy(out/"review_results.md",out/"RESULTS.md")
    print(json.dumps(receipt,indent=2))


if __name__ == "__main__":
    main()
