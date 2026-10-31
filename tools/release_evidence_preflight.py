# SPDX-License-Identifier: Apache-2.0
"""First-party candidate-build evidence checks. Never publish or inspect target code."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from research_audit_kit import __version__
from research_audit_kit.evidence import Limits, run
from research_audit_kit.evidence.core import strict_json
from research_audit_kit.evidence.fs import EvidenceError, Root, no_download
from research_audit_kit.evidence.initialize import ASSET_LIST_SCHEMA, INIT_SCHEMA, initialize

SCHEMA = "researchauditkit.release-preflight/v1"
CLAIM = "The local candidate build lists one wheel and one source distribution."
NAMESPACE = "rak-release"


def names(version):
    if (not isinstance(version, str)
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", version)
            or version != __version__):
        raise EvidenceError("PACKAGE_VERSION_MISMATCH")
    return {"wheel": f"research_audit_kit-{version}-py3-none-any.whl",
            "sdist": f"research_audit_kit-{version}.tar.gz"}


def publish(root, name, record):
    handle = None
    try:
        with no_download():
            handle = Root(root)
            relative = handle.output_relative(name, set())
        handle.publish(relative, record)
    finally:
        if handle is not None:
            handle.close()


def read(root, name, *, keep_bytes=False):
    with no_download():
        handle = Root(root)
        try:
            return handle.read(name, Limits().graph_bytes, keep_bytes=keep_bytes)
        finally:
            handle.close()


def capture(root, version):
    artifacts = names(version)
    manifest = {"schema": ASSET_LIST_SCHEMA,
                "assets": [{"name": key, "path": path} for key, path in sorted(artifacts.items())],
                "claims": [{"name": "candidate", "statement": CLAIM,
                            "supports": sorted(artifacts)}]}
    publish(root, "release-assets.json", manifest)
    receipt = initialize(Path(root) / "release-assets.json", root=root,
                         output="release-graph.json", namespace=NAMESPACE, version=version)
    if (receipt["status"] != "PASS" or not receipt["output_created"]
            or any(row.get("bytes", 0) <= 0 for row in receipt["artifact_observations"])):
        raise EvidenceError("CANDIDATE_CAPTURE_INCOMPLETE", "UNRESOLVED")
    publish(root, "release-capture.json", receipt)
    digest = read(root, "release-capture.json")["sha256"]
    return dict(schema=SCHEMA, mode="capture", status="PASS", candidate_only=True,
                package_version=version, capture_receipt_sha256=digest,
                publication_performed=False, claim_resolution="UNRESOLVED")


def _capture_receipt(root, version, expected_digest):
    if not isinstance(expected_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_digest):
        raise EvidenceError("CAPTURE_ANCHOR_REQUIRED")
    observed = read(root, "release-capture.json", keep_bytes=True)
    if observed["sha256"] != expected_digest:
        raise EvidenceError("CAPTURE_ANCHOR_MISMATCH")
    receipt = strict_json(observed["data"], Limits())
    expected = names(version)
    rows = receipt.get("artifact_observations")
    if (receipt.get("schema") != INIT_SCHEMA or receipt.get("status") != "PASS"
            or receipt.get("output_created") is not True
            or receipt.get("output_path") != "release-graph.json"
            or not isinstance(rows, list) or len(rows) != 2
            or any(not isinstance(row, dict) or not isinstance(row.get("path"), str)
                   or type(row.get("bytes")) is not int or row["bytes"] <= 0
                   or not isinstance(row.get("sha256"), str)
                   or not re.fullmatch(r"[0-9a-f]{64}", row["sha256"]) for row in rows)):
        raise EvidenceError("CAPTURE_RECEIPT_INVALID")
    if ({row.get("path") for row in rows} != set(expected.values())
            or any(row.get("declared_version") != version
                   or row.get("status") != "IDENTITY_CAPTURED" for row in rows)):
        raise EvidenceError("CAPTURE_SCOPE_MISMATCH")
    if read(root, "release-assets.json")["sha256"] != receipt.get("manifest_content_sha256"):
        raise EvidenceError("ASSET_LIST_CHANGED_AFTER_CAPTURE")
    return receipt


def check(root, version, expected_digest):
    artifacts = names(version)
    receipt = _capture_receipt(root, version, expected_digest)
    graph = Path(root) / "release-graph.json"
    doctor = run(graph, "doctor", root=root, output="release-doctor.json")
    impact = run(graph, "impact", root=root, output="release-impact.json")
    claim_id = f"urn:rak:{NAMESPACE}:claim:candidate@{version}"
    expected_ids = {claim_id} | {
        f"urn:rak:{NAMESPACE}:{kind}:{name}@{version}"
        for kind in ("artifact", "evidence") for name in artifacts
    }

    def mechanically_complete(report):
        observations = report["artifact_observations"]
        declarations = report["nodes_visited"]
        return (
            report["status"] == "UNRESOLVED"
            and report["graph_content_sha256"] == receipt.get("graph_content_sha256")
            and {node["id"] for node in declarations} == expected_ids
            and all(node["assertion_level"] == "DECLARED" for node in declarations)
            and any(node["id"] == claim_id and node.get("resolution") == "UNRESOLVED"
                    and node.get("statement") == CLAIM for node in declarations)
            and len(observations) == 2
            and {row["path"] for row in observations} == set(artifacts.values())
            and all(row["status"] == "MECHANICALLY_VERIFIED" and row.get("bytes", 0) > 0
                    for row in observations)
            and report["findings"] == [{"code": "EXPLICIT_UNRESOLVED", "severity": "UNRESOLVED",
                                       "node_id": claim_id, "path": ""}]
        )

    checks = {
        "doctor_identity_checks": mechanically_complete(doctor),
        "impact_identity_checks": mechanically_complete(impact),
        "impact_analysis_complete": impact["impact_analysis"]["analysis_status"] == "COMPLETE",
        "no_artifact_identity_issues": impact["impact_analysis"]["artifacts"] == [],
    }
    passed = all(checks.values())
    result = dict(schema=SCHEMA, mode="check", status="PASS" if passed else "FAIL",
                  candidate_only=True, package_version=version, checks=checks,
                  capture_receipt_sha256=expected_digest,
                  artifact_observations=doctor["artifact_observations"],
                  findings=impact["findings"],
                  evidence_status=impact["status"], claim_resolution="UNRESOLVED",
                  potentially_affected_claim_ids=impact["impact_analysis"]["potentially_affected_claim_ids"],
                  publication_performed=False,
                  scope="CURRENT_CANDIDATE_IDENTITIES_ONLY; supplied anchor, no independent attestation")
    publish(root, "release-gate.json", result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("capture", "check"))
    parser.add_argument("--root", required=True, help="existing candidate build directory")
    parser.add_argument("--version", required=True)
    parser.add_argument("--capture-sha256", help="separately retained capture receipt digest for check")
    args = parser.parse_args(argv)
    try:
        root = Path(args.root).absolute()
        result = capture(root, args.version) if args.mode == "capture" else check(root, args.version, args.capture_sha256)
    except EvidenceError as exc:
        result = dict(schema=SCHEMA, mode=args.mode, status="ERROR", error=exc.code,
                      candidate_only=True, publication_performed=False)
    except (OSError, ValueError, UnicodeError):
        result = dict(schema=SCHEMA, mode=args.mode, status="ERROR", error="LOCAL_INPUT_UNAVAILABLE",
                      candidate_only=True, publication_performed=False)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
