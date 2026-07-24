"""CSV helpers with explicit overwrite behavior."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, Mapping, Any

from ..exceptions import AuditError


def read_csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


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
        writer.writerows(rows)
    temporary.replace(target)
    return target

