"""Volatile metadata helpers."""

from __future__ import annotations

from .policy import IntegrityPolicy


def is_volatile(relative_path: str, policy: IntegrityPolicy) -> bool:
    return policy.classify(relative_path)[0] == "volatile_metadata"


def volatile_gate_effect(changed: bool) -> str:
    return "VOLATILE_WARNING" if changed else "MATCH"

