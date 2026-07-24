import pytest

from research_audit_kit.exceptions import PolicyError
from research_audit_kit.integrity.policy import IntegrityPolicy


def test_classifies_scientific_asset(policy):
    assert policy.classify("src/tool.py")[0] == "scientific_asset"


def test_volatile_precedes_include(policy):
    assert policy.classify("nested/.DS_Store")[0] == "volatile_metadata"


def test_missing_policy_id_fails():
    with pytest.raises(PolicyError):
        IntegrityPolicy.from_dict({"policy": {}})


def test_policy_roundtrip(policy):
    assert IntegrityPolicy.from_dict(policy.to_dict()) == policy

