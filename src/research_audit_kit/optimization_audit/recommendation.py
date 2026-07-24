"""Recommendation coordinate support audit."""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

from ..constants import SUPPORT_LIMITATION
from ..support.taxonomy import classify_candidate


def audit_recommendations(
    recommendations: Iterable[Mapping[str, Any]],
    observed_rows: Iterable[Mapping[str, Any]],
    features: Sequence[str],
    *,
    schema: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    observed = list(observed_rows)
    output: list[dict[str, Any]] = []
    for source_row, recommendation in enumerate(recommendations):
        classification = classify_candidate(
            recommendation, observed, features, schema=schema
        )
        output.append(
            {
                "source_row": source_row,
                **{feature: recommendation.get(feature) for feature in features},
                "exact_observed": classification["status"] == "OBSERVED_EXACT",
                "marginally_supported": classification["status"]
                not in {"OUTSIDE_MARGINAL_RANGE", "UNCLASSIFIED"},
                "jointly_supported": classification["status"] == "OBSERVED_EXACT",
                "conditional_status": classification.get("conditional_status", classification["status"]),
                "support_status": classification["status"],
                "allowed_interpretation": SUPPORT_LIMITATION,
            }
        )
    return output

