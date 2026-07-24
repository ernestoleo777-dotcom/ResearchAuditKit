"""Preregistered gates, claims, deviations, and negative results."""

from .gates import evaluate_gate
from .claims import evaluate_claims
from .deviations import record_deviation

__all__ = ["evaluate_gate", "evaluate_claims", "record_deviation"]

