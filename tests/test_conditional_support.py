from research_audit_kit.support.conditional import evaluate_conditional_rules


def test_conditional_supported(conditional_schema):
    result = evaluate_conditional_rules({"optimizer": "sgd", "momentum": "0.8"}, conditional_schema)
    assert result["status"] == "CONDITIONALLY_SUPPORTED"


def test_conditional_rejected(conditional_schema):
    result = evaluate_conditional_rules({"optimizer": "adam", "momentum": "0.8"}, conditional_schema)
    assert result["status"] == "CONDITIONALLY_REJECTED"


def test_conditional_unknown(conditional_schema):
    result = evaluate_conditional_rules({"optimizer": "rms", "momentum": "0.2"}, conditional_schema)
    assert result["status"] == "UNKNOWN"

