"""Conservative missingness-pattern classification."""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

from .conditional import evaluate_conditional_rules
from .joint import cartesian_gap


def classify_missingness(
    rows: Iterable[Mapping[str, Any]],
    features: Sequence[str],
    *,
    discrete: Sequence[str],
    schema: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    materialized = list(rows)
    gap = cartesian_gap(materialized, features, discrete=discrete)
    if len(materialized) < 4:
        status = "INSUFFICIENT_EVIDENCE"
    elif schema:
        rejected = sum(
            evaluate_conditional_rules(row, schema)["status"] == "CONDITIONALLY_REJECTED"
            for row in materialized
        )
        status = "SYSTEMATIC_CONDITIONAL_MISSING" if rejected == 0 and gap["gap_ratio"] > 0 else "RANDOM_OR_UNSTRUCTURED_MISSING"
    elif gap["gap_ratio"] >= 0.5:
        status = "STRUCTURAL_PATTERN_CANDIDATE"
    elif gap["gap_ratio"] > 0:
        status = "RANDOM_OR_UNSTRUCTURED_MISSING"
    else:
        status = "RANDOM_OR_UNSTRUCTURED_MISSING"
    return {"classification": status, **gap, "physical_interpretation": "NOT_INFERRED"}

