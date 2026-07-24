from research_audit_kit.support.missingness import classify_missingness


def test_small_sample_is_insufficient():
    result = classify_missingness([{"a": "x"}], ["a"], discrete=["a"])
    assert result["classification"] == "INSUFFICIENT_EVIDENCE"


def test_sparse_grid_is_pattern_candidate():
    rows = [{"a": "x", "b": "1"}, {"a": "x", "b": "2"}, {"a": "y", "b": "3"}, {"a": "z", "b": "1"}]
    result = classify_missingness(rows, ["a", "b"], discrete=["a", "b"])
    assert result["classification"] == "STRUCTURAL_PATTERN_CANDIDATE"


def test_physics_not_inferred(conditional_rows, conditional_schema):
    result = classify_missingness(conditional_rows, ["optimizer", "momentum"], discrete=["optimizer", "momentum"], schema=conditional_schema)
    assert result["physical_interpretation"] == "NOT_INFERRED"

