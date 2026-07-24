from research_audit_kit.support.taxonomy import classify_candidate


def test_observed_exact(conditional_rows):
    assert classify_candidate(conditional_rows[0], conditional_rows, list(conditional_rows[0]))["status"] == "OBSERVED_EXACT"


def test_conditionally_rejected(conditional_rows, conditional_schema):
    candidate = {"architecture": "compact", "optimizer": "adam", "momentum": "0.8", "depth": "3"}
    assert classify_candidate(candidate, conditional_rows, list(candidate), schema=conditional_schema)["status"] == "CONDITIONALLY_REJECTED"


def test_outside_marginal_range(conditional_rows):
    candidate = {"architecture": "deep", "optimizer": "adam", "momentum": "0.0", "depth": "3"}
    assert classify_candidate(candidate, conditional_rows, list(candidate))["status"] == "OUTSIDE_MARGINAL_RANGE"


def test_marginally_supported_jointly_unobserved(conditional_rows):
    candidate = {"architecture": "compact", "optimizer": "sgd", "momentum": "0.9", "depth": "3"}
    assert classify_candidate(candidate, conditional_rows, list(candidate))["status"] == "MARGINALLY_SUPPORTED_JOINTLY_UNOBSERVED"

