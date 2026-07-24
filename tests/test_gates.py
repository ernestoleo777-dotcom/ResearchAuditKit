import pytest

from research_audit_kit.exceptions import InputValidationError
from research_audit_kit.governance.gates import evaluate_gate


POLICY = {"gate": {"id": "effect", "criteria": [{"metric": "change", "pass": {"gte": 0.5}, "inconclusive": {"gte": 0.2, "lt": 0.5}, "fail": {"lt": 0.2}}]}}


def test_gate_pass():
    assert evaluate_gate({"change": 0.8}, POLICY)["status"] == "PASS"


def test_gate_inconclusive():
    assert evaluate_gate({"change": 0.3}, POLICY)["status"] == "INCONCLUSIVE"


def test_gate_fail():
    assert evaluate_gate({"change": 0.1}, POLICY)["status"] == "FAIL"


def test_gate_blocked():
    assert evaluate_gate({}, {"gate": {"id": "g", "blocked": True}})["status"] == "BLOCKED"


def test_gate_skipped():
    assert evaluate_gate({}, {"gate": {"id": "g", "enabled": False}})["status"] == "SKIPPED_BY_GATE"


def test_missing_metric_unadjudicated():
    assert evaluate_gate({}, POLICY)["status"] == "UNADJUDICATED"


def test_invalid_operator_fails():
    policy = {"gate": {"criteria": [{"metric": "x", "pass": {"near": 1}}]}}
    with pytest.raises(InputValidationError):
        evaluate_gate({"x": 1}, policy)

