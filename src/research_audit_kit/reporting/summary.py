"""Status counts and conservative aggregate summaries."""

from __future__ import annotations

from collections import Counter
from typing import Iterable


def summarize_statuses(statuses: Iterable[str]) -> dict[str, object]:
    counts = Counter(statuses)
    if counts["FAIL"] or counts["MISMATCH"] or counts["MISSING"]:
        aggregate = "FAIL"
    elif counts["INCONCLUSIVE"] or counts["UNADJUDICATED"]:
        aggregate = "INCONCLUSIVE"
    elif counts["VOLATILE_WARNING"] or counts["PASS_WITH_WARNINGS"]:
        aggregate = "PASS_WITH_WARNINGS"
    else:
        aggregate = "PASS"
    return {"status": aggregate, "counts": dict(counts)}

