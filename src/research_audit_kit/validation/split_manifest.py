"""Portable deterministic split manifests."""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

from ..exceptions import InputValidationError
from ..integrity.hashing import stable_object_hash

MANIFEST_FIELDS = [
    "row_id",
    "coordinate_id",
    "role",
    "split_family",
    "fold_id",
    "seed",
    "group_label",
    "dataset_hash",
]


def dataset_hash(rows: Iterable[Mapping[str, Any]]) -> str:
    normalized = [dict(sorted((str(key), str(value)) for key, value in row.items())) for row in rows]
    return stable_object_hash(normalized)


def coordinate_id(row: Mapping[str, Any], columns: Sequence[str]) -> str:
    return stable_object_hash([str(row.get(column, "")) for column in columns])[:16]


def build_split_manifest(
    rows: Iterable[Mapping[str, Any]],
    assignments: Iterable[Mapping[str, Any]],
    *,
    id_column: str,
    coordinate_columns: Sequence[str],
    split_family: str,
    fold_id: str,
    seed: int,
    group_column: str | None = None,
) -> list[dict[str, Any]]:
    materialized = list(rows)
    by_id = {str(row[id_column]): row for row in materialized}
    if len(by_id) != len(materialized):
        raise InputValidationError("row ids must be unique")
    digest = dataset_hash(materialized)
    output: list[dict[str, Any]] = []
    for assignment in assignments:
        row_id = str(assignment["row_id"])
        role = str(assignment["role"])
        if row_id not in by_id:
            raise InputValidationError(f"assignment references unknown row {row_id}")
        if role not in {"train", "test", "calibration", "validation"}:
            raise InputValidationError(f"invalid split role {role}")
        row = by_id[row_id]
        output.append(
            {
                "row_id": row_id,
                "coordinate_id": coordinate_id(row, coordinate_columns),
                "role": role,
                "split_family": split_family,
                "fold_id": fold_id,
                "seed": seed,
                "group_label": str(row.get(group_column, "")) if group_column else "",
                "dataset_hash": digest,
            }
        )
    return sorted(output, key=lambda row: (str(row["fold_id"]), str(row["role"]), str(row["row_id"])))

