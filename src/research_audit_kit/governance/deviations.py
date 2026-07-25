"""Append-only protocol-deviation ledger."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from ..exceptions import InputValidationError
from ..io.csv_io import read_csv_rows, write_csv_rows

DEVIATION_FIELDS = [
    "deviation_id",
    "triggering_action",
    "protocol_rule",
    "affected_files",
    "affected_metrics",
    "isolation_status",
    "adjudication_status",
    "allowed_usage",
    "forbidden_usage",
]


def normalize_deviation(value: Mapping[str, Any]) -> dict[str, str]:
    missing = [field for field in DEVIATION_FIELDS if field not in value]
    if missing:
        raise InputValidationError(f"missing deviation fields: {missing}")
    row = {field: value[field] for field in DEVIATION_FIELDS}
    for field in ("affected_files", "affected_metrics"):
        if isinstance(row[field], list):
            row[field] = ";".join(str(item) for item in row[field])
    return {field: str(row[field]) for field in DEVIATION_FIELDS}


def record_deviation(path: str | Path, value: Mapping[str, Any]) -> dict[str, str]:
    target = Path(path)
    row = normalize_deviation(value)
    target.parent.mkdir(parents=True, exist_ok=True)
    existing_ids: set[str] = set()
    existing_rows: list[dict[str, str]] = []
    if target.exists():
        existing_rows = read_csv_rows(target)
        existing_ids = {item["deviation_id"] for item in existing_rows}
    if row["deviation_id"] in existing_ids:
        raise InputValidationError("deviation_id already exists; ledger is append-only")
    write_csv_rows(target, [*existing_rows, row], DEVIATION_FIELDS, overwrite=True)
    return row
