"""Strict experiment-plan validation; no filesystem or data-loading side effects."""
from copy import deepcopy
import math
from sklearn.svm import LinearSVC

SVM_DEFAULTS = dict(C=1.0, loss="hinge", dual=True, tol=1e-4, max_iter=10000)
PLAN_FIELDS = set("status topics seeds policies budget primary_metric secondary_metrics svm seeding topic_selection temporary_negatives inference stopping extensions revision metric_parameters inputs analysis censoring deferred_phase_3_exit_criteria withdrawn_exploration_option outputs epsilon audit".split())
NESTED_FIELDS = {
    "audit": {"margin_scope"},
    "extensions": set("fixed_20 explore_10".split()),
    "revision": set("date_utc timing reason historical_plan original_primary_metric original_primary_metric_always_reported phase original_plan_sha256".split()),
    "metric_parameters": set("a b target_recalls scaled_cutoff_clamp recall_at_R_cutoff original_fixed_cutoff".split()),
    "inputs": set("runs_csv audits N_column R_column invoke_loader invoke_experiment".split()),
    "analysis": set("bootstrap_resamples bootstrap_confidence bootstrap_variants bootstrap_shared_draws primary_inference interval_material_disagreement analysis_seed paired_unit exact_sign_flip wilcoxon contrasts csv_consistency_absolute_tolerance csv_consistency_relative_tolerance".split()),
    "censoring": set("explicit_status full_mean_requires_all_topics_and_seeds partial_recall_mean partial_effort_mean partial_inference extrapolation".split()),
    "deferred_phase_3_exit_criteria": set("prerequisite required_run generation prohibited_now".split()),
    "outputs": set("directory notebook audit_directory".split()),
}


def resolve_plan(plan=None):
    config = deepcopy({} if plan is None else plan)
    if not isinstance(config, dict):
        raise ValueError("Plan must be a JSON object")
    unknown = set(config)-PLAN_FIELDS
    if unknown:
        raise ValueError(f"Unknown plan keys: {sorted(unknown)}")
    for name, keys in NESTED_FIELDS.items():
        if name in config:
            if not isinstance(config[name], dict):
                raise ValueError(f"{name} must be an object")
            extra = set(config[name])-keys
            if extra:
                raise ValueError(f"Unknown {name} keys: {sorted(extra)}")
    svm = config.get("svm", {})
    if not isinstance(svm, dict):
        raise ValueError("svm must be an object")
    extra = set(svm)-set(LinearSVC().get_params())
    if extra:
        raise ValueError(f"Unknown svm keys: {sorted(extra)}")
    if "random_state" in svm:
        raise ValueError("svm.random_state is derived from the run seed; configure seeds instead")
    config["svm"] = {**SVM_DEFAULTS, **svm}
    epsilon = config.get("epsilon", .1)
    if isinstance(epsilon, bool) or not isinstance(epsilon, (int,float)) or not math.isfinite(epsilon) or not 0 <= epsilon <= 1:
        raise ValueError("epsilon must be finite and between 0 and 1")
    config["epsilon"] = epsilon
    audit = config.setdefault("audit", {"margin_scope": "full"})
    audit.setdefault("margin_scope", "full")
    if audit["margin_scope"] not in ("full", "top_1000_plus_selected", "batch_plus_100_min_1000_plus_selected"):
        raise ValueError("Unknown margin_scope")
    return config
