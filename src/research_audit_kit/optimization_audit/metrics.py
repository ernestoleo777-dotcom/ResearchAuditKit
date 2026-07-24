"""Published support-audit metric definitions."""

from ..constants import SUPPORT_LIMITATION

METRIC_DEFINITIONS = {
    "SER": "selected conditionally unsupported candidates / selected candidates",
    "PCR": "conditionally unsupported predicted Pareto points / predicted Pareto size",
    "MSIR": "marginally supported but jointly unobserved selected candidates / selected candidates",
}


def metric_documentation() -> dict[str, object]:
    return {"definitions": METRIC_DEFINITIONS, "limitation": SUPPORT_LIMITATION}

