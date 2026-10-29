# SPDX-License-Identifier: Apache-2.0
"""Explicit evidence relationships and narrow mechanical observations, not adjudication."""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import asdict, dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
from typing import Any

from .fs import EvidenceError, Root, no_download, relative_path

SCHEMA = "researchauditkit.evidence/v1"
TYPES = ("Claim", "Evidence", "ExperimentRun", "Artifact", "Protocol", "Decision")
LEVELS = ("DECLARED", "MECHANICALLY_VERIFIED", "SCIENTIFICALLY_ADJUDICATED")
ENDPOINTS = {
    "SUPPORTS": {("Evidence", "Claim")},
    "CONTRADICTS": {("Evidence", "Claim"), ("Claim", "Claim")},
    "DERIVED_FROM": {("Evidence", t) for t in ("Artifact", "ExperimentRun", "Evidence")}
    | {("Artifact", t) for t in ("Artifact", "ExperimentRun")},
    "SUPERSEDES": {(t, t) for t in TYPES},
    "DEPENDS_ON": {("Claim", t) for t in ("Claim", "Protocol")}
    | {("Evidence", t) for t in ("Evidence", "Artifact", "ExperimentRun", "Protocol")}
    | {("ExperimentRun", t) for t in ("Protocol", "Artifact")}
    | {("Decision", t) for t in ("Claim", "Evidence", "Protocol")}
    | {("Artifact", "Artifact")},
}
BASE_FIELDS = {"id", "logical_id", "version", "type", "assertion_level", "external_adjudication"}
FIELDS = {
    "Claim": {"statement", "resolution"},
    "Evidence": {"description", "source_refs"},
    "Artifact": {"path", "media_type", "sha256", "unresolved_reason"},
    "ExperimentRun": {"protocol_ref", "execution_status", "record_refs"},
    "Protocol": {"description", "artifact_refs", "unresolved_reason"},
    "Decision": {"outcome", "rationale", "external_adjudication_ref", "unresolved_reason"},
}
RESOLUTIONS = {"ABSTAIN", "UNRESOLVED", "EXTERNAL_ADJUDICATION_RECORDED"}
EXECUTION = {"NOT_EXECUTED", "COMPLETED", "PASS", "FAIL", "PARTIAL", "BLOCKED", "UNRESOLVED"}


@dataclass(frozen=True)
class Limits:
    graph_bytes: int = 2 * 1024 * 1024
    nodes: int = 2048
    edges: int = 8192
    depth: int = 64
    json_depth: int = 64
    artifact_bytes: int = 64 * 1024 * 1024
    total_artifact_bytes: int = 256 * 1024 * 1024


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode()


def strict_json(payload: bytes, limits: Limits) -> dict:
    if len(payload) > limits.graph_bytes:
        raise EvidenceError("GRAPH_BUDGET_EXCEEDED")
    depth = 0
    quoted = escaped = False
    for byte in payload:
        if quoted:
            if escaped:
                escaped = False
            elif byte == 92:
                escaped = True
            elif byte == 34:
                quoted = False
        elif byte == 34:
            quoted = True
        elif byte in (91, 123):
            depth += 1
            if depth > limits.json_depth:
                raise EvidenceError("JSON_DEPTH_EXCEEDED")
        elif byte in (93, 125):
            depth -= 1
    def pairs(items):
        obj = {}
        for key, value in items:
            if key in obj:
                raise EvidenceError("DUPLICATE_JSON_KEY")
            obj[key] = value
        return obj
    def number(text):
        n = float(text)
        if not math.isfinite(n):
            raise EvidenceError("NONFINITE_JSON_NUMBER")
        return n
    def integer(text):
        if len(text) > 128:
            raise EvidenceError("JSON_INTEGER_BUDGET_EXCEEDED")
        return int(text)
    try:
        obj = json.loads(payload.decode("utf-8"), object_pairs_hook=pairs,
                         parse_constant=number, parse_float=number, parse_int=integer)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise EvidenceError("MALFORMED_JSON") from exc
    if not isinstance(obj, dict):
        raise EvidenceError("GRAPH_MUST_BE_OBJECT")
    pending = [obj]
    while pending:
        value = pending.pop()
        if isinstance(value, dict):
            pending.extend(value.keys())
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)
        elif isinstance(value, str):
            try:
                value.encode("utf-8")
            except UnicodeError as exc:
                raise EvidenceError("MALFORMED_UNICODE") from exc
    return obj


