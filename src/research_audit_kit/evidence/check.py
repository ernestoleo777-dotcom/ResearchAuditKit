# SPDX-License-Identifier: Apache-2.0
"""Explicit mechanical gate policy; never resolve a scientific declaration."""
from __future__ import annotations

import re

from .fs import EvidenceError

CHECK_SCHEMA = "researchauditkit.evidence-check/v1"


def validate_policy(anchor, allowed, limits):
    if not isinstance(anchor, str) or not re.fullmatch(r"[0-9a-f]{64}", anchor):
        raise EvidenceError("GRAPH_ANCHOR_REQUIRED")
    if (not isinstance(allowed, (tuple, list))
            or not all(isinstance(item, str) and 0 < len(item) <= 641 for item in allowed)
            or len(allowed) != len(set(allowed))
            or len(allowed) > limits.nodes):
        raise EvidenceError("INVALID_CLAIM_ALLOWLIST")


def validate_scope(nodes, allowed):
    for identity in allowed:
        node = nodes.get(identity)
        if (node is None or node["type"] != "Claim"
                or node.get("resolution") != "UNRESOLVED"):
            raise EvidenceError("ALLOWLIST_CLAIM_NOT_UNRESOLVED")


def gate_result(evidence, anchor, allowed):
    # Import here to keep the core's opt-in gate dependency acyclic.
    from .core import finding, finish

    accepted, blocking = [], []
    # Invalid API inputs must still return a serializable failure receipt.
    safe_allowed = sorted(allowed) if (isinstance(allowed, (tuple, list))
                                      and all(isinstance(x, str) for x in allowed)) else []
    nodes = {node["id"]: node for node in evidence["nodes_visited"]}
    for item in evidence["findings"]:
        node = nodes.get(item["node_id"], {})
        if (item["code"] == "EXPLICIT_UNRESOLVED" and item["severity"] == "UNRESOLVED"
                and item["node_id"] in safe_allowed and node.get("type") == "Claim"
                and node.get("resolution") == "UNRESOLVED" and not item["path"]):
            accepted.append(item)
        else:
            blocking.append(item)
    observations = evidence["artifact_observations"]
    if not observations:
        blocking.append(finding("CHECK_ARTIFACT_SCOPE_EMPTY", "UNRESOLVED"))
    if any(row["status"] != "MECHANICALLY_VERIFIED" for row in observations):
        blocking.append(finding("CHECK_IDENTITIES_INCOMPLETE", "UNRESOLVED"))
    if evidence["impact_analysis"]["analysis_status"] != "COMPLETE":
        blocking.append(finding("CHECK_IMPACT_INCOMPLETE", "UNRESOLVED"))
    result = finish(dict(
        schema=CHECK_SCHEMA, command="check", expected_graph_content_sha256=(
            anchor if isinstance(anchor, str) else None),
        allowed_unresolved_claim_ids=safe_allowed,
        evidence_status=evidence["status"], evidence_result=evidence,
        accepted_findings=accepted, findings=blocking,
        scope_limits={"scientific_adjudication": "NOT_PERFORMED",
                      "baseline_authority": "CALLER_SUPPLIED_ANCHOR",
                      "atomic_snapshot": "NOT_PROVIDED"},
    ))
    # Include the gate decision in the receipt's content hash.
    result.pop("result_content_sha256")
    result["mechanical_gate"] = "PASS" if result["status"] == "PASS" else "FAIL"
    return finish(result)
