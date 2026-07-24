import pytest

from research_audit_kit.exceptions import InputValidationError
from research_audit_kit.optimization_audit.pareto import nondominated_indices, validate_pareto_claims


ROWS = [
    {"cost": "1", "latency": "4", "claimed": "true"},
    {"cost": "2", "latency": "2", "claimed": "true"},
    {"cost": "4", "latency": "1", "claimed": "true"},
    {"cost": "3", "latency": "3", "claimed": "true"},
]


def test_pareto_correctness():
    assert nondominated_indices(ROWS, [("cost", "min"), ("latency", "min")]) == [0, 1, 2]


def test_pareto_detects_false_claim():
    result = validate_pareto_claims(ROWS, [("cost", "min"), ("latency", "min")], claimed_column="claimed")
    assert result["false_claims"] == [3]


def test_pareto_is_deterministic():
    first = nondominated_indices(ROWS, [("cost", "min"), ("latency", "min")])
    second = nondominated_indices(ROWS, [("cost", "min"), ("latency", "min")])
    assert first == second


def test_invalid_direction_fails():
    with pytest.raises(InputValidationError):
        nondominated_indices(ROWS, [("cost", "sideways")])


def test_max_direction():
    rows = [{"score": 1}, {"score": 3}, {"score": 2}]
    assert nondominated_indices(rows, [("score", "max")]) == [1]

