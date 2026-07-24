import pytest

from research_audit_kit.exceptions import InputValidationError
from research_audit_kit.support.joint import cartesian_gap, exact_membership, joint_support, pairwise_support


def test_joint_support_exact(conditional_rows):
    assert len(joint_support(conditional_rows, ["architecture", "optimizer"])) == 4


def test_exact_membership(conditional_rows):
    assert exact_membership(conditional_rows[0], conditional_rows, ["architecture", "optimizer", "momentum", "depth"])


def test_pairwise_support(conditional_rows):
    pairs = pairwise_support(conditional_rows, ["architecture", "optimizer", "depth"])
    assert "architecture|optimizer" in pairs


def test_cartesian_gap_requires_discrete(conditional_rows):
    with pytest.raises(InputValidationError):
        cartesian_gap(conditional_rows, ["architecture", "depth"])


def test_cartesian_gap_counts(conditional_rows):
    result = cartesian_gap(conditional_rows, ["architecture", "optimizer", "momentum"], discrete=["architecture", "optimizer", "momentum"])
    assert result["marginal_cartesian_size"] == 12
    assert result["absent_combination_count"] == 8

