# SPDX-License-Identifier: Apache-2.0
"""Empirical data-support auditing."""

from .marginal import marginal_support
from .joint import exact_membership, joint_support, cartesian_gap
from .conditional import evaluate_conditional_rules
from .taxonomy import classify_candidate

__all__ = [
    "marginal_support",
    "exact_membership",
    "joint_support",
    "cartesian_gap",
    "evaluate_conditional_rules",
    "classify_candidate",
]

