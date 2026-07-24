import pytest

from research_audit_kit.exceptions import InputValidationError
from research_audit_kit.governance.claims import evaluate_claims, validate_claim


CLAIM = {"claim_id": "c1", "claim": "declared effect", "evidence": "e1", "contradictory_evidence": "", "status": "INCONCLUSIVE", "allowed_wording": "effect remains uncertain", "forbidden_wording": "effect is proven"}


def test_claim_status_valid():
    assert validate_claim(CLAIM)["status"] == "INCONCLUSIVE"


def test_invalid_claim_status_fails():
    with pytest.raises(InputValidationError):
        validate_claim({**CLAIM, "status": "PROMISING"})


def test_evidence_reference_count():
    result = evaluate_claims([CLAIM], [{"evidence_id": "e1"}])
    assert result[0]["evidence_records_found"] == "1"