def finding(code: str, severity: str = "UNRESOLVED", node_id: str = "", path: str = "") -> dict:
    return {"code": code, "severity": severity, "node_id": node_id, "path": path}


def text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and len(value) <= 65536


def references(node: dict) -> list[tuple[str, str, set[str]]]:
    result = []
    for key, types in (("source_refs", {"Artifact", "Evidence", "ExperimentRun", "Protocol"}),
                       ("record_refs", {"Artifact"}), ("artifact_refs", {"Artifact"})):
        for target in node.get(key, []):
            result.append((key, target, types))
    for key, types in (("protocol_ref", {"Protocol"}), ("external_adjudication_ref", {"Artifact"})):
        if key in node:
            result.append((key, node[key], types))
    ext = node.get("external_adjudication")
    if isinstance(ext, dict) and text(ext.get("record_ref")):
        result.append(("external_adjudication.record_ref", ext["record_ref"], {"Artifact"}))
    return result


def dag(nodes: dict, arcs: list[tuple[str, str]], limit: int, code: str):
    adjacency = defaultdict(set)
    indegree = dict.fromkeys(nodes, 0)
    depths = dict.fromkeys(nodes, 0)
    for source, target in arcs:
        if target not in adjacency[source]:
            adjacency[source].add(target)
            indegree[target] += 1
    queue = deque(sorted(n for n in nodes if not indegree[n]))
    visited = 0
    while queue:
        node = queue.popleft()
        visited += 1
        for target in sorted(adjacency[node]):
            depths[target] = max(depths[target], depths[node] + 1)
            if depths[target] > limit:
                raise EvidenceError("DEPENDENCY_DEPTH_EXCEEDED")
            indegree[target] -= 1
            if not indegree[target]:
                queue.append(target)
    if visited != len(nodes):
        raise EvidenceError(code)


