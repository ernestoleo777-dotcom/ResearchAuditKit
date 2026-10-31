from __future__ import annotations

from dataclasses import replace
import json

import pytest

from research_audit_kit.cli import main
from research_audit_kit.evidence import Limits, exit_code, run
from research_audit_kit.evidence import fs
from research_audit_kit.evidence.impact import analyze
from test_evidence_graph_b1 import codes, edge, fixture, node, save


def test_changed_artifact_reaches_declared_claim_with_witness(tmp_path):
    path, graph, n = fixture(tmp_path)
    (tmp_path / "artifact.txt").write_bytes(b"changed")
    result = run(path, "impact")
    impact = result["impact_analysis"]
    assert exit_code(result) == 1
    assert impact["analysis_status"] == "COMPLETE"
    assert impact["potentially_affected_claim_ids"] == [n["claim"]["id"]]
    report = impact["artifacts"][0]
    assert report["identity_change"] == "CONFIRMED"
    assert report["claim_paths"] == [{
        "claim_id": n["claim"]["id"], "claim_version_state": "NOT_SUPERSEDED",
        "citation_context": "current",
        "node_ids": [n["artifact"]["id"], n["evidence"]["id"], n["claim"]["id"]],
        "relations": ["DERIVED_FROM", "SUPPORTS"],
    }]
    assert n["run"]["id"] in report["reached_node_ids"]
    assert result["scope_limits"]["scientific_adjudication"] == "NOT_PERFORMED"


@pytest.mark.parametrize("state", ["matched", "missing", "no-expected-hash", "budget"])
def test_identity_states_are_not_promoted_to_confirmed_change(tmp_path, state):
    path, graph, n = fixture(tmp_path)
    limits = Limits()
    if state == "missing":
        (tmp_path / "artifact.txt").unlink()
    elif state == "no-expected-hash":
        n["artifact"].pop("sha256")
        n["artifact"]["unresolved_reason"] = "Identity not supplied"
        save(path, graph)
    elif state == "budget":
        limits = replace(limits, artifact_bytes=1)
    result = run(path, "impact", limits=limits)
    analysis = result["impact_analysis"]
    assert result["status"] == "UNRESOLVED"
    assert analysis["analysis_status"] == "COMPLETE"
    if state == "matched":
        assert analysis["artifacts"] == []
        assert analysis["not_reached_claim_ids"] == [n["claim"]["id"]]
    else:
        assert analysis["artifacts"][0]["identity_change"] == "UNRESOLVED"
        assert analysis["potentially_affected_claim_ids"] == [n["claim"]["id"]]


def test_no_implicit_supersession_or_disconnected_claim_impact(tmp_path):
    path, graph, n = fixture(tmp_path)
    newer = dict(n["artifact"], id=n["artifact"]["logical_id"] + "@2", version="2",
                 path="new.txt")
    (tmp_path / "new.txt").write_bytes((tmp_path / "artifact.txt").read_bytes())
    separate = node("Claim", "separate", statement="Independent", resolution="UNRESOLVED")
    graph["nodes"].extend([newer, separate])
    graph["edges"].append(edge("SUPERSEDES", newer, n["artifact"], "new-version"))
    save(path, graph)
    (tmp_path / "artifact.txt").unlink()
    result = run(path, "impact")
    analysis = result["impact_analysis"]
    report = analysis["artifacts"][0]
    assert newer["id"] not in report["reached_node_ids"]
    assert separate["id"] in analysis["not_reached_claim_ids"]
    assert all(row["citation_context"] == "historical" for row in report["claim_paths"])
    assert "STALE_CURRENT_REFERENCE" in codes(result)


def test_current_and_historical_routes_remain_distinct_and_deterministic(tmp_path):
    path, graph, n = fixture(tmp_path)
    graph["edges"].append(edge("SUPPORTS", n["evidence"], n["claim"], "historic",
                               citation_context="historical"))
    save(path, graph)
    (tmp_path / "artifact.txt").unlink()
    first = run(path, "impact")
    routes = first["impact_analysis"]["artifacts"][0]["claim_paths"]
    assert {row["citation_context"] for row in routes} == {"current", "historical"}
    graph["nodes"].reverse()
    graph["edges"].reverse()
    n["evidence"]["source_refs"].reverse()
    save(path, graph)
    assert first == run(path, "impact")


def test_claim_dependencies_and_reciprocal_contradictions_terminate(tmp_path):
    path, graph, n = fixture(tmp_path)
    dependent = node("Claim", "dependent", statement="Depends on the first claim", resolution="UNRESOLVED")
    other = node("Claim", "opposing", statement="An opposing declaration", resolution="UNRESOLVED")
    graph["nodes"].extend([dependent, other])
    graph["edges"].extend([
        edge("DEPENDS_ON", dependent, n["claim"], "dependent"),
        edge("CONTRADICTS", n["claim"], other, "forward"),
        edge("CONTRADICTS", other, n["claim"], "backward"),
    ])
    save(path, graph)
    (tmp_path / "artifact.txt").unlink()
    result = run(path, "impact")
    assert result["impact_analysis"]["analysis_status"] == "COMPLETE"
    assert set(result["impact_analysis"]["potentially_affected_claim_ids"]) == {
        n["claim"]["id"], dependent["id"], other["id"],
    }


