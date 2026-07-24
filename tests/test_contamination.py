from research_audit_kit.io.csv_io import read_csv_rows
from research_audit_kit.optimization_audit.contamination import contamination_metrics
from research_audit_kit.optimization_audit.recommendation import audit_recommendations


def test_contamination_ratios():
    rows = [
        {"support": "OBSERVED_EXACT", "selected": "true", "pareto": "true"},
        {"support": "CONDITIONALLY_REJECTED", "selected": "true", "pareto": "true"},
        {"support": "MARGINALLY_SUPPORTED_JOINTLY_UNOBSERVED", "selected": "true", "pareto": "false"},
    ]
    result = contamination_metrics(rows, support_column="support", selected_column="selected", pareto_column="pareto")
    assert result["SER"] == 1 / 3
    assert result["PCR"] == 1 / 2
    assert result["MSIR"] == 1 / 3


def test_metric_limit_is_attached():
    result = contamination_metrics([], support_column="support")
    assert "not physical feasibility" in result["limitation"]


def test_recommendation_status(conditional_rows, conditional_schema):
    candidate = {"architecture": "compact", "optimizer": "adam", "momentum": "0.8", "depth": "3"}
    result = audit_recommendations([candidate], conditional_rows, list(candidate), schema=conditional_schema)
    assert result[0]["support_status"] == "CONDITIONALLY_REJECTED"