def validate_graph(graph: dict, limits: Limits) -> tuple[dict, list, list, list]:
    if set(graph) != {"schema", "nodes", "edges"} or graph.get("schema") != SCHEMA:
        raise EvidenceError("GRAPH_SCHEMA_INVALID")
    if not isinstance(graph["nodes"], list) or not isinstance(graph["edges"], list):
        raise EvidenceError("GRAPH_COLLECTION_TYPE")
    if not graph["nodes"] or len(graph["nodes"]) > limits.nodes or len(graph["edges"]) > limits.edges:
        raise EvidenceError("GRAPH_SIZE_BUDGET_EXCEEDED")
    nodes, findings = {}, []
    for node in graph["nodes"]:
        if not isinstance(node, dict) or node.get("type") not in TYPES:
            raise EvidenceError("UNKNOWN_NODE_TYPE")
        kind = node["type"]
        if not {"id", "logical_id", "version", "type", "assertion_level"}.issubset(node):
            raise EvidenceError("MISSING_NODE_FIELDS")
        if set(node) - (BASE_FIELDS | FIELDS[kind]):
            raise EvidenceError("UNKNOWN_NODE_FIELD")
        logical, version = node["logical_id"], node["version"]
        if (not isinstance(logical, str) or len(logical) > 512
                or not re.fullmatch(r"urn:rak:[A-Za-z0-9_.-]+:" + kind.lower()
                                    + r":[A-Za-z0-9_.:-]+", logical)
                or not isinstance(version, str)
                or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", version)
                or version.lower() in {"latest", "current", "head", "main", "master"}
                or node["id"] != logical + "@" + version):
            raise EvidenceError("VERSION_IDENTITY_INVALID")
        nid = node["id"]
        if nid in nodes:
            raise EvidenceError("DUPLICATE_NODE_ID")
        if node["assertion_level"] not in LEVELS:
            raise EvidenceError("ASSERTION_LEVEL_INVALID")
        for key in ("statement", "description", "media_type", "rationale", "unresolved_reason"):
            if key in node and not text(node[key]):
                raise EvidenceError("INVALID_TEXT_FIELD")
        for key in ("source_refs", "record_refs", "artifact_refs"):
            if key in node and (not isinstance(node[key], list)
                                or not all(text(x) for x in node[key])
                                or len(node[key]) != len(set(node[key]))):
                raise EvidenceError("INVALID_REFERENCE_LIST")
        for key in ("protocol_ref", "external_adjudication_ref"):
            if key in node and not text(node[key]):
                raise EvidenceError("INVALID_REFERENCE")
        required = {"Claim": {"statement", "resolution"},
                    "Evidence": {"description", "source_refs"},
                    "Artifact": {"path", "media_type"},
                    "ExperimentRun": {"protocol_ref", "execution_status", "record_refs"},
                    "Protocol": {"description"}, "Decision": {"outcome", "rationale"}}[kind]
        if not required.issubset(node):
            raise EvidenceError("MISSING_TYPED_FIELDS")
        if kind == "Claim" and (not isinstance(node["resolution"], str) or node["resolution"] not in RESOLUTIONS):
            raise EvidenceError("CLAIM_RESOLUTION_INVALID")
        if kind == "Decision" and (not isinstance(node["outcome"], str) or node["outcome"] not in {"GO", "NO_GO", "ABSTAIN", "UNRESOLVED"}):
            raise EvidenceError("DECISION_OUTCOME_INVALID")
        if kind == "ExperimentRun" and (not isinstance(node["execution_status"], str) or node["execution_status"] not in EXECUTION):
            raise EvidenceError("EXECUTION_STATUS_INVALID")
        if kind == "Artifact":
            relative_path(node["path"])
            if "sha256" in node and (not isinstance(node["sha256"], str)
                                      or not re.fullmatch(r"[0-9a-f]{64}", node["sha256"])):
                raise EvidenceError("SHA256_INVALID")
            if "sha256" not in node and not node.get("unresolved_reason"):
                raise EvidenceError("ARTIFACT_IDENTITY_REQUIRED")
        if kind == "Protocol" and not node.get("artifact_refs") and not node.get("unresolved_reason"):
            raise EvidenceError("PROTOCOL_PROVENANCE_REQUIRED")
        if kind == "Decision" and not node.get("external_adjudication_ref") and not node.get("unresolved_reason"):
            raise EvidenceError("DECISION_PROVENANCE_REQUIRED")
        if node["assertion_level"] != "DECLARED":
            findings.append(finding("INPUT_VERIFICATION_LABEL_IS_DECLARATION", "INFO", nid))
        ext = node.get("external_adjudication")
        if "external_adjudication" in node and (not isinstance(ext, dict)
                or set(ext) - {"identity", "method", "scope", "record_ref"}
                or any(not text(value) for value in ext.values())):
            raise EvidenceError("EXTERNAL_ADJUDICATION_FORMAT_INVALID")
        if (node["assertion_level"] == "SCIENTIFICALLY_ADJUDICATED"
                or node.get("resolution") == "EXTERNAL_ADJUDICATION_RECORDED"):
            complete = isinstance(ext, dict) and all(text(ext.get(k)) for k in ("identity", "method", "scope", "record_ref"))
            findings.append(finding("EXTERNAL_ADJUDICATION_RECORDED_NOT_VALIDATED" if complete
                                    else "EXTERNAL_ADJUDICATION_INCOMPLETE",
                                    "INFO" if complete else "UNRESOLVED", nid))
        nodes[nid] = dict(node)
        for field in ("source_refs", "record_refs", "artifact_refs"):
            if field in node:
                nodes[nid][field] = sorted(node[field])
    refs = []
    for nid, node in nodes.items():
        for field, target, types in references(node):
            if target not in nodes:
                raise EvidenceError("DANGLING_REFERENCE")
            if nodes[target]["type"] not in types:
                raise EvidenceError("REFERENCE_TYPE_INVALID")
            refs.append({"source": nid, "target": target, "field": field})
    edge_ids, edges = set(), []
    for edge in graph["edges"]:
        if (not isinstance(edge, dict) or not {"id", "type", "source", "target"}.issubset(edge)
                or set(edge) - {"id", "type", "source", "target", "citation_context"}):
            raise EvidenceError("EDGE_FIELDS_INVALID")
        if not text(edge["id"]) or edge["id"] in edge_ids:
            raise EvidenceError("EDGE_ID_INVALID_OR_DUPLICATE")
        edge_ids.add(edge["id"])
        if not isinstance(edge["type"], str) or edge["type"] not in ENDPOINTS:
            raise EvidenceError("UNKNOWN_EDGE_TYPE")
        if not isinstance(edge["source"], str) or not isinstance(edge["target"], str):
            raise EvidenceError("EDGE_ENDPOINT_INVALID")
        if edge["source"] not in nodes or edge["target"] not in nodes:
            raise EvidenceError("DANGLING_REFERENCE")
        source, target = nodes[edge["source"]], nodes[edge["target"]]
        if (source["type"], target["type"]) not in ENDPOINTS[edge["type"]]:
            raise EvidenceError("EDGE_ENDPOINT_TYPE_INVALID")
        if edge.get("citation_context", "current") not in ("current", "historical"):
            raise EvidenceError("CITATION_CONTEXT_INVALID")
        if edge["type"] == "SUPERSEDES" and (source["logical_id"] != target["logical_id"]
                                               or source["version"] == target["version"]):
            raise EvidenceError("SUPERSEDES_IDENTITY_INVALID")
        edges.append(edge)
    dependency = [(e["source"], e["target"]) for e in edges if e["type"] in ("DERIVED_FROM", "DEPENDS_ON")]
    dependency += [(r["source"], r["target"]) for r in refs]
    dag(nodes, dependency, limits.depth, "DEPENDENCY_CYCLE")
    dag(nodes, [(e["source"], e["target"]) for e in edges if e["type"] == "SUPERSEDES"],
        limits.depth, "SUPERSEDES_CYCLE")
    return nodes, edges, refs, findings


