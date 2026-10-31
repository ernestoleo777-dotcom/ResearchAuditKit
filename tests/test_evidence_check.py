from __future__ import annotations

from contextlib import contextmanager
from dataclasses import replace
import hashlib
import json

import pytest

from research_audit_kit.cli import main
from research_audit_kit.evidence import Limits, exit_code, run
from research_audit_kit.evidence import fs
from research_audit_kit.evidence.core import canonical
from research_audit_kit.evidence.initialize import initialize


CLAIM = "urn:rak:project:claim:main@1"


def baseline(root, *, claims=True):
    (root / "result.txt").write_bytes(b"synthetic result\n")
    manifest = {"schema": "researchauditkit.asset-list/v1",
                "assets": [{"name": "result", "path": "result.txt"}]}
    if claims:
        manifest["claims"] = [{"name": "main", "statement": "An explicit declaration",
                               "supports": ["result"]}]
    (root / "assets.json").write_text(json.dumps(manifest))
    receipt = initialize(root / "assets.json", output="graph.json")
    return root / "graph.json", receipt["graph_content_sha256"]


def check(path, anchor, **kwargs):
    return run(path, "check", expected_graph_sha256=anchor,
               allow_unresolved_claims=(CLAIM,), **kwargs)


def codes(result):
    return {item["code"] for item in result["findings"]}


def test_gate_pass_is_separate_from_claim_resolution_and_retains_report(tmp_path):
    path, anchor = baseline(tmp_path)
    before = path.read_bytes()
    result = check(path, anchor, output="check.json")
    assert exit_code(result) == 0 and result["mechanical_gate"] == "PASS"
    assert result["evidence_status"] == "UNRESOLVED"
    assert result["accepted_findings"][0]["node_id"] == CLAIM
    assert result["evidence_result"] == run(path, "impact")
    assert json.loads((tmp_path / "check.json").read_text()) == result
    assert path.read_bytes() == before
    digest = result.pop("result_content_sha256")
    assert digest == hashlib.sha256(canonical(result)).hexdigest()


def test_no_implicit_unresolved_allowance(tmp_path):
    path, anchor = baseline(tmp_path)
    result = run(path, "check", expected_graph_sha256=anchor)
    assert result["mechanical_gate"] == "FAIL" and exit_code(result) == 2
    assert "EXPLICIT_UNRESOLVED" in codes(result)
    assert result["accepted_findings"] == []


def test_artifact_only_graph_can_pass_without_allowance(tmp_path):
    path, anchor = baseline(tmp_path, claims=False)
    assert run(path, "check", expected_graph_sha256=anchor)["status"] == "PASS"


@pytest.mark.parametrize("fault", ["changed", "missing", "no_digest", "symlink"])
def test_faults_block_and_retain_impact_paths(tmp_path, fault):
    path, anchor = baseline(tmp_path)
    if fault == "changed":
        (tmp_path / "result.txt").write_bytes(b"replacement\n")
    elif fault == "missing":
        (tmp_path / "result.txt").unlink()
    elif fault == "symlink":
        (tmp_path / "result.txt").unlink()
        (tmp_path / "result.txt").symlink_to(tmp_path / "assets.json")
    else:
        graph = json.loads(path.read_text())
        artifact = next(n for n in graph["nodes"] if n["type"] == "Artifact")
        artifact.pop("sha256")
        artifact["unresolved_reason"] = "No expected digest"
        path.write_text(json.dumps(graph))
        anchor = run(path)["graph_content_sha256"]
    result = check(path, anchor)
    assert result["mechanical_gate"] == "FAIL"
    assert "CHECK_IDENTITIES_INCOMPLETE" in codes(result)
    assert result["evidence_result"]["impact_analysis"]["potentially_affected_claim_ids"] == [CLAIM]


@pytest.mark.parametrize("anchor", [None, "", "0" * 64, "A" * 64, []])
def test_bad_or_changed_anchor_stops_before_artifact_reads(tmp_path, monkeypatch, anchor):
    path, _ = baseline(tmp_path)
    original = fs.Root.read
    def graph_only(self, relative, *args, **kwargs):
        assert relative == "graph.json"
        return original(self, relative, *args, **kwargs)
    monkeypatch.setattr(fs.Root, "read", graph_only)
    result = check(path, anchor)
    assert exit_code(result) == 1 and result["mechanical_gate"] == "FAIL"
    assert not result["evidence_result"]["artifact_observations"]


def test_rewritten_baseline_cannot_hide_changed_asset(tmp_path):
    path, anchor = baseline(tmp_path)
    (tmp_path / "result.txt").write_bytes(b"replacement")
    graph = json.loads(path.read_text())
    next(n for n in graph["nodes"] if n["type"] == "Artifact")["sha256"] = hashlib.sha256(b"replacement").hexdigest()
    path.write_text(json.dumps(graph))
    assert "GRAPH_ANCHOR_MISMATCH" in codes(check(path, anchor))


