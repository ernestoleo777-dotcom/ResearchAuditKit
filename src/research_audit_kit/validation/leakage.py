"""Conservative metadata-based leakage checks."""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable, Mapping, Sequence


def _roles(manifest: list[Mapping[str, Any]], key: str) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for row in manifest:
        result.setdefault(str(row.get(key, "")), set()).add(str(row.get("role", "")))
    return result


def _cross_role(values: dict[str, set[str]], left: str = "train", right: str = "test") -> list[str]:
    return sorted(key for key, roles in values.items() if left in roles and right in roles)


def audit_split_leakage(
    data_rows: Iterable[Mapping[str, Any]],
    manifest_rows: Iterable[Mapping[str, Any]],
    *,
    id_column: str,
    coordinate_columns: Sequence[str] = (),
    group_column: str | None = None,
    time_column: str | None = None,
    branch_column: str | None = None,
) -> dict[str, Any]:
    data = list(data_rows)
    manifest = list(manifest_rows)
    ids = [str(row.get(id_column, "")) for row in data]
    duplicate_rows = sorted(key for key, count in Counter(ids).items() if count > 1)
    by_id = {str(row.get(id_column, "")): row for row in data}
    id_overlap = _cross_role(_roles(manifest, "row_id"))
    coordinate_overlap = _cross_role(_roles(manifest, "coordinate_id")) if manifest else []
    groups: dict[str, set[str]] = {}
    branches: dict[str, set[str]] = {}
    train_times: list[str] = []
    test_times: list[str] = []
    for item in manifest:
        data_row = by_id.get(str(item.get("row_id", "")), {})
        role = str(item.get("role", ""))
        if group_column:
            groups.setdefault(str(data_row.get(group_column, "")), set()).add(role)
        if branch_column:
            branches.setdefault(str(data_row.get(branch_column, "")), set()).add(role)
        if time_column:
            (train_times if role == "train" else test_times if role == "test" else []).append(
                str(data_row.get(time_column, ""))
            )
    group_overlap = _cross_role(groups) if group_column else []
    branch_overlap = _cross_role(branches) if branch_column else []
    temporal_leakage = bool(train_times and test_times and max(train_times) >= min(test_times))
    calibration_test_overlap = _cross_role(_roles(manifest, "row_id"), "calibration", "test")
    issues = {
        "row_id_overlap": id_overlap,
        "coordinate_overlap": coordinate_overlap,
        "duplicate_rows": duplicate_rows,
        "group_overlap": group_overlap,
        "branch_overlap": branch_overlap,
        "temporal_leakage": temporal_leakage,
        "calibration_test_overlap": calibration_test_overlap,
    }
    detected = any(bool(value) for value in issues.values())
    return {"status": "FAIL" if detected else "PASS", "issues": issues, "metadata_only": True}


def file_overlap(train_files: Iterable[str], test_files: Iterable[str]) -> list[str]:
    return sorted(set(train_files) & set(test_files))