def graph_digest(nodes: dict, edges: list) -> str:
    ordered = []
    for node in sorted(nodes.values(), key=lambda n: n["id"]):
        copy = dict(node)
        for key in ("source_refs", "record_refs", "artifact_refs"):
            if key in copy:
                copy[key] = sorted(copy[key])
        ordered.append(copy)
    return hashlib.sha256(canonical({"schema": SCHEMA, "nodes": ordered,
                                    "edges": sorted(edges, key=edge_key)})).hexdigest()


def edge_key(e: dict):
    return e["type"], e["source"], e["target"], e["id"]


def trace_scope(claim: str, nodes: dict, edges: list, refs: list, limit: int) -> tuple[set, list, list]:
    if claim not in nodes or nodes[claim]["type"] != "Claim":
        raise EvidenceError("UNKNOWN_CLAIM")
    queue, seen, visited_edges, visited_refs = deque([(claim, 0)]), set(), {}, {}
    while queue:
        nid, depth = queue.popleft()
        if nid in seen:
            continue
        if depth > limit:
            raise EvidenceError("TRACE_DEPTH_EXCEEDED")
        seen.add(nid)
        for e in edges:
            incoming = e["target"] == nid and e["type"] in ("SUPPORTS", "CONTRADICTS")
            outgoing = e["source"] == nid and e["type"] in ("DERIVED_FROM", "DEPENDS_ON", "CONTRADICTS")
            if incoming or outgoing:
                visited_edges[e["id"]] = e
                queue.append((e["source"] if incoming else e["target"], depth + 1))
        for r in refs:
            if r["source"] == nid:
                visited_refs[(r["source"], r["field"], r["target"])] = r
                queue.append((r["target"], depth + 1))
    return seen, list(visited_edges.values()), list(visited_refs.values())


