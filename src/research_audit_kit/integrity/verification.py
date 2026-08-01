# SPDX-License-Identifier: Apache-2.0
"""Baseline verification with warnings separated from failures."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from ..constants import STATUS_FAIL, STATUS_PASS, STATUS_PASS_WITH_WARNINGS
from ..io.csv_io import read_csv_rows, write_csv_rows
from ..io.json_io import write_json
from .hashing import sha256_file
from .inventory import build_inventory
from .policy import IntegrityPolicy

VERIFICATION_FIELDS = ["path", "category", "expected_sha256", "current_sha256", "status"]


def verify_baseline(root: str | Path, baseline_path: str | Path) -> dict[str, object]:
    base = Path(root).resolve()
    baseline = Path(baseline_path)
    rows = read_csv_rows(baseline)
    if not rows:
        raise ValueError("baseline is empty")
    policy = IntegrityPolicy.from_dict(json.loads(rows[0]["policy_json"]))
    expected = {row["path"]: row for row in rows}
    omit: set[str] = set()
    try:
        relative_baseline = baseline.resolve().relative_to(base).as_posix()
        omit = {relative_baseline, relative_baseline + ".sha256", relative_baseline + ".tmp"}
    except ValueError:
        pass
    current_rows = build_inventory(base, policy, omit_paths=omit)
    current = {str(row["path"]): row for row in current_rows}
    results: list[dict[str, str]] = []
    for path, row in sorted(expected.items()):
        category = row["category"]
        if path not in current or current[path]["gate_status"] == "MISSING_REQUIRED":
            status = "MISSING" if category == "scientific_asset" else "EXCLUDED_CHANGED"
            current_hash = ""
        else:
            current_hash = str(current[path]["sha256"])
            changed = current_hash != row["sha256"]
            if category == "scientific_asset":
                status = "MISMATCH" if changed else "MATCH"
            elif category == "volatile_metadata":
                status = "VOLATILE_WARNING" if changed else "EXCLUDED_MATCH"
            else:
                status = "EXCLUDED_CHANGED" if changed else "EXCLUDED_MATCH"
        results.append(
            {
                "path": path,
                "category": category,
                "expected_sha256": row["sha256"],
                "current_sha256": current_hash,
                "status": status,
            }
        )
    for path, row in sorted(current.items()):
        if path in expected:
            continue
        category = str(row["category"])
        if category == "volatile_metadata":
            status = "VOLATILE_WARNING"
        elif category in {"scientific_asset", "unclassified_file"}:
            status = "NEW_UNCLASSIFIED"
        else:
            status = "EXCLUDED_MATCH"
        results.append(
            {
                "path": path,
                "category": category,
                "expected_sha256": "",
                "current_sha256": str(row["sha256"]),
                "status": status,
            }
        )
    counts = Counter(row["status"] for row in results)
    failure = counts["MISMATCH"] + counts["MISSING"]
    if policy.unexpected_scientific_file_policy == "fail":
        failure += sum(
            row["status"] == "NEW_UNCLASSIFIED" and row["category"] == "scientific_asset"
            for row in results
        )
    warnings = counts["VOLATILE_WARNING"] + counts["EXCLUDED_CHANGED"]
    gate_status = STATUS_FAIL if failure else (STATUS_PASS_WITH_WARNINGS if warnings else STATUS_PASS)
    return {
        "policy_id": policy.policy_id,
        "baseline_id": rows[0]["baseline_id"],
        "root_identifier": base.name,
        "gate_status": gate_status,
        "counts": dict(counts),
        "results": results,
        "baseline_sha256": sha256_file(baseline),
    }


def write_verification(result: dict[str, object], out_dir: str | Path) -> tuple[Path, Path]:
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    csv_path = write_csv_rows(
        target / "verification.csv",
        result["results"],
        VERIFICATION_FIELDS,
    )
    json_path = write_json(
        target / "summary.json",
        {key: value for key, value in result.items() if key != "results"},
    )
    return csv_path, json_path