def test_typed_refs_propagate_from_protocol_to_run_to_evidence(tmp_path):
    path, graph, n = fixture(tmp_path)
    n["evidence"]["source_refs"] = [n["run"]["id"]]
    n["run"]["record_refs"] = []
    graph["edges"] = [edge("SUPPORTS", n["evidence"], n["claim"], "support")]
    save(path, graph)
    (tmp_path / "artifact.txt").unlink()
    result = run(path, "impact")
    route = result["impact_analysis"]["artifacts"][0]["claim_paths"][0]
    assert route["node_ids"] == [n["artifact"]["id"], n["protocol"]["id"],
                                  n["run"]["id"], n["evidence"]["id"], n["claim"]["id"]]
    assert route["relations"] == ["artifact_refs", "protocol_ref", "source_refs", "SUPPORTS"]


@pytest.mark.parametrize("budget,reason", [
    ({"depth": 1}, "IMPACT_DEPTH_EXCEEDED"),
    ({"edges": 1}, "IMPACT_PROPAGATION_BUDGET_EXCEEDED"),
    ({"nodes": 1}, "IMPACT_CLAIM_PATH_BUDGET_EXCEEDED"),
    ({"edges": 4}, "IMPACT_WITNESS_BUDGET_EXCEEDED"),
])
def test_bounded_analysis_never_silently_truncates(tmp_path, budget, reason):
    path, graph, n = fixture(tmp_path)
    # Use one deterministic chain and several terminal claims to isolate summary budgets.
    claims = [node("Claim", "c" + str(i), statement="Declared", resolution="UNRESOLVED")
              for i in range(3)]
    nodes = {x["id"]: x for x in [n["artifact"], n["evidence"], *claims]}
    edges = [edge("SUPPORTS", n["evidence"], claim, "s" + str(i))
             for i, claim in enumerate(claims)]
    refs = [{"source": n["evidence"]["id"], "target": n["artifact"]["id"], "field": "source_refs"}]
    observations = [{"node_id": n["artifact"]["id"], "path": "artifact.txt", "status": "MISSING"}]
    result = analyze(nodes, edges, refs, observations, replace(Limits(), **budget))
    assert result["analysis_status"] == "INCOMPLETE"
    assert reason in result["incomplete_reasons"]
    for key in ("propagation_steps", "witness_steps", "claim_paths"):
        assert result["usage"][key] <= result["limits"][key]


def test_invalid_graph_does_not_emit_complete_analysis(tmp_path):
    path = tmp_path / "graph.json"
    path.write_text('{"schema": "unknown"}')
    result = run(path, "impact")
    assert result["status"] == "INVALID"
    assert result["impact_analysis"]["analysis_status"] == "NOT_ANALYZED"


def test_safe_io_and_old_doctor_results_remain_unchanged(tmp_path, monkeypatch):
    path, graph, n = fixture(tmp_path)
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    original = fs.Root.read
    reads = []
    def observe(self, relative, *args, **kwargs):
        reads.append(relative)
        return original(self, relative, *args, **kwargs)
    monkeypatch.setattr(fs.Root, "read", observe)
    impact = run(path, "impact")
    assert reads == ["graph.json", "artifact.txt"]
    doctor = run(path, "doctor")
    assert "impact_analysis" not in doctor
    for key in doctor.keys() - {"command", "result_content_sha256"}:
        assert impact[key] == doctor[key]
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == before
    assert run(path, "impact", output="artifact.txt")["status"] == "INVALID"
    assert run(path, "impact", output="../outside.json")["status"] == "INVALID"
    saved = run(path, "impact", output="report.json")
    assert json.loads((tmp_path / "report.json").read_text()) == saved
    assert run(path, "impact", output="report.json")["status"] == "INVALID"


def test_cli_impact_reports_missing_artifact_and_witness(tmp_path, capsys):
    path, graph, n = fixture(tmp_path)
    (tmp_path / "artifact.txt").unlink()
    assert main(["evidence", "impact", str(path)]) == 2
    report = json.loads(capsys.readouterr().out)
    assert report["impact_analysis"]["artifacts"][0]["claim_paths"]


def test_cli_depth_exhaustion_adds_unresolved_finding(tmp_path):
    path, graph, n = fixture(tmp_path)
    artifact, evidence, claim = n["artifact"], n["evidence"], n["claim"]
    evidence["source_refs"] = [artifact["id"]]
    save(path, {"schema": graph["schema"], "nodes": [artifact, evidence, claim],
                "edges": [edge("SUPPORTS", evidence, claim, "support")]})
    (tmp_path / "artifact.txt").unlink()
    result = run(path, "impact", limits=replace(Limits(), depth=1))
    assert result["status"] == "UNRESOLVED"
    assert result["impact_analysis"]["analysis_status"] == "INCOMPLETE"
    assert "IMPACT_DEPTH_EXCEEDED" in codes(result)
