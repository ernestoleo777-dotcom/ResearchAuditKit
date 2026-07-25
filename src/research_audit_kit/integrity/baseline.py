"""Versioned portable baselines with companion hashes."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from ..exceptions import BaselineExistsError
from ..io.csv_io import write_csv_rows
from .hashing import sha256_file
from .inventory import build_inventory
from .policy import IntegrityPolicy

BASELINE_FIELDS = [
    "baseline_id",
    "policy_id",
    "created_at",
    "root_identifier",
    "path",
    "size_bytes",
    "sha256",
    "category",
    "policy_json",
    "forced_overwrite",
]


def _atomic_write_text(path: Path, text: str) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def freeze_baseline(
    root: str | Path,
    policy: IntegrityPolicy,
    baseline_path: str | Path,
    *,
    baseline_id: str | None = None,
    force: bool = False,
) -> dict[str, object]:
    base = Path(root).resolve()
    target = Path(baseline_path)
    companion = target.with_name(target.name + ".sha256")
    if (target.exists() or companion.exists()) and not force:
        raise BaselineExistsError(f"Baseline exists: {target}")
    identifier = baseline_id or datetime.now(timezone.utc).strftime("baseline-%Y%m%dT%H%M%SZ")
    omitted: set[str] = set()
    candidate = target.resolve()
    try:
        relative_target = candidate.relative_to(base).as_posix()
        omitted = {
            relative_target,
            relative_target + ".sha256",
            relative_target + ".tmp",
        }
    except ValueError:
        omitted = set()
    inventory = build_inventory(base, policy, omit_paths=omitted)
    created = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    policy_json = json.dumps(policy.to_dict(), sort_keys=True, separators=(",", ":"))
    rows = [
        {
            "baseline_id": identifier,
            "policy_id": policy.policy_id,
            "created_at": created,
            "root_identifier": base.name,
            "path": row["path"],
            "size_bytes": row["size_bytes"],
            "sha256": row["sha256"],
            "category": row["category"],
            "policy_json": policy_json,
            "forced_overwrite": str(bool(force)).lower(),
        }
        for row in inventory
    ]
    write_csv_rows(target, rows, BASELINE_FIELDS, overwrite=True)
    digest = sha256_file(target)
    _atomic_write_text(companion, f"{digest}  {target.name}\n")
    return {
        "baseline_id": identifier,
        "policy_id": policy.policy_id,
        "asset_count": len(rows),
        "baseline_sha256": digest,
        "forced_overwrite": bool(force),
        "root_identifier": base.name,
    }
