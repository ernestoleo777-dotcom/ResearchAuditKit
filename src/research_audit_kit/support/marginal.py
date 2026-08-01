# SPDX-License-Identifier: Apache-2.0
"""Marginal support summaries."""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable, Mapping


def _numeric(values: list[str]) -> list[float] | None:
    try:
        return [float(value) for value in values]
    except (TypeError, ValueError):
        return None


def marginal_support(
    rows: Iterable[Mapping[str, Any]], features: Iterable[str]
) -> dict[str, dict[str, Any]]:
    materialized = list(rows)
    report: dict[str, dict[str, Any]] = {}
    for feature in features:
        raw = [row.get(feature) for row in materialized]
        missing = sum(value is None or str(value).strip() == "" for value in raw)
        values = [str(value) for value in raw if value is not None and str(value).strip() != ""]
        counts = Counter(values)
        numeric = _numeric(values)
        report[feature] = {
            "unique_values": sorted(counts, key=lambda value: (float(value) if numeric else value)),
            "unique_count": len(counts),
            "min": min(numeric) if numeric else (min(values) if values else None),
            "max": max(numeric) if numeric else (max(values) if values else None),
            "missing_values": missing,
            "frequency": dict(sorted(counts.items())),
        }
    return report

