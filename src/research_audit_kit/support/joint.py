# SPDX-License-Identifier: Apache-2.0
"""Exact and subset joint-support operations."""

from __future__ import annotations

import itertools
from typing import Any, Iterable, Mapping, Sequence

from ..exceptions import InputValidationError


def tuple_key(row: Mapping[str, Any], features: Sequence[str]) -> tuple[str, ...]:
    return tuple(str(row.get(feature, "")) for feature in features)


def joint_support(
    rows: Iterable[Mapping[str, Any]], features: Sequence[str]
) -> set[tuple[str, ...]]:
    if not features:
        raise InputValidationError("at least one feature is required")
    return {tuple_key(row, features) for row in rows}


def exact_membership(
    candidate: Mapping[str, Any], rows: Iterable[Mapping[str, Any]], features: Sequence[str]
) -> bool:
    return tuple_key(candidate, features) in joint_support(rows, features)


def pairwise_support(
    rows: Iterable[Mapping[str, Any]], features: Sequence[str]
) -> dict[str, set[tuple[str, str]]]:
    materialized = list(rows)
    return {
        f"{left}|{right}": joint_support(materialized, [left, right])
        for left, right in itertools.combinations(features, 2)
    }


def observed_combination_table(
    rows: Iterable[Mapping[str, Any]], features: Sequence[str]
) -> list[dict[str, Any]]:
    counts: dict[tuple[str, ...], int] = {}
    for row in rows:
        key = tuple_key(row, features)
        counts[key] = counts.get(key, 0) + 1
    return [
        {**dict(zip(features, key)), "frequency": count}
        for key, count in sorted(counts.items())
    ]


def cartesian_gap(
    rows: Iterable[Mapping[str, Any]],
    features: Sequence[str],
    *,
    discrete: Sequence[str] = (),
    supplied_grid: Mapping[str, Sequence[Any]] | None = None,
) -> dict[str, Any]:
    materialized = list(rows)
    grid = dict(supplied_grid or {})
    discrete_set = set(discrete)
    for feature in features:
        if feature not in grid and feature not in discrete_set:
            raise InputValidationError(
                f"exact Cartesian gap requires {feature!r} to be discrete or have a supplied grid"
            )
        grid.setdefault(feature, sorted({str(row.get(feature, "")) for row in materialized}))
    marginal_size = 1
    for feature in features:
        marginal_size *= len(grid[feature])
    observed = len(joint_support(materialized, features))
    absent = marginal_size - observed
    return {
        "marginal_cartesian_size": marginal_size,
        "observed_joint_size": observed,
        "absent_combination_count": absent,
        "gap_ratio": absent / marginal_size if marginal_size else 0.0,
    }

