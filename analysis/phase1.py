"""Pure transformations of archived run records; no filesystem access or loader.

The notebook supplies parsed inputs and owns all output operations. Counts come
only from runs.csv; original metric values are independent archived consistency
comparators, not external ground-truth fixtures. Any inconsistency raises.
"""
from fractions import Fraction
from itertools import combinations, product
import hashlib
import math
from types import SimpleNamespace
import warnings

import numpy as np
import pandas as pd
from scipy.stats import rankdata, bootstrap


ABS_TOL = 1e-12
TARGETS = (75, 80, 90)
OBSERVED = "OBSERVED"
CENSORED = "CENSORED"


class InputError(ValueError):
    """Invalid or inconsistent immutable input: stop, do not repair it."""


def _integer(value, name, minimum=0):
    try:
        numeric = float(value)
    except (ValueError, TypeError):
        raise InputError(f"Missing/non-numeric {name}: {value!r}") from None
    if not math.isfinite(numeric) or numeric != int(numeric) or numeric < minimum:
        raise InputError(f"Invalid integer {name}: {value!r}")
    return int(numeric)


def _missing(value):
    return value is None or value == "" or (isinstance(value, float) and math.isnan(value))


def _compare(actual, recorded, name):
    if actual is None:
        if not _missing(recorded):
            raise InputError(f"{name}: censored in audit but recorded as {recorded!r}")
        return
    if _missing(recorded):
        raise InputError(f"{name}: observed in audit but missing from runs.csv")
    if isinstance(actual, (int, np.integer)):
        if _integer(recorded, name) != actual:
            raise InputError(f"{name}: audit={actual}, CSV={recorded}")
    else:
        if not math.isclose(float(recorded), actual, rel_tol=0, abs_tol=ABS_TOL):
            raise InputError(f"{name}: audit={actual}, CSV={recorded}")


