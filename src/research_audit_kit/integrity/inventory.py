"""Recursive relative-path repository inventory."""

from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Iterable

from ..exceptions import InputValidationError, UnsafePathError, UnsupportedFormatError
from ..io.csv_io import write_csv_rows
from ..io.json_io import write_json
from .hashing import sha256_bytes, sha256_file
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
    casefolded: dict[str, str] = {}
    for path in sorted(base.rglob("*")):
        relative_lexical = path.relative_to(base).as_posix()
        if any(
            relative_lexical == omitted_path
            or relative_lexical.startswith(omitted_path.rstrip("/") + "/")
            for omitted_path in omitted
        ) or relative_lexical.endswith(".tmp"):
            continue
        if path.is_symlink():
            resolved = path.resolve(strict=False)
            try:
                resolved.relative_to(base)
            except ValueError as exc:
                raise UnsafePathError(f"symlink escapes repository root: {relative_lexical}") from exc
            stat = path.lstat()
            rows.append(
                {
                    "path": relative_lexical,
                    "size_bytes": stat.st_size,
                    "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                    "sha256": sha256_bytes(os.readlink(path).encode("utf-8")),
                    "category": "unclassified_file",
                    "gate_status": "EXCLUDED_OR_WARNING",
                    "exclusion_reason": "symlink recorded but target was not followed",
                }
            )
            continue
        if path.is_dir():
            continue
        if not path.is_file():
            raise UnsupportedFormatError(f"unsupported filesystem object: {relative_lexical}")
        relative = safe_relative(base, path)
        folded = relative.casefold()
        if folded in casefolded and casefolded[folded] != relative:
            raise InputValidationError(
                f"case-insensitive path collision: {casefolded[folded]!r} and {relative!r}"
            )
        casefolded[folded] = relative
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
