"""Candidate support taxonomy without physical interpretation."""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

from .conditional import evaluate_conditional_rules
from .joint import exact_membership


def _range_status(candidate: Mapping[str, Any], rows: list[Mapping[str, Any]], features: Sequence[str]) -> bool:
    for feature in features:
        observed = [row.get(feature) for row in rows]
        value = candidate.get(feature)
        try:
            numeric = [float(item) for item in observed]
            if float(value) < min(numeric) or float(value) > max(numeric):
                return False
        except (TypeError, ValueError):
            if str(value) not in {str(item) for item in observed}:
                return False
    return True


def classify_candidate(
    candidate: Mapping[str, Any],
    rows: Iterable[Mapping[str, Any]],
    features: Sequence[str],
    *,
    schema: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    materialized = list(rows)
    if not materialized:
        return {"status": "UNCLASSIFIED", "conditional_status": "UNKNOWN"}
    if exact_membership(candidate, materialized, features):
        return {"status": "OBSERVED_EXACT", "conditional_status": "OBSERVED"}
    if not _range_status(candidate, materialized, features):
        return {"status": "OUTSIDE_MARGINAL_RANGE", "conditional_status": "UNKNOWN"}
    marginal = all(
        str(candidate.get(feature)) in {str(row.get(feature)) for row in materialized}
        for feature in features
    )
    if schema:
        conditional = evaluate_conditional_rules(candidate, schema)
        if conditional["status"] == "CONDITIONALLY_REJECTED":
            return {"status": "CONDITIONALLY_REJECTED", **conditional}
        if conditional["status"] == "CONDITIONALLY_SUPPORTED":
            return {"status": "CONDITIONALLY_SUPPORTED", **conditional}
    if marginal:
        return {
            "status": "MARGINALLY_SUPPORTED_JOINTLY_UNOBSERVED",
            "conditional_status": "UNKNOWN",
        }
    return {"status": "UNCLASSIFIED", "conditional_status": "UNKNOWN"}

