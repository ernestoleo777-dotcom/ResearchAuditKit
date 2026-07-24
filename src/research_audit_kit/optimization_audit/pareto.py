"""Deterministic Pareto-membership recomputation."""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

from ..exceptions import InputValidationError


def _value(row: Mapping[str, Any], objective: str, direction: str) -> float:
    try:
        value = float(row[objective])
    except (KeyError, TypeError, ValueError) as exc:
        raise InputValidationError(f"invalid objective {objective!r}") from exc
    if direction not in {"min", "max"}:
        raise InputValidationError(f"direction must be min or max, got {direction!r}")
    return value if direction == "min" else -value


def nondominated_indices(
    rows: Iterable[Mapping[str, Any]], objectives: Sequence[tuple[str, str]]
) -> list[int]:
    materialized = list(rows)
    if not objectives:
        raise InputValidationError("at least one objective is required")
    values = [[_value(row, name, direction) for name, direction in objectives] for row in materialized]
    result: list[int] = []
    for index, candidate in enumerate(values):
        dominated = False
        for other_index, other in enumerate(values):
            if index == other_index:
                continue
            if all(left <= right for left, right in zip(other, candidate)) and any(
                left < right for left, right in zip(other, candidate)
            ):
                dominated = True
                break
        if not dominated:
            result.append(index)
    return result


def duplicate_objective_groups(
    rows: Iterable[Mapping[str, Any]], objectives: Sequence[tuple[str, str]]
) -> list[list[int]]:
    groups: dict[tuple[float, ...], list[int]] = {}
    for index, row in enumerate(rows):
        key = tuple(_value(row, name, direction) for name, direction in objectives)
        groups.setdefault(key, []).append(index)
    return [indices for indices in groups.values() if len(indices) > 1]


def validate_pareto_claims(
    rows: Iterable[Mapping[str, Any]],
    objectives: Sequence[tuple[str, str]],
    *,
    claimed_column: str | None = None,
) -> dict[str, Any]:
    materialized = list(rows)
    recomputed = set(nondominated_indices(materialized, objectives))
    claimed: set[int] = set()
    if claimed_column:
        claimed = {
            index
            for index, row in enumerate(materialized)
            if str(row.get(claimed_column, "")).strip().lower() in {"1", "true", "yes"}
        }
    return {
        "row_count": len(materialized),
        "recomputed_indices": sorted(recomputed),
        "claimed_indices": sorted(claimed),
        "false_claims": sorted(claimed - recomputed),
        "missed_claims": sorted(recomputed - claimed) if claimed_column else [],
        "duplicate_objective_groups": duplicate_objective_groups(materialized, objectives),
        "deterministic": True,
    }