def health(nodes: dict, edges: list, refs: list) -> list:
    findings = []
    superseded = {e["target"] for e in edges if e["type"] == "SUPERSEDES"}
    groups = defaultdict(list)
    for node in nodes.values():
        if node["id"] not in superseded:
            groups[node["logical_id"]].append(node["id"])
    for members in groups.values():
        if len(members) > 1:
            findings.extend(finding("VERSION_FORK_UNRESOLVED", node_id=nid) for nid in members)
    support, contradict = defaultdict(list), defaultdict(list)
    for edge in edges:
        if edge["type"] in ("SUPPORTS", "CONTRADICTS"):
            (support if edge["type"] == "SUPPORTS" else contradict)[edge["target"]].append(edge["source"])
        stale_id = edge["source"] if edge["type"] in ("SUPPORTS", "CONTRADICTS") else edge["target"]
        if edge["type"] != "SUPERSEDES" and stale_id in superseded:
            historical = edge.get("citation_context") == "historical"
            findings.append(finding("SUPERSEDED_HISTORICAL_CITATION" if historical else "STALE_CURRENT_REFERENCE",
                                    "INFO" if historical else "UNRESOLVED", stale_id))
    for ref in refs:
        if ref["target"] in superseded:
            historical = ref["source"] in superseded
            findings.append(finding("SUPERSEDED_HISTORICAL_CITATION" if historical else "STALE_CURRENT_REFERENCE",
                                    "INFO" if historical else "UNRESOLVED", ref["target"]))
    for nid in support.keys() & contradict.keys():
        findings.append(finding("SUPPORT_AND_CONTRADICTION_DECLARED", node_id=nid))
    for nid, node in nodes.items():
        if node.get("resolution") in ("ABSTAIN", "UNRESOLVED") or node.get("outcome") in ("ABSTAIN", "UNRESOLVED"):
            findings.append(finding("EXPLICIT_" + node.get("outcome", node.get("resolution")), node_id=nid))
        if node.get("unresolved_reason"):
            findings.append(finding("DECLARED_UNRESOLVED_METADATA", node_id=nid))
        if node["type"] == "Claim" and not support[nid] and not contradict[nid]:
            findings.append(finding("CLAIM_EVIDENCE_CHAIN_MISSING", node_id=nid))
        if node["type"] == "Evidence" and not node["source_refs"] and not any(
                e["source"] == nid and e["type"] in ("DERIVED_FROM", "DEPENDS_ON") for e in edges):
            findings.append(finding("EVIDENCE_PROVENANCE_MISSING", node_id=nid))
    return findings


def finish(result: dict) -> dict:
    result["findings"] = sorted({canonical(x): x for x in result["findings"]}.values(),
                                key=lambda x: (x["code"], x["node_id"], x["path"], x["severity"]))
    levels = {x["severity"] for x in result["findings"]}
    result["status"] = "INVALID" if "INVALID" in levels else "UNRESOLVED" if "UNRESOLVED" in levels else "PASS"
    result["result_content_sha256"] = hashlib.sha256(canonical(result)).hexdigest()
    return result


def exit_code(result: dict) -> int:
    return {"PASS": 0, "INVALID": 1, "UNRESOLVED": 2}[result["status"]]


