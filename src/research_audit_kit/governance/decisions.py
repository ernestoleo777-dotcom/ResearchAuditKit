# SPDX-License-Identifier: Apache-2.0
"""Machine-readable final decision model."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from ..constants import GATE_STATUSES


@dataclass
class ResearchDecision:
    project_class: str
    next_stage: str
    gates: dict[str, str]
    allowed_work: list[str] = field(default_factory=list)
    forbidden_work: list[str] = field(default_factory=list)
    confidence: str = "unknown"

    def __post_init__(self) -> None:
        invalid = {value for value in self.gates.values() if value not in GATE_STATUSES}
        if invalid:
            raise ValueError(f"invalid gate statuses: {sorted(invalid)}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

