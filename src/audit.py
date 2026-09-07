"""Schema 3 audit serialization and model-free replay. No collection access."""
from copy import deepcopy


def seed_round(row, batch_size):
    return dict(round_index=0, fit_index=None, fit=None, candidate_margins=None,
                margin_unavailable_reason="seed_before_ranking", selected_rows=[int(row)],
                selection_operators=["seed"], batch_size_before_growth=batch_size,
                batch_size_after_growth=batch_size)


def externalize_round(record, document_ids):
    """Preserve numeric ranking rows and their external string identities."""
    record = deepcopy(record)
    record["selected_document_ids"] = [str(document_ids[r]) for r in record["selected_rows"]]
    fit = record["fit"]
    record["temporary_negative_document_ids"] = ([] if fit is None else
        [str(document_ids[r]) for r in fit["temporary_negative_rows"]])
    margins = record["candidate_margins"]
    if margins is not None:
        margins["document_ids"] = [str(document_ids[r]) for r in margins["rows"]]
    return record


def replay_row_order(audit):
    """Reconstruct from round events alone; never read the flat row_order field."""
    if audit.get("schema_version") != 3:
        raise ValueError("Expected audit schema 3")
    order, seen_ids = [], set()
    seen_rows = set()
    for index, record in enumerate(audit["rounds"]):
        if record["round_index"] != index:
            raise ValueError("Noncontiguous round indices")
        rows, ids = record["selected_rows"], record["selected_document_ids"]
        operators = record["selection_operators"]
        if not rows or len(rows) != len(ids) or len(rows) != len(operators):
            raise ValueError("Invalid selection alignment")
        for row, doc_id, operator in zip(rows, ids, operators):
            if not isinstance(row, int) or isinstance(row, bool) or row < 0 or not isinstance(doc_id, str):
                raise ValueError("Invalid document identity")
            if row in seen_rows or doc_id in seen_ids:
                raise ValueError("Repeated review")
            if operator not in {"exploit", "explore", "seed", "random"}:
                raise ValueError("Unknown selection operator")
            if (index == 0) != (operator == "seed"):
                raise ValueError("Seed must occur only in round zero")
            seen_rows.add(row); seen_ids.add(doc_id); order.append(row)
    if not order:
        raise ValueError("Missing seed round")
    return order
