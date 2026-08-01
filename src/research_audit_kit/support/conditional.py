# SPDX-License-Identifier: Apache-2.0
"""User-declared empirical branch-rule evaluation."""

from __future__ import annotations

from typing import Any, Mapping


def _as_number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _equals(left: Any, right: Any) -> bool:
    left_num, right_num = _as_number(left), _as_number(right)
    if left_num is not None and right_num is not None:
        return left_num == right_num
    return str(left) == str(right)


def _satisfies(value: Any, requirement: Any) -> bool:
    if isinstance(requirement, list):
        return any(_equals(value, allowed) for allowed in requirement)
    if isinstance(requirement, dict):
        numeric = _as_number(value)
        if numeric is None:
            return False
        if "min" in requirement and numeric < float(requirement["min"]):
            return False
        if "max" in requirement and numeric > float(requirement["max"]):
            return False
        if "in" in requirement and not any(_equals(value, item) for item in requirement["in"]):
            return False
        return True
    return _equals(value, requirement)


def _branch_applies(candidate: Mapping[str, Any], when: Mapping[str, Any]) -> bool:
    return all(_satisfies(candidate.get(feature), requirement) for feature, requirement in when.items())


def evaluate_conditional_rules(
    candidate: Mapping[str, Any], schema: Mapping[str, Any]
) -> dict[str, Any]:
    branches = schema.get("branches", schema)
    applicable: list[str] = []
    failures: list[str] = []
    for name, rule in branches.items():
        if _branch_applies(candidate, rule.get("when", {})):
            applicable.append(str(name))
            for feature, requirement in rule.get("require", {}).items():
                if not _satisfies(candidate.get(feature), requirement):
                    failures.append(f"{name}:{feature}")
    if not applicable:
        status = "UNKNOWN"
    elif failures:
        status = "CONDITIONALLY_REJECTED"
    else:
        status = "CONDITIONALLY_SUPPORTED"
    return {"status": status, "applicable_branches": applicable, "failed_requirements": failures}

