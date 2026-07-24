"""Deterministic declarative gate evaluation."""

from __future__ import annotations

from typing import Any, Mapping

from ..constants import GATE_STATUSES
from ..exceptions import InputValidationError


def _condition(value: float, rules: Mapping[str, Any]) -> bool:
    checks = {
        "gte": lambda bound: value >= float(bound),
        "gt": lambda bound: value > float(bound),
        "lte": lambda bound: value <= float(bound),
        "lt": lambda bound: value < float(bound),
        "eq": lambda bound: value == float(bound),
    }
    for operator, bound in rules.items():
        if operator not in checks:
            raise InputValidationError(f"unsupported gate operator {operator}")
        if not checks[operator](bound):
            return False
    return True


def _criterion_status(value: float, criterion: Mapping[str, Any]) -> str:
    for status, key in (("PASS", "pass"), ("INCONCLUSIVE", "inconclusive"), ("FAIL", "fail")):
        if key in criterion and _condition(value, criterion[key]):
            return status
    return "UNADJUDICATED"


def evaluate_gate(metrics: Mapping[str, Any], policy: Mapping[str, Any]) -> dict[str, Any]:
    gate = policy.get("gate", policy)
    gate_id = str(gate.get("id", "unnamed_gate"))
    if gate.get("blocked"):
        return {"gate_id": gate_id, "status": "BLOCKED", "criteria": []}
    if gate.get("enabled") is False:
        return {"gate_id": gate_id, "status": "SKIPPED_BY_GATE", "criteria": []}
    results: list[dict[str, Any]] = []
    for criterion in gate.get("criteria", []):
        metric = str(criterion.get("metric", ""))
        if metric not in metrics:
            results.append({"metric": metric, "status": "UNADJUDICATED", "value": None})
            continue
        try:
            value = float(metrics[metric])
        except (TypeError, ValueError) as exc:
            raise InputValidationError(f"metric {metric!r} must be numeric") from exc
        results.append({"metric": metric, "value": value, "status": _criterion_status(value, criterion)})
    statuses = {row["status"] for row in results}
    if not results or "UNADJUDICATED" in statuses:
        status = "UNADJUDICATED"
    elif "FAIL" in statuses:
        status = "FAIL"
    elif "INCONCLUSIVE" in statuses:
        status = "INCONCLUSIVE"
    else:
        status = "PASS"
    if status not in GATE_STATUSES:
        raise AssertionError(status)
    return {"gate_id": gate_id, "status": status, "criteria": results}

