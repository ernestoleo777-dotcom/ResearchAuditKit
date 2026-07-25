"""CSV helpers with explicit overwrite behavior."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, Mapping, Any

from ..exceptions import AuditError, InputValidationError, UnsupportedFormatError


def read_csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise UnsupportedFormatError("CSV is empty and has no header") from exc
        if not header or any(not column.strip() for column in header):
            raise UnsupportedFormatError("CSV header contains an empty column name")
        if len(set(header)) != len(header):
            raise UnsupportedFormatError("CSV header contains duplicate column names")
        rows: list[dict[str, str]] = []
        for line_number, values in enumerate(reader, start=2):
            if not values or all(not value.strip() for value in values):
                continue
            if len(values) != len(header):
                raise InputValidationError(
                    f"CSV row {line_number} has {len(values)} values; expected {len(header)}"
                )
            rows.append(dict(zip(header, values)))
        return rows


def sanitize_csv_cell(value: Any) -> Any:
    """Neutralize spreadsheet formulas while preserving ordinary negative numbers."""
    if not isinstance(value, str) or not value:
        return value
    if value[0] in {"=", "+", "@"}:
        return "'" + value
    if value[0] == "-":
        try:
            float(value)
        except ValueError:
            return "'" + value
    return value


def write_csv_rows(
    path: str | Path,
    rows: Iterable[Mapping[str, Any]],
    fieldnames: list[str],
    *,
    overwrite: bool = True,
) -> Path:
    target = Path(path)
    if target.exists() and not overwrite:
        raise AuditError(f"Refusing to overwrite {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(
            {key: sanitize_csv_cell(value) for key, value in row.items()} for row in rows
        )
    temporary.replace(target)
    return target
