"""Determinism comparisons."""

from __future__ import annotations

from typing import Any

from ..integrity.hashing import stable_object_hash


def deterministic_hash(value: Any) -> str:
    return stable_object_hash(value)


def compare_repeated_outputs(first: Any, second: Any) -> dict[str, Any]:
    first_hash = deterministic_hash(first)
    second_hash = deterministic_hash(second)
    return {
        "deterministic": first_hash == second_hash,
        "first_hash": first_hash,
        "second_hash": second_hash,
    }


def stable_order(rows: list[dict[str, Any]], keys: list[str]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: tuple(str(row.get(key, "")) for key in keys))

