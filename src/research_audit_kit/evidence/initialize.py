# SPDX-License-Identifier: Apache-2.0
"""Generate a declared evidence graph from a user-supplied asset list."""
from __future__ import annotations

from dataclasses import asdict
import json
import os
from pathlib import Path
import re

from .core import (Limits, SCHEMA, edge_key, finding, finish, graph_digest,
                   strict_json, text, validate_graph)
from .fs import EvidenceError, Root, no_download, relative_path

ASSET_LIST_SCHEMA = "researchauditkit.asset-list/v1"
INIT_SCHEMA = "researchauditkit.evidence-init/v1"


def _name(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", value):
        raise EvidenceError("ASSET_LIST_NAME_INVALID")
    return value


def scaffold(manifest, namespace, version, limits):
    """Validate the entire declaration before opening any asset payload."""
    if (manifest.get("schema") != ASSET_LIST_SCHEMA
            or set(manifest) - {"schema", "assets", "claims"}
            or not isinstance(manifest.get("assets"), list) or not manifest["assets"]
            or not isinstance(manifest.get("claims", []), list)):
        raise EvidenceError("ASSET_LIST_SCHEMA_INVALID")
    assets = manifest["assets"]
    claims = manifest.get("claims", [])
    if 2 * len(assets) + len(claims) > limits.nodes:
        raise EvidenceError("GRAPH_SIZE_BUDGET_EXCEEDED")
    if not isinstance(namespace, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", namespace):
        raise EvidenceError("NAMESPACE_INVALID")
    if (not isinstance(version, str)
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", version)
            or version.lower() in {"latest", "current", "head", "main", "master"}):
        raise EvidenceError("VERSION_IDENTITY_INVALID")

    def node(kind, name, **fields):
        logical = f"urn:rak:{namespace}:{kind.lower()}:{name}"
        return dict(id=logical + "@" + version, logical_id=logical, version=version,
                    type=kind, assertion_level="DECLARED", **fields)

    nodes, edges, by_name, paths = [], [], {}, set()
    for asset in assets:
        if (not isinstance(asset, dict) or not {"name", "path"}.issubset(asset)
                or set(asset) - {"name", "path", "media_type"}):
            raise EvidenceError("ASSET_FIELDS_INVALID")
        name = _name(asset["name"])
        path = relative_path(asset["path"])
        if name in by_name or path in paths:
            raise EvidenceError("DUPLICATE_ASSET")
        media = asset.get("media_type", "application/octet-stream")
        if not text(media):
            raise EvidenceError("INVALID_TEXT_FIELD")
        artifact = node("Artifact", name, path=path, media_type=media,
                        unresolved_reason="IDENTITY_NOT_CAPTURED")
        evidence = node("Evidence", name, description=f"User-listed asset record: {name}",
                        source_refs=[artifact["id"]])
        by_name[name] = (artifact, evidence)
        paths.add(path)
        nodes.extend([artifact, evidence])
    claim_names = set()
    for claim in claims:
        if (not isinstance(claim, dict) or not {"name", "statement"}.issubset(claim)
                or set(claim) - {"name", "statement", "supports", "contradicts"}):
            raise EvidenceError("CLAIM_FIELDS_INVALID")
        name = _name(claim["name"])
        if name in claim_names:
            raise EvidenceError("DUPLICATE_CLAIM")
        claim_names.add(name)
        if not text(claim["statement"]):
            raise EvidenceError("INVALID_TEXT_FIELD")
        generated = node("Claim", name, statement=claim["statement"], resolution="UNRESOLVED")
        nodes.append(generated)
        for field, kind in (("supports", "SUPPORTS"), ("contradicts", "CONTRADICTS")):
            refs = claim.get(field, [])
            if (not isinstance(refs, list) or not all(isinstance(ref, str) for ref in refs)
                    or len(refs) != len(set(refs))):
                raise EvidenceError("INVALID_REFERENCE_LIST")
            for ref in refs:
                if ref not in by_name:
                    raise EvidenceError("UNKNOWN_ASSET_REFERENCE")
                edges.append(dict(id=f"{kind.lower()}:{ref}:{name}", type=kind,
                                  source=by_name[ref][1]["id"], target=generated["id"]))
                if len(edges) > limits.edges:
                    raise EvidenceError("GRAPH_SIZE_BUDGET_EXCEEDED")
    graph = dict(schema=SCHEMA, nodes=nodes, edges=edges)
    validate_graph(graph, limits)
    return graph, by_name


def initialize(manifest_path: str | Path, *, output: str | Path,
               root: str | Path | None = None, namespace: str = "project", version: str = "1",
               limits: Limits = Limits()) -> dict:
    result = dict(schema=INIT_SCHEMA, command="init", findings=[],
                  manifest_content_sha256=None, graph_content_sha256=None,
                  output_path=None, output_created=False, generated_node_counts={},
                  artifact_observations=[], scope_limits={
                      "budgets": asdict(limits), "artifact_bytes_read": 0,
                      "identity_capture": "CURRENT_BYTES_ONLY",
                      "claim_resolution": "UNRESOLVED_DECLARATIONS_ONLY",
                      "relationships": "USER_SUPPLIED_ONLY",
                      "scientific_adjudication": "NOT_PERFORMED",
                      "network_execution_and_hydration": "NOT_PERFORMED"})
    confined = None
    total = limits.total_artifact_bytes if type(limits.total_artifact_bytes) is int and limits.total_artifact_bytes > 0 else 0
    budget = {"remaining": total}
    try:
        if any(type(value) is not int or value <= 0 for value in asdict(limits).values()):
            raise EvidenceError("INVALID_LIMITS")
        if output is None:
            raise EvidenceError("OUTPUT_REQUIRED")
        path = Path(os.path.abspath(manifest_path))
        base = Path(os.path.abspath(root)) if root is not None else path.parent
        try:
            relative = path.relative_to(base).as_posix()
        except ValueError as exc:
            raise EvidenceError("MANIFEST_OUTSIDE_ROOT") from exc
        with no_download():
            confined = Root(base)
            try:
                observed = confined.read(relative, limits.graph_bytes, keep_bytes=True)
            except EvidenceError as exc:
                if exc.code == "ARTIFACT_BUDGET_EXCEEDED":
                    raise EvidenceError("MANIFEST_BUDGET_EXCEEDED") from exc
                raise
            result["manifest_content_sha256"] = observed["sha256"]
            manifest = strict_json(observed["data"], limits)
            graph, assets = scaffold(manifest, namespace, version, limits)
            protected = {relative} | {artifact["path"] for artifact, _ in assets.values()}
            out_relative = confined.output_relative(output, protected)
            result["output_path"] = out_relative
            for name in sorted(assets):
                artifact, _ = assets[name]
                observation = dict(node_id=artifact["id"], path=artifact["path"],
                                   declared_version=version, expected_sha256=None)
                try:
                    if budget["remaining"] <= 0:
                        raise EvidenceError("TOTAL_ARTIFACT_BUDGET_EXCEEDED", "UNRESOLVED")
                    seen = confined.read(artifact["path"],
                                         min(limits.artifact_bytes, budget["remaining"]),
                                         budget=budget)
                    artifact.pop("unresolved_reason")
                    artifact["sha256"] = seen["sha256"]
                    observation.update(seen, status="IDENTITY_CAPTURED")
                except EvidenceError as exc:
                    observation["status"] = exc.code
                    result["artifact_observations"].append(observation)
                    if exc.severity == "INVALID":
                        raise
                    artifact["unresolved_reason"] = exc.code
                    result["findings"].append(finding(exc.code, exc.severity,
                                                       artifact["id"], artifact["path"]))
                    continue
                result["artifact_observations"].append(observation)
            nodes, edges, _, _ = validate_graph(graph, limits)
            graph = dict(schema=SCHEMA, nodes=sorted(nodes.values(), key=lambda n: n["id"]),
                         edges=sorted(edges, key=edge_key))
            payload_bytes = len((json.dumps(graph, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode())
            if payload_bytes > limits.graph_bytes:
                raise EvidenceError("GENERATED_GRAPH_BUDGET_EXCEEDED")
            result["graph_content_sha256"] = graph_digest(nodes, edges)
            result["generated_node_counts"] = {
                kind: sum(node["type"] == kind for node in nodes.values())
                for kind in ("Artifact", "Evidence", "Claim")
            }
        # Restoration must succeed before the new graph is published.
        confined.publish(out_relative, graph)
        result["output_created"] = True
    except EvidenceError as exc:
        result["findings"].append(finding(exc.code, exc.severity))
    except (OSError, UnicodeError):
        result["findings"].append(finding("LOCAL_IO_UNAVAILABLE"))
    finally:
        result["scope_limits"]["artifact_bytes_read"] = total - budget["remaining"]
        if confined is not None:
            confined.close()
    return finish(result)
