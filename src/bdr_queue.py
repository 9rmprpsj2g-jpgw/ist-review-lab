"""Rank a supplied matter-signal CSV using the user's own relevance judgments.

This model is trained from scratch on this queue. The RCV1 model is not reused.
No contacts are scraped, messages sent, or purchase probabilities inferred.
"""

import sys as _durable_sys
from pathlib import Path as _DurablePath
_durable_sys.path.insert(0, str(_DurablePath(__file__).resolve().parents[1]))
from src import durable_io as _durable
import argparse
import csv
import json
from datetime import date
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from .learner import new_svm

REQUIRED = {"id", "account", "signal", "event_date", "source_url", "label"}


def rank_signals(input_path, output_path, as_of, top=20, seed=11):
    frame = pd.read_csv(input_path, dtype=str, keep_default_na=False)
    if not REQUIRED.issubset(frame.columns):
        raise ValueError(f"Missing columns: {sorted(REQUIRED-set(frame.columns))}")
    if frame.id.duplicated().any() or (frame.id.str.strip() == "").any():
        raise ValueError("Every record needs a unique nonempty ID.")
    if not frame.label.isin(["", "0", "1"]).all():
        raise ValueError("Use label 1, 0, or blank. Do not label unknowns as 0.")
    if (frame.signal.str.strip() == "").any():
        raise ValueError("Every record needs evidence text in signal.")
    if top < 1:
        raise ValueError("top must be at least 1.")
    as_of_date = date.fromisoformat(as_of)
    # Same account + normalized text is one evidence item, regardless of URL.
    frame["_key"] = frame.account.str.strip().str.casefold()+"|"+frame.signal.str.casefold().str.split().str.join(" ")
    dedup_audit = []
    kept = []
    for _, group in frame.groupby("_key", sort=False):
        known = group[group.label != ""]
        if known.label.nunique() > 1:
            raise ValueError("Conflicting labels for duplicate evidence: "+", ".join(group.id))
        canonical = known.iloc[0] if len(known) else group.iloc[0]
        kept.append(canonical)
        for duplicate in group[group.id != canonical.id].id:
            dedup_audit.append({"excluded_id": duplicate, "canonical_id": canonical.id})
    frame = pd.DataFrame(kept).reset_index(drop=True)
    observed = np.flatnonzero(frame.label.to_numpy() != "")
    if "1" not in frame.label.values:
        raise ValueError("Mark at least one useful signal with label=1 first.")
    if "0" not in frame.label.values:
        raise ValueError("Mark at least one reviewed, non-useful signal with label=0 first.")
    if len(observed) == len(frame):
        raise ValueError("No unreviewed signals remain; add new records.")
    vectorizer = TfidfVectorizer(ngram_range=(1,2), sublinear_tf=True,
                                 stop_words="english", min_df=1)
    X = vectorizer.fit_transform(frame.signal)
    # Operational adaptation for small BDR queues: use confirmed positives AND
    # negatives, with class balancing. Pseudo-labeling a whole small queue as
    # negative can collapse every margin near -1. This is not paper Auto TAR.
    model = new_svm(seed).set_params(class_weight="balanced")
    model.fit(X[observed],frame.iloc[observed].label.astype(int))
    remaining = np.flatnonzero(frame.label.to_numpy() == "")
    scores = model.decision_function(X[remaining])
    ranked = remaining[np.lexsort((remaining,-scores))][:top]
    terms = vectorizer.get_feature_names_out()
    output = frame.iloc[ranked].drop(columns="_key").copy()
    output.insert(0, "rank", np.arange(1,len(output)+1))
    output["ranking_score"] = model.decision_function(X[ranked])
    explanations = []
    for i in ranked:
        contributions = X[i].multiply(model.coef_[0]).tocsr()
        good = [(float(v),terms[j]) for j,v in zip(contributions.indices,contributions.data) if v > 0]
        explanations.append("; ".join(t for _,t in sorted(good,reverse=True)[:5]) or "No positive word contributions")
    output["model_word_cues"] = explanations
    def age(value):
        if not value:
            return "unknown"
        try:
            delta = (as_of_date - date.fromisoformat(value)).days
            return str(delta) if delta >= 0 else "future date - verify"
        except ValueError:
            return "invalid date - verify"
    output["event_age_days"] = output.event_date.map(age)
    output["review_action"] = "Verify event, account and matter relevance; assign label 1 or 0"
    # Protect user-supplied strings when the output is opened in Excel.
    safe = output.copy()
    for col in safe.select_dtypes(include="object").columns:
        safe[col] = safe[col].map(lambda s: "'"+s if isinstance(s,str) and s.lstrip().startswith(("=","+","-","@")) else s)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _durable.write_csv(safe, output_path, index=False, quoting=csv.QUOTE_MINIMAL)
    meta = {"as_of":as_of,"seed":seed,"reviewed":len(observed),
            "positives":int((frame.label=="1").sum()),"negatives":int((frame.label=="0").sum()),
            "unreviewed":int((frame.label=="").sum()),"returned":len(output),
            "duplicate_exclusions":dedup_audit,
            "score_meaning":"Uncalibrated SVM ranking margin, not probability of buying",
            "adaptation":"Class-balanced SVM using confirmed labels only; no temporary negatives for small operational queues",
            "scope":"Prototype ranked by supplied text and reviewer labels; dates are displayed, not used in ranking; no IST outcome validation"}
    _durable.write_text(output_path.with_suffix(".audit.json"), json.dumps(meta,indent=2)+"\n")
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",required=True)
    parser.add_argument("--output",default="results/bdr_queue.csv")
    parser.add_argument("--as-of",default=date.today().isoformat())
    parser.add_argument("--top",type=int,default=20)
    args=parser.parse_args()
    out=rank_signals(args.input,args.output,args.as_of,args.top)
    print(out[["rank","account","ranking_score","model_word_cues"]].to_string(index=False))
    print("\nScores rank evidence for human review; they are not probabilities. Update labels in the original CSV and rerun.")


if __name__=="__main__":
    main()
