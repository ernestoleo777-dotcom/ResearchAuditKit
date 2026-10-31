# SPDX-License-Identifier: Apache-2.0
"""Bounded consequences of observed artifact identity issues in declared graphs."""
from __future__ import annotations

from collections import defaultdict, deque

IMPACT_SCHEMA = "researchauditkit.evidence-impact/v1"


def empty_analysis(limits):
    return {
        "schema": IMPACT_SCHEMA,
        "analysis_status": "NOT_ANALYZED",
        "semantics": "DECLARED_RELATIONSHIPS_ONLY",
        "path_selection": "ONE_SHORTEST_PATH_PER_ARTIFACT_CLAIM_AND_CONTEXT",
        "artifacts": [],
        "potentially_affected_claim_ids": [],
        "not_reached_claim_ids": [],
        "incomplete_reasons": [],
        "limits": {"propagation_steps": limits.edges, "witness_steps": limits.edges,
                   "claim_paths": limits.nodes, "depth": limits.depth},
        "usage": {"propagation_steps": 0, "witness_steps": 0, "claim_paths": 0},
    }


def analyze(nodes, edges, refs, observations, limits):
    """Do not infer causality, supersession propagation, or scientific validity."""
    result = empty_analysis(limits)
    usage = result["usage"]
    reasons = set()
    superseded = {edge["target"] for edge in edges if edge["type"] == "SUPERSEDES"}
    adjacency = defaultdict(set)
    for edge in edges:
        kind = edge["type"]
        if kind == "SUPERSEDES":
            continue
        if kind in ("SUPPORTS", "CONTRADICTS"):
            source, target = edge["source"], edge["target"]
        else:
            source, target = edge["target"], edge["source"]
        adjacency[source].add((target, kind, edge.get("citation_context") == "historical"))
    for ref in refs:
        adjacency[ref["target"]].add((ref["source"], ref["field"], False))
    adjacency = {key: sorted(values) for key, values in adjacency.items()}
    affected_claims = set()
    for observation in sorted(observations, key=lambda row: row["node_id"]):
        if observation["status"] == "MECHANICALLY_VERIFIED":
            continue
        seed = observation["node_id"]
        first = (seed, seed in superseded)
        parents = {first: None}
        queue = deque([(first, 0)])
        reached = set()
        claim_ids = set()
        paths = []
        while queue:
            state, depth = queue.popleft()
            current, historical = state
            reached.add(current)
            if nodes[current]["type"] == "Claim":
                claim_ids.add(current)
                affected_claims.add(current)
                node_ids, relations = [current], []
                cursor = state
                while parents[cursor] is not None:
                    previous, relation = parents[cursor]
                    node_ids.append(previous[0])
                    relations.append(relation)
                    cursor = previous
                node_ids.reverse()
                relations.reverse()
                if usage["claim_paths"] >= limits.nodes:
                    reasons.add("IMPACT_CLAIM_PATH_BUDGET_EXCEEDED")
                elif usage["witness_steps"] + len(relations) > limits.edges:
                    reasons.add("IMPACT_WITNESS_BUDGET_EXCEEDED")
                else:
                    usage["claim_paths"] += 1
                    usage["witness_steps"] += len(relations)
                    paths.append({
                        "claim_id": current,
                        "claim_version_state": "SUPERSEDED" if current in superseded else "NOT_SUPERSEDED",
                        "citation_context": "historical" if historical else "current",
                        "node_ids": node_ids,
                        "relations": relations,
                    })
            for target, relation, declared_historical in adjacency.get(current, []):
                if usage["propagation_steps"] >= limits.edges:
                    reasons.add("IMPACT_PROPAGATION_BUDGET_EXCEEDED")
                    break
                usage["propagation_steps"] += 1
                following = (target, historical or declared_historical or target in superseded)
                if following in parents:
                    continue
                if depth >= limits.depth:
                    reasons.add("IMPACT_DEPTH_EXCEEDED")
                    continue
                parents[following] = (state, relation)
                queue.append((following, depth + 1))
        result["artifacts"].append({
            "artifact_id": seed,
            "path": observation["path"],
            "observation_status": observation["status"],
            "identity_change": "CONFIRMED" if observation["status"] == "IDENTITY_MISMATCH" else "UNRESOLVED",
            "reached_node_ids": sorted(reached),
            "potentially_affected_claim_ids": sorted(claim_ids),
            "claim_paths": sorted(paths, key=lambda row: (row["claim_id"], row["citation_context"])),
        })
    result["potentially_affected_claim_ids"] = sorted(affected_claims)
    result["not_reached_claim_ids"] = sorted(
        nid for nid, node in nodes.items() if node["type"] == "Claim" and nid not in affected_claims
    )
    result["incomplete_reasons"] = sorted(reasons)
    result["analysis_status"] = "INCOMPLETE" if reasons else "COMPLETE"
    return result
