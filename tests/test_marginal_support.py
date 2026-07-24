from research_audit_kit.support.marginal import marginal_support


def test_marginal_counts(conditional_rows):
    report = marginal_support(conditional_rows, ["optimizer"])
    assert report["optimizer"]["frequency"] == {"adam": 2, "sgd": 2}


def test_marginal_missing_values():
    report = marginal_support([{"depth": "3"}, {"depth": ""}, {}], ["depth"])
    assert report["depth"]["missing_values"] == 2