def run(graph_path: str | Path, command: str = "validate", *, claim: str | None = None,
        root: str | Path | None = None, output: str | Path | None = None,
        limits: Limits = Limits()) -> dict:
    result = {"schema": SCHEMA, "command": command, "graph_content_sha256": None,
              "findings": [], "nodes_visited": [], "edges_visited": [],
              "reference_observations": [], "artifact_observations": [],
              "scope_limits": {"budgets": asdict(limits), "scientific_adjudication": "NOT_PERFORMED",
                               "input_verification_labels": "DECLARATIONS_ONLY",
                               "network_execution_and_hydration": "NOT_PERFORMED",
                               "historical_identity": "NOT_INFERRED_FROM_CURRENT_HASH",
                               "file_identity": "Stable descriptor checks; portable byte digest. Inodes and times excluded from result digest."}}
    confined = None
    try:
        if command not in ("validate", "trace", "doctor"):
            raise EvidenceError("UNKNOWN_COMMAND")
        if any(type(x) is not int or x <= 0 for x in asdict(limits).values()):
            raise EvidenceError("INVALID_LIMITS")
        path = Path(os.path.abspath(graph_path))
        base = Path(os.path.abspath(root)) if root is not None else path.parent
        try:
            graph_rel = str(path.relative_to(base))
        except ValueError as exc:
            raise EvidenceError("GRAPH_OUTSIDE_ROOT") from exc
        with no_download():
            confined = Root(base)
            try:
                payload = confined.read(graph_rel, limits.graph_bytes, keep_bytes=True)["data"]
            except EvidenceError as exc:
                if exc.code == "ARTIFACT_BUDGET_EXCEEDED":
                    raise EvidenceError("GRAPH_BUDGET_EXCEEDED") from exc
                raise
            graph = strict_json(payload, limits)
            nodes, edges, refs, declarations = validate_graph(graph, limits)
            result["graph_content_sha256"] = graph_digest(nodes, edges)
            protected = {graph_rel} | {n["path"] for n in nodes.values() if n["type"] == "Artifact"}
            out_rel = confined.output_relative(output, protected) if output is not None else None
            scope = set(nodes)
            scoped_edges, scoped_refs = edges, refs
            if command == "trace":
                scope, scoped_edges, scoped_refs = trace_scope(claim or "", nodes, edges, refs, limits.depth)
            # Keep graph-wide version-health warnings: a fork outside traversal can affect current selection.
            result["findings"].extend(declarations)
            if command != "validate":
                result["findings"].extend(health(nodes, edges, refs))
            result["nodes_visited"] = sorted((nodes[n] for n in scope), key=lambda n: n["id"])
            result["edges_visited"] = sorted(scoped_edges, key=edge_key)
            result["reference_observations"] = sorted(scoped_refs, key=lambda r: (r["source"], r["field"], r["target"]))
            budget = {"remaining": limits.total_artifact_bytes}
            if command != "validate":
                for nid in sorted(scope):
                    node = nodes[nid]
                    if node["type"] != "Artifact":
                        continue
                    observation = {"node_id": nid, "path": node["path"],
                                   "declared_version": node["version"], "expected_sha256": node.get("sha256")}
                    try:
                        if budget["remaining"] <= 0:
                            raise EvidenceError("TOTAL_ARTIFACT_BUDGET_EXCEEDED", "UNRESOLVED")
                        seen = confined.read(node["path"], min(limits.artifact_bytes, budget["remaining"]),
                                             budget=budget)
                        observation.update(seen)
                        if not node.get("sha256"):
                            observation["status"] = "OBSERVED_WITHOUT_DECLARED_IDENTITY"
                            result["findings"].append(finding("ARTIFACT_IDENTITY_UNRESOLVED", node_id=nid, path=node["path"]))
                        elif seen["sha256"] != node["sha256"]:
                            observation["status"] = "IDENTITY_MISMATCH"
                            result["findings"].append(finding("IDENTITY_MISMATCH", "INVALID", nid, node["path"]))
                        else:
                            observation["status"] = "MECHANICALLY_VERIFIED"
                    except EvidenceError as exc:
                        observation["status"] = exc.code
                        result["findings"].append(finding(exc.code, exc.severity, nid, node["path"]))
                    result["artifact_observations"].append(observation)
            result["scope_limits"]["artifact_bytes_read"] = limits.total_artifact_bytes - budget["remaining"]
            result = finish(result)
        # A failed policy restoration must not publish a success-shaped report.
        if out_rel is not None:
            confined.publish(out_rel, result)
        return result
    except EvidenceError as exc:
        result.pop("result_content_sha256", None)
        result["findings"].append(finding(exc.code, exc.severity))
        return finish(result)
    except (OSError, UnicodeError) as exc:
        result.pop("result_content_sha256", None)
        result["findings"].append(finding("LOCAL_IO_UNAVAILABLE", "UNRESOLVED"))
        return finish(result)
    finally:
        if confined is not None:
            confined.close()
