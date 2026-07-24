"""Claim-status evaluation and vocabulary enforcement."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from ..constants import CLAIM_STATUSES
from ..exceptions import InputValidationError

CLAIM_FIELDS = [
    "claim_id",
    "claim",
    "evidence",
    "contradictory_evidence",
    "status",
    "allowed_wording",
    "forbidden_wording",
]


def validate_claim(row: Mapping[str, Any]) -> dict[str, str]:
    missing = [field for field in CLAIM_FIELDS if field not in row]
    if missing:
        raise InputValidationError(f"missing claim fields: {missing}")
    status = str(row["status"])
    if status not in CLAIM_STATUSES:
        raise InputValidationError(f"invalid claim status {status}")
    return {field: str(row[field]) for field in CLAIM_FIELDS}


def evaluate_claims(
    claims: Iterable[Mapping[str, Any]], evidence: Iterable[Mapping[str, Any]]
) -> list[dict[str, str]]:
    evidence_by_id = {str(row.get("evidence_id", "")): row for row in evidence}
    output: list[dict[str, str]] = []
    for claim in claims:
        normalized = validate_claim(claim)
        references = [value for value in normalized["evidence"].split(";") if value]
        normalized["evidence_records_found"] = str(sum(ref in evidence_by_id for ref in references))
        normalized["evidence_records_requested"] = str(len(references))
        output.append(normalized)
    return output

