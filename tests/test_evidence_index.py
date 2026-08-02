from __future__ import annotations

import json

import pytest

from research_audit_kit.exceptions import InputValidationError
from research_audit_kit.governance.evidence_index import build_evidence_index, write_evidence_index


def roles() -> dict:
    return {
        "roles": [
            {"role_id": "inspector", "role_label": "Synthetic inspector"},
            {"role_id": "author", "role_label": "Synthetic author"},
        ]
    }


def records() -> dict:
    return {
        "records": [
            {
                "evidence_id": "e-2",
                "role_id": "inspector",
                "evidence_kind": "note",
                "subject_ref": "items/two",
                "recorded_at": "2026-01-01T00:00:00Z",
                "custody_status": "VERIFIED",
            },
            {
                "evidence_id": "e-1",
                "role_id": "author",
                "evidence_kind": "note",
                "subject_ref": "opaque-subject",
                "recorded_at": "2026-01-01T00:00:00Z",
                "custody_status": "DECLARED",
            },
        ]
    }


def test_evidence_index_is_sorted_and_writes_both_formats(tmp_path):
    result = build_evidence_index(roles(), records())
    json_path, csv_path = write_evidence_index(result, tmp_path)
    assert [item["role_id"] for item in result["roles"]] == ["author", "inspector"]
    assert [item["evidence_id"] for item in result["records"]] == ["e-1", "e-2"]
    assert result["counts"]["by_evidence_kind"] == {"note": 2}
    assert result["counts"]["by_custody_status"] == {"DECLARED": 1, "VERIFIED": 1}
    assert json.loads(json_path.read_text())["status"] == "PASS"
    assert csv_path.read_text().splitlines()[0].startswith("evidence_id,")


@pytest.mark.parametrize(
    ("role_value", "record_value", "code"),
    [
        ({"invalid": []}, records(), "EVIDENCE_INDEX_INVALID_ROLES"),
        (roles(), {"invalid": []}, "EVIDENCE_INDEX_INVALID_RECORDS"),
        (
            {"roles": [roles()["roles"][0], roles()["roles"][0]]},
            records(),
            "EVIDENCE_INDEX_DUPLICATE_ROLE_ID",
        ),
        (
            roles(),
            {"records": [records()["records"][0], records()["records"][0]]},
            "EVIDENCE_INDEX_DUPLICATE_EVIDENCE_ID",
        ),
        (
            roles(),
            {"records": [{**records()["records"][0], "role_id": "missing"}]},
            "EVIDENCE_INDEX_UNKNOWN_ROLE",
        ),
        (
            roles(),
            {"records": [{**records()["records"][0], "subject_ref": "../outside"}]},
            "EVIDENCE_INDEX_UNSAFE_REFERENCE",
        ),
        (
            roles(),
            {"records": [{**records()["records"][0], "custody_status": "INVALID"}]},
            "EVIDENCE_INDEX_INVALID_CUSTODY_STATUS",
        ),
    ],
)
def test_evidence_index_rejects_invalid_inputs(role_value, record_value, code):
    with pytest.raises(InputValidationError, match=code):
        build_evidence_index(role_value, record_value)
