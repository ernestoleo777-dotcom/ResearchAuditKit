# SPDX-License-Identifier: Apache-2.0
"""Canonical sealing and verification of opaque prediction declarations."""

from __future__ import annotations

from datetime import datetime, timezone
import math
from pathlib import Path
from typing import Any, Mapping

from ..constants import STATUS_FAIL, STATUS_PASS
from ..exceptions import BaselineExistsError, InputValidationError
from ..io.json_io import write_json
from .hashing import stable_object_hash
from .portable import normalize_portable_reference

PREDICTION_SCHEMA_VERSION = 1
_DECLARATION_FIELDS = {"declaration_id", "declared_at", "predictions"}
_PREDICTION_FIELDS = {
    "prediction_id",
    "subject_ref",
    "prediction_value",
    "producer_role",
    "method_version",
}


def _input_error(code: str, message: str) -> None:
    raise InputValidationError(f"{code}: {message}")


def _required_string(value: Mapping[str, Any], field: str, code: str) -> str:
    raw = value.get(field)
    if not isinstance(raw, str) or not raw.strip():
        _input_error(code, f"{field} must be a non-empty string")
    return raw


def _validate_opaque_value(value: Any) -> None:
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float) and not math.isfinite(value):
        _input_error("PREDICTION_SEAL_UNSUPPORTED_VALUE", "prediction_value must be finite")
    elif isinstance(value, float):
        return
    elif isinstance(value, list):
        for item in value:
            _validate_opaque_value(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                _input_error("PREDICTION_SEAL_UNSUPPORTED_VALUE", "prediction_value keys must be strings")
            _validate_opaque_value(item)
    else:
        _input_error("PREDICTION_SEAL_UNSUPPORTED_VALUE", "prediction_value must be JSON-compatible")


def canonical_prediction_declaration(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and canonicalize a declaration without inspecting its meaning."""
    if not isinstance(value, Mapping):
        _input_error("PREDICTION_SEAL_INVALID_INPUT", "declaration must be an object")
    if set(value) != _DECLARATION_FIELDS:
        _input_error("PREDICTION_SEAL_INVALID_INPUT", "declaration has missing or undeclared fields")
    predictions = value["predictions"]
    if not isinstance(predictions, list) or not predictions:
        _input_error("PREDICTION_SEAL_INVALID_INPUT", "predictions must be a non-empty array")

    normalized: list[dict[str, Any]] = []
    identifiers: set[str] = set()
    for item in predictions:
        if not isinstance(item, Mapping) or set(item) != _PREDICTION_FIELDS:
            _input_error("PREDICTION_SEAL_INVALID_INPUT", "prediction has missing or undeclared fields")
        prediction_id = _required_string(item, "prediction_id", "PREDICTION_SEAL_INVALID_INPUT")
        if prediction_id in identifiers:
            _input_error("PREDICTION_SEAL_DUPLICATE_ID", f"duplicate prediction_id {prediction_id!r}")
        identifiers.add(prediction_id)
        try:
            subject_ref = normalize_portable_reference(
                item["subject_ref"],
                code="PREDICTION_SEAL_UNSAFE_REFERENCE",
                field="subject_ref",
            )
        except InputValidationError as exc:
            if str(exc).startswith("PREDICTION_SEAL_UNSAFE_REFERENCE"):
                raise
            _input_error("PREDICTION_SEAL_UNSAFE_REFERENCE", "subject_ref is invalid")
        _validate_opaque_value(item["prediction_value"])
        normalized.append(
            {
                "prediction_id": prediction_id,
                "subject_ref": subject_ref,
                "prediction_value": item["prediction_value"],
                "producer_role": _required_string(item, "producer_role", "PREDICTION_SEAL_INVALID_INPUT"),
                "method_version": _required_string(item, "method_version", "PREDICTION_SEAL_INVALID_INPUT"),
            }
        )
    return {
        "schema_version": PREDICTION_SCHEMA_VERSION,
        "declaration_id": _required_string(value, "declaration_id", "PREDICTION_SEAL_INVALID_INPUT"),
        "declared_at": _required_string(value, "declared_at", "PREDICTION_SEAL_INVALID_INPUT"),
        "predictions": sorted(normalized, key=lambda item: item["prediction_id"]),
    }


def seal_prediction_declaration(value: Mapping[str, Any]) -> dict[str, Any]:
    declaration = canonical_prediction_declaration(value)
    seal = {
        "seal_schema_version": PREDICTION_SCHEMA_VERSION,
        "declaration": declaration,
        "declaration_sha256": stable_object_hash(declaration),
        "sealed_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }
    return {**seal, "seal_sha256": stable_object_hash(seal)}


def write_prediction_seal(seal: Mapping[str, Any], path: str | Path, *, force: bool = False) -> Path:
    target = Path(path)
    if target.exists() and not force:
        raise BaselineExistsError("prediction seal already exists; pass --force to replace it")
    return write_json(target, dict(seal), overwrite=True)


def verify_prediction_seal(value: Mapping[str, Any], seal: Mapping[str, Any]) -> dict[str, Any]:
    observed = canonical_prediction_declaration(value)
    observed_digest = stable_object_hash(observed)
    if not isinstance(seal, Mapping) or set(seal) != {
        "seal_schema_version",
        "declaration",
        "declaration_sha256",
        "sealed_at",
        "seal_sha256",
    }:
        _input_error("PREDICTION_VERIFY_MALFORMED_SEAL", "seal has missing or undeclared fields")
    if seal["seal_schema_version"] != PREDICTION_SCHEMA_VERSION:
        _input_error("PREDICTION_VERIFY_SCHEMA_MISMATCH", "unsupported seal schema version")
    if not all(isinstance(seal[field], str) for field in ("declaration_sha256", "sealed_at", "seal_sha256")):
        _input_error("PREDICTION_VERIFY_MALFORMED_SEAL", "seal digests and timestamp must be strings")
    if not isinstance(seal["declaration"], Mapping):
        _input_error("PREDICTION_VERIFY_MALFORMED_SEAL", "seal declaration must be an object")
    sealed_source = dict(seal["declaration"])
    if sealed_source.pop("schema_version", None) != PREDICTION_SCHEMA_VERSION:
        _input_error("PREDICTION_VERIFY_SCHEMA_MISMATCH", "unsupported declaration schema version")
    try:
        sealed_declaration = canonical_prediction_declaration(sealed_source)
    except InputValidationError as exc:
        _input_error("PREDICTION_VERIFY_MALFORMED_SEAL", str(exc))
    sealed_digest = stable_object_hash(sealed_declaration)
    if sealed_digest != seal["declaration_sha256"]:
        _input_error("PREDICTION_VERIFY_MALFORMED_SEAL", "seal declaration does not match its digest")
    seal_payload = {key: value for key, value in seal.items() if key != "seal_sha256"}
    if stable_object_hash(seal_payload) != seal["seal_sha256"]:
        _input_error("PREDICTION_VERIFY_MALFORMED_SEAL", "seal metadata does not match its digest")

    failures = [] if observed_digest == seal["declaration_sha256"] else ["PREDICTION_VERIFY_DIGEST_MISMATCH"]
    return {
        "status": STATUS_PASS if not failures else STATUS_FAIL,
        "failure_codes": failures,
        "expected_digest": seal["declaration_sha256"],
        "observed_digest": observed_digest,
        "declaration_id": observed["declaration_id"],
        "limitation": "A matching seal establishes byte-level declaration consistency only, not prediction correctness or trusted timing.",
    }