@pytest.mark.parametrize("allowed", [(CLAIM, CLAIM), ("unknown",),
                                     ("urn:rak:project:artifact:result@1",), ([],), None])
def test_allowance_is_exact_and_validated(tmp_path, allowed):
    path, anchor = baseline(tmp_path)
    result = run(path, "check", expected_graph_sha256=anchor, allow_unresolved_claims=allowed)
    assert exit_code(result) == 1


@pytest.mark.parametrize("fault", ["unlinked", "abstain", "metadata", "contradiction"])
def test_claim_allowance_never_suppresses_other_findings(tmp_path, fault):
    path, _ = baseline(tmp_path)
    graph = json.loads(path.read_text())
    claim = next(n for n in graph["nodes"] if n["type"] == "Claim")
    if fault == "unlinked":
        graph["edges"] = []
    elif fault == "abstain":
        claim["resolution"] = "ABSTAIN"
    elif fault == "metadata":
        next(n for n in graph["nodes"] if n["type"] == "Artifact")["unresolved_reason"] = "Unknown origin"
    else:
        graph["edges"].append(dict(graph["edges"][0], id="opposition", type="CONTRADICTS"))
    path.write_text(json.dumps(graph))
    anchor = run(path)["graph_content_sha256"]
    result = check(path, anchor)
    assert result["mechanical_gate"] == "FAIL" and exit_code(result) != 0


def test_no_artifacts_is_not_vacuous_success(tmp_path):
    path, _ = baseline(tmp_path)
    graph = json.loads(path.read_text())
    graph["nodes"] = [n for n in graph["nodes"] if n["type"] == "Claim"]
    graph["edges"] = []
    path.write_text(json.dumps(graph))
    anchor = run(path)["graph_content_sha256"]
    assert "CHECK_ARTIFACT_SCOPE_EMPTY" in codes(check(path, anchor))


def test_read_budget_and_invalid_limits_fail_closed(tmp_path):
    path, anchor = baseline(tmp_path)
    assert check(path, anchor, limits=replace(Limits(), artifact_bytes=1))["mechanical_gate"] == "FAIL"
    assert "INVALID_LIMITS" in codes(check(path, anchor, limits=replace(Limits(), nodes=False)))


def test_output_collision_and_missing_asset_output_are_protected(tmp_path):
    path, anchor = baseline(tmp_path)
    before = path.read_bytes()
    assert check(path, anchor, output="graph.json")["status"] == "INVALID"
    assert path.read_bytes() == before
    (tmp_path / "result.txt").unlink()
    assert check(path, anchor, output="result.txt")["status"] == "INVALID"
    assert not (tmp_path / "result.txt").exists()


def test_policy_restoration_and_publication_failure_cannot_return_pass(tmp_path, monkeypatch):
    path, anchor = baseline(tmp_path)
    @contextmanager
    def failed_restore():
        yield
        raise fs.EvidenceError("POLICY_RESTORE_FAILED")
    with monkeypatch.context() as patch:
        patch.setattr("research_audit_kit.evidence.core.no_download", failed_restore)
        assert check(path, anchor, output="restore.json")["mechanical_gate"] == "FAIL"
        assert not (tmp_path / "restore.json").exists()
    def failed_publish(*args):
        raise fs.EvidenceError("OUTPUT_WRITE_FAILED")
    monkeypatch.setattr(fs.Root, "publish", failed_publish)
    result = check(path, anchor, output="failure.json")
    assert result["mechanical_gate"] == "FAIL" and "OUTPUT_WRITE_FAILED" in codes(result)


def test_cli_json_and_human_exit_codes(tmp_path, capsys):
    path, anchor = baseline(tmp_path)
    args = ["evidence", "check", str(path), "--graph-sha256", anchor,
            "--allow-unresolved-claim", CLAIM]
    assert main(args) == 0
    assert json.loads(capsys.readouterr().out)["mechanical_gate"] == "PASS"
    (tmp_path / "result.txt").write_bytes(b"changed")
    assert main(args + ["--format", "human"]) == 1
    text = capsys.readouterr().out
    assert "Mechanical gate: FAIL" in text and "Claim to review:" in text
    assert CLAIM in text


def test_incomplete_impact_is_a_blocker(tmp_path):
    path, anchor = baseline(tmp_path)
    (tmp_path / "result.txt").write_bytes(b"changed")
    result = check(path, anchor, limits=replace(Limits(), depth=1))
    assert "CHECK_IMPACT_INCOMPLETE" in codes(result)
    assert result["evidence_result"]["impact_analysis"]["analysis_status"] == "INCOMPLETE"


def test_semantic_anchor_ignores_format_and_order_only(tmp_path):
    path, anchor = baseline(tmp_path)
    graph = json.loads(path.read_text())
    graph["nodes"].reverse()
    graph["edges"].reverse()
    path.write_text(json.dumps(graph, indent=4))
    assert check(path, anchor)["mechanical_gate"] == "PASS"