def validate_inputs(rows, audits, original_plan):
    """Return normalized records after exact grid and archived-metric checks.

    audits maps filenames (not paths) to parsed JSON objects. No files are read.
    """
    expected = set(product(original_plan["topics"], original_plan["seeds"],
                           original_plan["policies"]))
    found, normalized, used_files = set(), [], set()
    topic_counts, seed_rows, seed_ids, document_labels = {}, {}, {}, {}
    if not rows:
        raise InputError("runs.csv contains no records")
    for source in rows:
        row = dict(source)
        required = ("topic", "seed", "policy", "n", "positives", "reviewed", "seed_doc_id")
        for name in required:
            if name not in row or _missing(row[name]):
                raise InputError(f"Missing {name} in runs.csv")
        topic, seed, policy = row["topic"], _integer(row["seed"], "seed"), row["policy"]
        key = (topic, seed, policy)
        if key in found:
            raise InputError(f"Duplicate run {key}")
        found.add(key)
        n = _integer(row["n"], f"{key} n", 2)
        r = _integer(row["positives"], f"{key} positives", 1)
        reviewed = _integer(row["reviewed"], f"{key} reviewed", 1)
        if r > n or reviewed != min(n, original_plan["budget"]):
            raise InputError(f"Invalid population or truncated/incorrect-budget run {key}")
        if topic in topic_counts and topic_counts[topic] != (n, r):
            raise InputError(f"Inconsistent N/R within topic {topic}")
        topic_counts[topic] = (n, r)
        filename = f"{topic}_{seed}_{policy}.json"
        if filename not in audits:
            raise InputError(f"Missing audit {filename}")
        used_files.add(filename)
        audit = audits[filename]
        if (audit.get("topic"), audit.get("seed"), audit.get("policy")) != key:
            raise InputError(f"Audit identity mismatch: {filename}")
        for field in ("row_order", "observed_labels", "batch_ends"):
            if not isinstance(audit.get(field), list):
                raise InputError(f"Missing/invalid {field}: {filename}")
        order = [_integer(x, f"{key} review row") for x in audit["row_order"]]
        labels = [_integer(x, f"{key} label") for x in audit["observed_labels"]]
        boundaries = [_integer(x, f"{key} boundary", 1) for x in audit["batch_ends"]]
        if len(order) != reviewed or len(labels) != reviewed:
            raise InputError(f"Audit length mismatch: {key}")
        if len(set(order)) != reviewed or max(order) >= n:
            raise InputError(f"Duplicate/out-of-range document row: {key}")
        if not boundaries or boundaries[0] != 1 or boundaries[-1] != reviewed:
            raise InputError(f"Missing initial/final boundary: {key}")
        if boundaries != sorted(set(boundaries)):
            raise InputError(f"Non-increasing/repeated batch boundary: {key}")
        if any(x not in (0, 1) for x in labels) or labels[0] != 1:
            raise InputError(f"Nonbinary labels or missing known-positive seed: {key}")
        if sum(labels) > r or reviewed - sum(labels) > n - r:
            raise InputError(f"Observed labels exceed population totals: {key}")
        pair = (topic, seed)
        if pair in seed_rows and seed_rows[pair] != order[0]:
            raise InputError(f"Seed row differs across paired methods: {pair}")
        if pair in seed_ids and seed_ids[pair] != str(row["seed_doc_id"]):
            raise InputError(f"External seed ID differs across paired methods: {pair}")
        seed_rows[pair], seed_ids[pair] = order[0], str(row["seed_doc_id"])
        for doc, label in zip(order, labels):
            label_key = (topic, doc)
            if label_key in document_labels and document_labels[label_key] != label:
                raise InputError(f"Conflicting labels for {label_key}")
            document_labels[label_key] = label
        gains = np.cumsum(labels, dtype=np.int64)
        for k in (20, 100, 500, 1000, 2000, 5000):
            for prefix in ("found", "precision", "recall"):
                col = f"{prefix}_at_{k}"
                actual = None
                if k <= reviewed:
                    actual = int(gains[k-1])
                    if prefix == "precision": actual /= k
                    if prefix == "recall": actual /= r
                _compare(actual, row.get(col), f"{key} {col}")
        for target in (75, 90):
            hits = np.flatnonzero(gains >= (target*r + 99)//100)
            effort = int(hits[0]+1) if len(hits) else None
            batch = next((b for b in boundaries if effort is not None and b >= effort), None)
            _compare(effort, row.get(f"effort_at_{target}"), f"{key} effort@{target}")
            _compare(batch, row.get(f"batch_effort_at_{target}"), f"{key} batch effort@{target}")
            _compare(target/100-effort/n if effort is not None else None,
                     row.get(f"wss_at_{target}"), f"{key} WSS@{target}")
        normalized.append(dict(topic=topic, seed=seed, policy=policy, n=n, positives=r,
                               reviewed=reviewed, order=tuple(order), labels=tuple(labels),
                               boundaries=tuple(boundaries)))
    if found != expected:
        raise InputError(f"Run grid differs: missing={sorted(expected-found)}, extra={sorted(found-expected)}")
    if set(audits) != used_files:
        raise InputError(f"Unmatched audit files: {sorted(set(audits)-used_files)}")
    return sorted(normalized, key=lambda x: (x["topic"], x["seed"], x["policy"]))


def run_metrics(records):
    """Long-form exact rational metrics, plus explicit censoring metadata."""
    output = []
    for rec in records:
        n, r, budget = rec["n"], rec["positives"], rec["reviewed"]
        gains = np.cumsum(rec["labels"], dtype=np.int64)
        base = {k: rec[k] for k in ("topic", "seed", "policy", "n", "positives", "reviewed")}
        def emit(metric, value, cutoff=None, bound=None, reason=None):
            output.append(dict(**base, metric=metric,
                status=OBSERVED if value is not None else CENSORED,
                value=float(value) if value is not None else None,
                numerator=value.numerator if value is not None else None,
                denominator=value.denominator if value is not None else None,
                requested_depth=cutoff, censor_lower_bound=bound,
                censor_reason="" if value is not None else
                    (reason or ("requested_depth_exceeds_logged_budget" if cutoff is not None else "target_not_reached"))))
        cutoffs = {"recall_at_1000": 1000, "recall_at_R": r, "recall_at_2R": min(n, 2*r)}
        for a, b in product((1, 2, 4), (0, 100, 1000)):
            cutoffs[f"recall_at_{a}R_plus_{b}"] = min(n, a*r+b)
        for metric, k in cutoffs.items():
            emit(metric, Fraction(int(gains[k-1]), r) if k <= budget else None, cutoff=k)
        for target in TARGETS:
            hits = np.flatnonzero(gains >= (target*r+99)//100)
            effort = int(hits[0]+1) if len(hits) else None
            batch = next((b for b in rec["boundaries"] if effort is not None and b >= effort), None)
            for name, val, denominator in (
                ("effort", effort, 1), ("batch_effort", batch, 1),
                ("depth_fraction", effort, n), ("depth_per_positive", effort, r)):
                emit(f"{name}_at_{target}", Fraction(val, denominator) if val is not None else None,
                     bound=budget/denominator if val is None else None)
            overshoot = batch-effort if batch is not None and effort is not None else None
            emit(f"overshoot_at_{target}", Fraction(overshoot, 1) if overshoot is not None else None,
                 bound=0 if overshoot is None else None, reason="component_censored")
    return pd.DataFrame(output)


def topic_metrics(metrics):
    """No mean over only the successful seeds of a topic."""
    result = []
    for (topic, policy, metric), group in metrics.groupby(["topic", "policy", "metric"], sort=True):
        complete = group.status.eq(OBSERVED).all()
        value = None
        if complete:
            fractions = [Fraction(int(x.numerator), int(x.denominator)) for x in group.itertuples()]
            value = sum(fractions, Fraction()) / len(fractions)
        censored_seeds = sorted(group.loc[group.status.ne(OBSERVED), "seed"].astype(int).tolist())
        result.append(dict(topic=topic, policy=policy, metric=metric,
            status=OBSERVED if complete else CENSORED,
            value=float(value) if complete else None,
            numerator=value.numerator if complete else None,
            denominator=value.denominator if complete else None,
            seeds_total=len(group), seeds_observed=int(group.status.eq(OBSERVED).sum()),
            censored_seeds=",".join(map(str, censored_seeds))))
    return pd.DataFrame(result)


def method_metrics(topics):
    """Complete macro means; explicitly labelled recall-only partial means."""
    output = []
    for (policy, metric), group in topics.groupby(["policy", "metric"], sort=True):
        observed = group.status.eq(OBSERVED)
        excluded = sorted(group.loc[~observed, "topic"].tolist())
        complete = bool(observed.all())
        partial_allowed = metric.startswith("recall_") and observed.any() and not complete
        included = sorted(group.loc[observed, "topic"].tolist())
        output.append(dict(policy=policy, metric=metric,
            status=OBSERVED if complete else CENSORED,
            full_mean=float(group.value.mean()) if complete else None,
            partial_mean=float(group.loc[observed, "value"].mean()) if partial_allowed else None,
            mean_label=(f"Full mean: {len(group)}/{len(group)} topics" if complete else
                        f"PARTIAL recall mean: {len(included)}/{len(group)} topics" if partial_allowed else
                        "NOT COMPUTED: censored; no success-only effort mean"),
            topics_total=len(group), topics_observed=len(included),
            observed_topics=",".join(included), censored_topics=",".join(excluded)))
    return pd.DataFrame(output)


def paired_statistics(topics, methods, bootstrap_resamples=10000, analysis_seed=20260907):
    """All unordered method pairs; difference is method_a minus method_b.

    Fractions avoid manufacturing nonzero pairs through floating roundoff.
    Whole topics (already averaged over all seeds) are bootstrap units.
    """
    statistics, differences = [], []
    for metric in sorted(topics.metric.unique()):
        frame = topics[topics.metric.eq(metric)]
        for method_a, method_b in combinations(methods, 2):
            left = frame[frame.policy.eq(method_a)].set_index("topic")
            right = frame[frame.policy.eq(method_b)].set_index("topic")
            if set(left.index) != set(right.index):
                raise InputError(f"Unpaired topic grid for {method_a}, {method_b}, {metric}")
            keys = sorted(left.index)
            excluded = [q for q in keys if left.loc[q, "status"] != OBSERVED or right.loc[q, "status"] != OBSERVED]
            base = dict(metric=metric, method_a=method_a, method_b=method_b,
                        topics_total=len(keys), censored_topics=",".join(excluded))
            vals = []
            for q in keys:
                value = None
                if q not in excluded:
                    a, b = left.loc[q], right.loc[q]
                    value = Fraction(int(a.numerator), int(a.denominator))-Fraction(int(b.numerator), int(b.denominator))
                    vals.append(value)
                differences.append(dict(**base, topic=q,
                    status=OBSERVED if value is not None else CENSORED,
                    difference=float(value) if value is not None else None))
            if excluded:
                statistics.append(dict(**base, status="NOT_COMPUTED_CENSORED",
                    topics_used=0, note="No inference on a complete-case subset; censored topics listed."))
                continue
            nz = [x for x in vals if x != 0]
            m = len(nz)
            if m > 20:
                raise InputError("Exact sign enumeration exceeds the declared 20-nonzero-topic implementation limit")
            observed = abs(sum(nz, Fraction()))
            assignments = list(product((-1, 1), repeat=m))
            extreme = sum(abs(sum((s*v for s, v in zip(signs, nz)), Fraction())) >= observed
                          for signs in assignments)
            sign_p = extreme/len(assignments)
            if m:
                # Rank exact absolute Fractions; scipy average ranks retain exact ties.
                unique = sorted(set(abs(x) for x in nz))
                codes = [unique.index(abs(x)) for x in nz]
                doubled = np.rint(2*rankdata(codes, method="average")).astype(int)
                observed_rank = abs(sum((1 if x > 0 else -1)*int(rank) for x, rank in zip(nz, doubled)))
                rank_extreme = sum(abs(sum(s*int(rank) for s, rank in zip(signs, doubled))) >= observed_rank
                                   for signs in assignments)
                wilcoxon_p = rank_extreme/len(assignments)
            else:
                wilcoxon_p = 1.0
            minimum = min(1.0, 2/(2**m))
            identity = f"{analysis_seed}|{metric}|{method_a}|{method_b}"
            rng_seed = int.from_bytes(hashlib.sha256(identity.encode()).digest()[:8], "big")
            rng = np.random.default_rng(rng_seed)
            arr = np.array([float(v) for v in vals])
            sampled = arr[rng.integers(0, len(arr), size=(bootstrap_resamples, len(arr)))].mean(axis=1)
            low, high = np.quantile(sampled, (.025, .975), method="linear")
            # Reuse exactly the percentile draws; BCa changes endpoints, not resampling.
            bca_low = bca_high = float("nan")
            bca_status = "UNDEFINED_DEGENERATE"
            bca_warning = "All topic differences identical; acceleration undefined."
            if np.ptp(arr) != 0:
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter("always")
                    result = bootstrap((arr,), np.mean, method="BCa", confidence_level=.95,
                        n_resamples=0, bootstrap_result=SimpleNamespace(bootstrap_distribution=sampled),
                        rng=np.random.default_rng(rng_seed))
                bca_low, bca_high = map(float, result.confidence_interval)
                bca_status = "OBSERVED" if np.isfinite([bca_low, bca_high]).all() else "UNDEFINED"
                bca_warning = "; ".join(str(w.message) for w in caught)
            # A disclosed diagnostic, not a significance test: zero inclusion differs,
            # or an endpoint moves by >=25% of the percentile interval width.
            disagreement = "UNDEFINED_BCA"
            shift = float("nan")
            if bca_status == "OBSERVED":
                shift = max(abs(bca_low-low), abs(bca_high-high))
                zero_disagrees = (low <= 0 <= high) != (bca_low <= 0 <= bca_high)
                material = zero_disagrees or shift >= .25*(high-low)
                disagreement = "MATERIAL" if material else "BELOW_DIAGNOSTIC_THRESHOLD"
            note = "Exact sign-flip is primary. Both bootstrap variants are exploratory and unreliable with five topics; agreement does not establish coverage; nonsignificance is not equivalence."
            if disagreement == "MATERIAL":
                note += " BCa and percentile disagree materially: interval inference is not trustworthy here."
            if minimum > .05:
                note += f" Minimum attainable two-sided p={minimum:g} exceeds 0.05 for {m} nonzero pairs."
            statistics.append(dict(**base, status=OBSERVED, topics_used=len(vals), nonzero_pairs=m,
                mean_difference=float(sum(vals, Fraction())/len(vals)),
                bootstrap_ci_low=float(low), bootstrap_ci_high=float(high),
                bca_ci_low=bca_low, bca_ci_high=bca_high, bca_status=bca_status,
                bca_warning=bca_warning, interval_disagreement=disagreement,
                maximum_endpoint_shift=shift,
                **{f"difference_{q}": float(v) for q, v in zip(keys, vals)},
                bootstrap_resamples=bootstrap_resamples, analysis_seed=analysis_seed,
                exact_sign_flip_p=sign_p, wilcoxon_exact_p=wilcoxon_p,
                minimum_two_sided_p=minimum, note=note))
    return pd.DataFrame(statistics), pd.DataFrame(differences)


def gain_curves(records):
    """Every observed prefix, without truncation, interpolation, or extrapolation."""
    frames = []
    for rec in records:
        k = np.arange(1, rec["reviewed"]+1)
        n, r = rec["n"], rec["positives"]
        g = np.cumsum(rec["labels"], dtype=np.int64)
        frames.append(pd.DataFrame(dict(topic=rec["topic"], seed=rec["seed"], policy=rec["policy"],
            k=k, gain=g, recall=g/r, normalized_effort=k/r,
            random_reference=(1+(k-1)*(r-1)/(n-1))/r,
            ideal_bound=np.minimum(k/r, 1), batch_boundary=np.isin(k, rec["boundaries"]))))
    return pd.concat(frames, ignore_index=True)


def metric_display(value, status, metric):
    if status != OBSERVED:
        return CENSORED
    if metric.startswith("recall_"):
        return f"{100*value:.2f}%"
    return f"{value:,.3f}"


def summary_display(summary, metric_order, methods):
    """A reader-facing table that cannot hide censored partial means."""
    result = []
    for policy in methods:
        row = {"method": policy}
        for metric in metric_order:
            item = summary[(summary.policy == policy) & (summary.metric == metric)].iloc[0]
            if item.status == OBSERVED:
                row[metric] = metric_display(item.full_mean, OBSERVED, metric)
            elif pd.notna(item.partial_mean):
                row[metric] = (f"CENSORED | PARTIAL {100*item.partial_mean:.2f}% "
                    f"({item.topics_observed}/{item.topics_total}; excludes {item.censored_topics})")
            else:
                row[metric] = f"CENSORED (topics: {item.censored_topics}); no mean"
        result.append(row)
    return pd.DataFrame(result)
