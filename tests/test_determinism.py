from research_audit_kit.validation.determinism import compare_repeated_outputs, stable_order


def test_equal_outputs_are_deterministic():
    assert compare_repeated_outputs({"seed": 7}, {"seed": 7})["deterministic"] is True


def test_different_outputs_are_not_deterministic():
    assert compare_repeated_outputs([1, 2], [2, 1])["deterministic"] is False


def test_stable_ordering():
    rows = [{"id": "b"}, {"id": "a"}]
    assert [row["id"] for row in stable_order(rows, ["id"])] == ["a", "b"]

