"""Support contamination metrics for selected and Pareto rows."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from ..constants import SUPPORT_LIMITATION

UNSUPPORTED = {"CONDITIONALLY_REJECTED", "OUTSIDE_MARGINAL_RANGE", "BELOW_OBSERVED_BRANCH_SUPPORT"}


def contamination_metrics(
    rows: Iterable[Mapping[str, Any]],
    *,
    support_column: str,
    selected_column: str | None = None,
    pareto_column: str | None = None,
) -> dict[str, Any]:
    materialized = list(rows)
    selected = (
        [row for row in materialized if str(row.get(selected_column, "")).lower() in {"1", "true", "yes"}]
        if selected_column
        else materialized
    )
    pareto = (
        [row for row in materialized if str(row.get(pareto_column, "")).lower() in {"1", "true", "yes"}]
        if pareto_column
        else materialized
    )
    unsupported_selected = sum(str(row.get(support_column)) in UNSUPPORTED for row in selected)
    unsupported_pareto = sum(str(row.get(support_column)) in UNSUPPORTED for row in pareto)
    marginal_illusion = sum(
        str(row.get(support_column)) == "MARGINALLY_SUPPORTED_JOINTLY_UNOBSERVED"
        for row in selected
    )
    return {
        "SER": unsupported_selected / len(selected) if selected else 0.0,
        "PCR": unsupported_pareto / len(pareto) if pareto else 0.0,
        "MSIR": marginal_illusion / len(selected) if selected else 0.0,
        "selected_count": len(selected),
        "pareto_count": len(pareto),
        "unsupported_headline_count": unsupported_selected,
        "limitation": SUPPORT_LIMITATION,
    }

