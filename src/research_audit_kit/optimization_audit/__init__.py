# SPDX-License-Identifier: Apache-2.0
"""Optimization-result auditing without truth claims."""

from .pareto import nondominated_indices, validate_pareto_claims
from .contamination import contamination_metrics
from .recommendation import audit_recommendations

__all__ = ["nondominated_indices", "validate_pareto_claims", "contamination_metrics", "audit_recommendations"]

