"""Shared status vocabularies."""

__version__ = "0.1.0"

ASSET_CATEGORIES = {
    "scientific_asset",
    "volatile_metadata",
    "generated_artifact",
    "cache",
    "temporary_file",
    "unclassified_file",
}

VERIFICATION_STATUSES = {
    "MATCH",
    "MISMATCH",
    "MISSING",
    "NEW_UNCLASSIFIED",
    "VOLATILE_WARNING",
    "EXCLUDED_MATCH",
    "EXCLUDED_CHANGED",
}

GATE_STATUSES = {
    "PASS",
    "PASS_WITH_WARNINGS",
    "INCONCLUSIVE",
    "FAIL",
    "BLOCKED",
    "SKIPPED_BY_GATE",
    "UNADJUDICATED",
}

CLAIM_STATUSES = {
    "VALIDATED",
    "PARTIALLY_SUPPORTED",
    "INCONCLUSIVE",
    "FALSIFIED",
    "RETIRED",
    "UNADJUDICATED",
    "OUT_OF_SCOPE",
}

SUPPORT_STATUSES = {
    "OBSERVED_EXACT",
    "MARGINALLY_SUPPORTED_JOINTLY_UNOBSERVED",
    "CONDITIONALLY_SUPPORTED",
    "CONDITIONALLY_REJECTED",
    "OUTSIDE_MARGINAL_RANGE",
    "BELOW_OBSERVED_BRANCH_SUPPORT",
    "UNCLASSIFIED",
}

SUPPORT_LIMITATION = (
    "These metrics audit support status, not physical feasibility or true performance."
)

