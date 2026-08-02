from __future__ import annotations

import json

import pytest

from research_audit_kit.exceptions import InputValidationError
from research_audit_kit.integrity.prediction_seal import (
    canonical_prediction_declaration,
    seal_prediction_declaration,
    verify_prediction_seal,
    write_prediction_seal,
)


def declaration() -> dict:
    return {
        "declaration_id": "synthetic-declaration",
        "declared_at": "2026-01-01T00:00:00Z",
        "predictions": [
            {
                "prediction_id": "p-2",
                "subject_ref": "items/two",
                "prediction_value": {"label": "opaque", "score": 0.5},
                "producer_role": "author",
                "method_version": "v1",
            },
            {
                "prediction_id": "p-1",
                "subject_ref": "subject-one",
                "prediction_value": ["opaque", 1],
                "producer_role": "author",
                "method_version": "v1",
            },
        ],
    }


def test_prediction_seal_is_stable_for_reordered_records(tmp_path):
    first = declaration()
    second = declaration()
    second["predictions"].reverse()
    first_seal = seal_prediction_declaration(first)
    second_seal = seal_prediction_declaration(second)
    assert first_seal["declaration_sha256"] == second_seal["declaration_sha256"]
    assert [item["prediction_id"] for item in first_seal["declaration"]["predictions"]] == ["p-1", "p-2"]
    target = write_prediction_seal(first_seal, tmp_path / "seal.json")
    assert json.loads(target.read_text())["declaration_sha256"] == first_seal["declaration_sha256"]


def test_prediction_verify_detects_changed_declaration():
    sealed = seal_prediction_declaration(declaration())
    changed = declaration()
    changed["predictions"][0]["prediction_value"] = "different opaque value"
    result = verify_prediction_seal(changed, sealed)
    assert result["status"] == "FAIL"
    assert result["failure_codes"] == ["PREDICTION_VERIFY_DIGEST_MISMATCH"]


def test_prediction_verify_detects_changed_sealing_metadata():
    sealed = seal_prediction_declaration(declaration())
    sealed["sealed_at"] = "2030-01-01T00:00:00+00:00"
    with pytest.raises(InputValidationError, match="PREDICTION_VERIFY_MALFORMED_SEAL"):
        verify_prediction_seal(declaration(), sealed)


@pytest.mark.parametrize(
    ("value", "code"),
    [
        ({"declaration_id": "only"}, "PREDICTION_SEAL_INVALID_INPUT"),
        (
            {
                **declaration(),
                "predictions": [declaration()["predictions"][0], declaration()["predictions"][0]],
            },
            "PREDICTION_SEAL_DUPLICATE_ID",
        ),
        (
            {
                **declaration(),
                "predictions": [{**declaration()["predictions"][0], "subject_ref": "../outside"}],
            },
            "PREDICTION_SEAL_UNSAFE_REFERENCE",
        ),
        (
            {
                **declaration(),
                "predictions": [{**declaration()["predictions"][0], "subject_ref": "/absolute"}],
            },
            "PREDICTION_SEAL_UNSAFE_REFERENCE",
        ),
        (
            {
                **declaration(),
                "predictions": [{**declaration()["predictions"][0], "prediction_value": float("nan")}],
            },
            "PREDICTION_SEAL_UNSUPPORTED_VALUE",
        ),
        (
            {
                **declaration(),
                "predictions": [{**declaration()["predictions"][0], "prediction_value": {"not-json"}}],
            },
            "PREDICTION_SEAL_UNSUPPORTED_VALUE",
        ),
    ],
)
def test_prediction_seal_rejects_invalid_declarations(value, code):
    with pytest.raises(InputValidationError, match=code):
        canonical_prediction_declaration(value)


def test_prediction_verify_rejects_bad_seals():
    sealed = seal_prediction_declaration(declaration())
    malformed = dict(sealed)
    malformed.pop("sealed_at")
    with pytest.raises(InputValidationError, match="PREDICTION_VERIFY_MALFORMED_SEAL"):
        verify_prediction_seal(declaration(), malformed)
    mismatch = dict(sealed)
    mismatch["seal_schema_version"] = 99
    with pytest.raises(InputValidationError, match="PREDICTION_VERIFY_SCHEMA_MISMATCH"):
        verify_prediction_seal(declaration(), mismatch)
