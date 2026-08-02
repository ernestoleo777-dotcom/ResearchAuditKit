# SPDX-License-Identifier: Apache-2.0
"""Deterministic indexing of role-labelled evidence records."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from ..constants import STATUS_PASS
from ..exceptions import InputValidationError
from ..integrity.portable import normalize_portable_reference
from ..io.csv_io import write_csv_rows
from ..io.json_io import write_json

CUSTODY_STATUSES = {"DECLARED", "SEALED", "VERIFIED", "UNVERIFIED", "RETIRED"}
EVIDENCE_INDEX_FIELDS = [
    "evidence_id",
    "role_id",
    "evidence_kind",
    "subject_ref",
    "recorded_at",
    "custody_status",
]
_ROLE_FIELDS = {"role_id", "role_label"}
_RECORD_FIELDS = set(EVIDENCE_INDEX_FIELDS)


def _error(code: str, message: str) -> None:
    raise InputValidationError(f"{code}: {message}")


def _string(value: Mapping[str, Any], field: str, code: str) -> str:
    raw = value.get(field)
    if not isinstance(raw, str) or not raw.strip():
        _error(code, f"{field} must be a non-empty string")
    return raw


def normalize_roles(value: Mapping[str, Any]) -> list[dict[str, str]]:
    if not isinstance(value, Mapping) or set(value) != {"roles"} or not isinstance(value["roles"], list):
        _error("EVIDENCE_INDEX_INVALID_ROLES", "roles document must contain only a roles array")
    output: list[dict[str, str]] = []
    identifiers: set[str] = set()
    for item in value["roles"]:
        if not isinstance(item, Mapping) or set(item) != _ROLE_FIELDS:
            _error("EVIDENCE_INDEX_INVALID_ROLES", "role has missing or undeclared fields")
        role_id = _string(item, "role_id", "EVIDENCE_INDEX_INVALID_ROLES")
        if role_id in identifiers:
            _error("EVIDENCE_INDEX_DUPLICATE_ROLE_ID", f"duplicate role_id {role_id!r}")
        identifiers.add(role_id)
        output.append({"role_id": role_id, "role_label": _string(item, "role_label", "EVIDENCE_INDEX_INVALID_ROLES")})
    return sorted(output, key=lambda item: item["role_id"])


def normalize_records(value: Mapping[str, Any], role_ids: set[str]) -> list[dict[str, str]]:
    if not isinstance(value, Mapping) or set(value) != {"records"} or not isinstance(value["records"], list):
        _error("EVIDENCE_INDEX_INVALID_RECORDS", "records document must contain only a records array")
    output: list[dict[str, str]] = []
    identifiers: set[str] = set()
    for item in value["records"]:
        if not isinstance(item, Mapping) or set(item) != _RECORD_FIELDS:
            _error("EVIDENCE_INDEX_INVALID_RECORDS", "record has missing or undeclared fields")
        evidence_id = _string(item, "evidence_id", "EVIDENCE_INDEX_INVALID_RECORDS")
        if evidence_id in identifiers:
            _error("EVIDENCE_INDEX_DUPLICATE_EVIDENCE_ID", f"duplicate evidence_id {evidence_id!r}")
        identifiers.add(evidence_id)
        role_id = _string(item, "role_id", "EVIDENCE_INDEX_INVALID_RECORDS")
        if role_id not in role_ids:
            _error("EVIDENCE_INDEX_UNKNOWN_ROLE", f"unknown role_id {role_id!r}")
        custody_status = _string(item, "custody_status", "EVIDENCE_INDEX_INVALID_RECORDS")
        if custody_status not in CUSTODY_STATUSES:
            _error("EVIDENCE_INDEX_INVALID_CUSTODY_STATUS", f"invalid custody_status {custody_status!r}")
        try:
            subject_ref = normalize_portable_reference(
                item["subject_ref"],
                code="EVIDENCE_INDEX_UNSAFE_REFERENCE",
                field="subject_ref",
            )
        except InputValidationError as exc:
            if str(exc).startswith("EVIDENCE_INDEX_UNSAFE_REFERENCE"):
                raise
            _error("EVIDENCE_INDEX_UNSAFE_REFERENCE", "subject_ref is invalid")
        output.append(
            {
                "evidence_id": evidence_id,
                "role_id": role_id,
                "evidence_kind": _string(item, "evidence_kind", "EVIDENCE_INDEX_INVALID_RECORDS"),
                "subject_ref": subject_ref,
                "recorded_at": _string(item, "recorded_at", "EVIDENCE_INDEX_INVALID_RECORDS"),
                "custody_status": custody_status,
            }
        )
    return sorted(output, key=lambda item: item["evidence_id"])


def build_evidence_index(roles: Mapping[str, Any], records: Mapping[str, Any]) -> dict[str, Any]:
    normalized_roles = normalize_roles(roles)
    normalized_records = normalize_records(records, {item["role_id"] for item in normalized_roles})
    return {
        "status": STATUS_PASS,
        "roles": normalized_roles,
        "records": normalized_records,
        "counts": {
            "total": len(normalized_records),
            "by_role": dict(sorted(Counter(item["role_id"] for item in normalized_records).items())),
            "by_evidence_kind": dict(
                sorted(Counter(item["evidence_kind"] for item in normalized_records).items())
            ),
            "by_custody_status": dict(
                sorted(Counter(item["custody_status"] for item in normalized_records).items())
            ),
        },
        "limitation": "An index records asserted custody metadata only; it does not adjudicate evidence or establish scientific correctness.",
    }


def write_evidence_index(result: Mapping[str, Any], out_dir: str | Path) -> tuple[Path, Path]:
    target = Path(out_dir)
    json_path = write_json(target / "evidence_index.json", dict(result))
    csv_path = write_csv_rows(target / "evidence_index.csv", result["records"], EVIDENCE_INDEX_FIELDS)
    return json_path, csv_path
