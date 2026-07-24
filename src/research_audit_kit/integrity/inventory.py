"""Recursive relative-path repository inventory."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from ..exceptions import UnsafePathError
from ..io.csv_io import write_csv_rows
from ..io.json_io import write_json
from .hashing import sha256_file
from .policy import IntegrityPolicy

INVENTORY_FIELDS = [
    "path",
    "size_bytes",
    "modified_at",
    "sha256",
    "category",
    "gate_status",
    "exclusion_reason",
]


def safe_relative(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise UnsafePathError(f"{path} escapes {root}") from exc


def build_inventory(
    root: str | Path,
    policy: IntegrityPolicy,
    *,
    omit_paths: Iterable[str] = (),
) -> list[dict[str, object]]:
    base = Path(root).resolve()
    if not base.is_dir():
        raise NotADirectoryError(base)
    omitted = set(omit_paths)
    rows: list[dict[str, object]] = []
    for path in sorted(p for p in base.rglob("*") if p.is_file()):
        relative = safe_relative(base, path)
        if relative in omitted or relative.endswith(".tmp"):
            continue
        category, reason = policy.classify(relative)
        stat = path.stat()
        gate_status = "INCLUDED" if category == "scientific_asset" else "EXCLUDED_OR_WARNING"
        rows.append(
            {
                "path": relative,
                "size_bytes": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                "sha256": sha256_file(path),
                "category": category,
                "gate_status": gate_status,
                "exclusion_reason": "" if category == "scientific_asset" else reason,
            }
        )
    present = {str(row["path"]) for row in rows}
    for required in policy.required_files:
        if required not in present and required not in omitted:
            rows.append(
                {
                    "path": required,
                    "size_bytes": 0,
                    "modified_at": "",
                    "sha256": "",
                    "category": "scientific_asset",
                    "gate_status": "MISSING_REQUIRED",
                    "exclusion_reason": "required file is missing",
                }
            )
    return sorted(rows, key=lambda row: str(row["path"]))


def write_inventory(rows: list[dict[str, object]], out_dir: str | Path) -> tuple[Path, Path]:
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    csv_path = write_csv_rows(target / "inventory.csv", rows, INVENTORY_FIELDS)
    json_path = write_json(target / "inventory.json", {"assets": rows})
    return csv_path, json_path

