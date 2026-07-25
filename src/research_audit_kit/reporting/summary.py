"""Status counts and conservative aggregate summaries."""

from __future__ import annotations

from collections import Counter
from typing import Iterable

from ..constants import (
    STATUS_FAIL,
    STATUS_INCONCLUSIVE,
    STATUS_PASS,
    STATUS_PASS_WITH_WARNINGS,
    STATUS_UNADJUDICATED,
)

def summarize_statuses(statuses: Iterable[str]) -> dict[str, object]:
    counts = Counter(statuses)
    if counts[STATUS_FAIL] or counts["MISMATCH"] or counts["MISSING"]:
        aggregate = STATUS_FAIL
    elif counts[STATUS_INCONCLUSIVE] or counts[STATUS_UNADJUDICATED]:
        aggregate = STATUS_INCONCLUSIVE
    elif counts["VOLATILE_WARNING"] or counts[STATUS_PASS_WITH_WARNINGS]:
        aggregate = STATUS_PASS_WITH_WARNINGS
    else:
        aggregate = STATUS_PASS
    return {"status": aggregate, "counts": dict(counts)}
