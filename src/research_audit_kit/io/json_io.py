# SPDX-License-Identifier: Apache-2.0
"""JSON helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..exceptions import InputValidationError


def read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_json_strict(path: str | Path, *, duplicate_key_code: str) -> Any:
    """Read JSON while rejecting duplicate object keys for closed contracts."""

    def object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise InputValidationError(f"{duplicate_key_code}: duplicate JSON key {key!r}")
            value[key] = item
        return value

    return json.loads(
        Path(path).read_text(encoding="utf-8"),
        object_pairs_hook=object_without_duplicates,
    )


def write_json(path: str | Path, value: Any, *, overwrite: bool = True) -> Path:
    target = Path(path)
    if target.exists() and not overwrite:
        raise FileExistsError(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(target)
    return target
