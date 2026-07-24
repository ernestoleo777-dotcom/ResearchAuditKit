import csv

import pytest

from research_audit_kit.exceptions import InputValidationError
from research_audit_kit.governance.deviations import record_deviation


def deviation(identifier="d-1"):
    return {"deviation_id": identifier, "triggering_action": "unauthorized-stage", "protocol_rule": "gate-required", "affected_files": ["synthetic-output.csv"], "affected_metrics": ["score"], "isolation_status": "ISOLATED", "adjudication_status": "UNADJUDICATED", "allowed_usage": "audit only", "forbidden_usage": "formal claims"}


def test_protocol_deviation_recorded(tmp_path):
    target = tmp_path / "ledger.csv"
    record_deviation(target, deviation())
    assert list(csv.DictReader(target.open()))[0]["adjudication_status"] == "UNADJUDICATED"


def test_deviation_ledger_appends(tmp_path):
    target = tmp_path / "ledger.csv"
    record_deviation(target, deviation("d-1"))
    record_deviation(target, deviation("d-2"))
    assert len(list(csv.DictReader(target.open()))) == 2


def test_deviation_ids_are_immutable(tmp_path):
    target = tmp_path / "ledger.csv"
    record_deviation(target, deviation())
    with pytest.raises(InputValidationError):
        record_deviation(target, deviation())

