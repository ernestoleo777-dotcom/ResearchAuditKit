from __future__ import annotations

import copy
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess

import pytest

from research_audit_kit.evidence import Limits, SCHEMA, exit_code, run
from research_audit_kit.evidence import fs
from research_audit_kit.cli import build_parser, main


def node(kind, name, version="1", **fields):
    logical = f"urn:rak:b1test:{kind.lower()}:{name}"
    return dict(id=f"{logical}@{version}", logical_id=logical, version=version,
                type=kind, assertion_level="DECLARED", **fields)


def edge(kind, source, target, name, **fields):
    return dict(id=name, type=kind, source=source["id"], target=target["id"], **fields)


def fixture(root):
    root.mkdir(parents=True, exist_ok=True)
    payload = b"Explicit test evidence, not a scientific result.\n"
    (root / "artifact.txt").write_bytes(payload)
    artifact = node("Artifact", "payload", path="artifact.txt", media_type="text/plain",
                    sha256=hashlib.sha256(payload).hexdigest())
    protocol = node("Protocol", "protocol", description="Declared procedure", artifact_refs=[artifact["id"]])
    execution = node("ExperimentRun", "run", protocol_ref=protocol["id"], execution_status="COMPLETED",
                     record_refs=[artifact["id"]])
    evidence = node("Evidence", "evidence", description="Declared observation",
                    source_refs=[artifact["id"], execution["id"]])
    claim = node("Claim", "claim", statement="A user-authored claim", resolution="UNRESOLVED")
    decision = node("Decision", "decision", outcome="ABSTAIN", rationale="No scientific adjudication",
                    unresolved_reason="Outside mechanical scope")
    graph = dict(schema=SCHEMA, nodes=[artifact, protocol, execution, evidence, claim, decision],
                 edges=[edge("SUPPORTS", evidence, claim, "support"),
                        edge("DERIVED_FROM", evidence, artifact, "artifact-origin"),
                        edge("DERIVED_FROM", evidence, execution, "run-origin"),
                        edge("DEPENDS_ON", execution, protocol, "run-protocol"),
                        edge("DEPENDS_ON", decision, claim, "decision-context")])
    path = root / "graph.json"
    save(path, graph)
    return path, graph, dict(artifact=artifact, protocol=protocol, run=execution,
                            evidence=evidence, claim=claim, decision=decision)


def save(path, graph):
    path.write_text(json.dumps(graph), encoding="utf-8")


def codes(result):
    return {f["code"] for f in result["findings"]}


def test_eg01_meaningful_chain_and_typed_trace(tmp_path):
    path, graph, n = fixture(tmp_path)
    assert exit_code(run(path)) == 0
    report = run(path, "trace", claim=n["claim"]["id"])
    assert {x["type"] for x in report["nodes_visited"]} == {"Claim", "Evidence", "Artifact", "ExperimentRun", "Protocol"}
    assert {x["id"] for x in report["edges_visited"]} >= {"support", "artifact-origin", "run-origin", "run-protocol"}
    assert report["artifact_observations"][0]["status"] == "MECHANICALLY_VERIFIED"
    assert report["scope_limits"]["scientific_adjudication"] == "NOT_PERFORMED"
    assert report == run(path, "trace", claim=n["claim"]["id"])


def test_eg02_duplicate_ids_and_json_keys(tmp_path):
    path, graph, n = fixture(tmp_path)
    graph["nodes"].append(copy.deepcopy(n["claim"]))
    save(path, graph)
    assert "DUPLICATE_NODE_ID" in codes(run(path))
    path.write_text('{"schema":"x","schema":"y"}')
    assert "DUPLICATE_JSON_KEY" in codes(run(path))


def test_eg03_types_endpoints_and_malformed_fields(tmp_path):
    path, original, _ = fixture(tmp_path)
    for mutate in (lambda g: g["nodes"][0].update(type="Unknown"),
                   lambda g: g["edges"][0].update(type="Unknown"),
                   lambda g: g["edges"][0].update(type=[]),
                   lambda g: g["nodes"][4].update(resolution=[]),
                   lambda g: g["edges"][0].update(source=g["nodes"][0]["id"])):
        graph = copy.deepcopy(original)
        mutate(graph)
        save(path, graph)
        assert exit_code(run(path)) == 1


def test_eg04_dangling_edge_and_typed_references(tmp_path):
    path, original, n = fixture(tmp_path)
    for location in ("edge", "protocol", "source"):
        graph = copy.deepcopy(original)
        if location == "edge":
            graph["edges"][0]["target"] = "missing"
        elif location == "protocol":
            graph["nodes"][2]["protocol_ref"] = "missing"
        else:
            graph["nodes"][3]["source_refs"] = ["missing"]
        save(path, graph)
        assert "DANGLING_REFERENCE" in codes(run(path))


def test_eg05_unsafe_paths_before_artifact_open(tmp_path, monkeypatch):
    path, graph, n = fixture(tmp_path)
    original = fs.Root.read
    def guarded(self, rel, *args, **kwargs):
        assert rel == "graph.json"
        return original(self, rel, *args, **kwargs)
    monkeypatch.setattr(fs.Root, "read", guarded)
    for unsafe in ("/etc/passwd", "../outside", "a/../b", "//server/share", "C:/drive", "a\\b", "a\x00b"):
        n["artifact"]["path"] = unsafe
        save(path, graph)
        assert "UNSAFE_PATH" in codes(run(path, "doctor"))


def test_eg06_symlinks_and_parent_swap_no_external_reads(tmp_path, monkeypatch):
    outside = tmp_path / "outside"
    outside.mkdir()
    secret = outside / "artifact.txt"
    secret.write_bytes(b"never read this target")
    for internal in (True, False):
        root = tmp_path / str(internal)
        path, graph, n = fixture(root)
        (root / "link").symlink_to(root / "artifact.txt" if internal else secret)
        n["artifact"]["path"] = "link"
        save(path, graph)
        assert exit_code(run(path, "doctor")) == 1
    root = tmp_path / "race"
    path, graph, n = fixture(root)
    (root / "nested").mkdir()
    (root / "artifact.txt").rename(root / "nested/artifact.txt")
    n["artifact"]["path"] = "nested/artifact.txt"
    save(path, graph)
    original_anchor, original_read = fs.Root.anchored, fs.os.read
    read_inodes = []
    def anchored(self, rel, fd):
        if rel == "nested/artifact.txt" and (root / "nested").is_dir() and not (root / "nested").is_symlink():
            (root / "nested").rename(root / "moved")
            (root / "nested").symlink_to(outside, target_is_directory=True)
        return original_anchor(self, rel, fd)
    def read(fd, count):
        read_inodes.append(os.fstat(fd).st_ino)
        return original_read(fd, count)
    monkeypatch.setattr(fs.Root, "anchored", anchored)
    monkeypatch.setattr(fs.os, "read", read)
    assert exit_code(run(path, "doctor")) == 1
    assert secret.stat().st_ino not in read_inodes


def test_eg07_missing_artifact_is_unresolved(tmp_path):
    path, graph, n = fixture(tmp_path)
    (tmp_path / "artifact.txt").unlink()
    result = run(path, "doctor")
    assert "MISSING" in codes(result) and exit_code(result) == 2


def test_eg08_unreadable_is_not_empty_hash(tmp_path):
    path, graph, n = fixture(tmp_path)
    artifact = tmp_path / "artifact.txt"
    artifact.chmod(0)
    try:
        report = run(path, "doctor")
        assert "UNREADABLE" in codes(report)
        assert "sha256" not in report["artifact_observations"][0]
    finally:
        artifact.chmod(0o600)


def test_eg09_dataless_never_opened(tmp_path, monkeypatch):
    path, graph, n = fixture(tmp_path)
    original_stat, original_open = fs.os.stat, fs.os.open
    class Dataless:
        def __init__(self, value):
            self.value = value
            self.st_flags = getattr(value, "st_flags", 0) | fs.DATALESS
        def __getattr__(self, name):
            return getattr(self.value, name)
    def stat_call(name, *args, **kwargs):
        s = original_stat(name, *args, **kwargs)
        return Dataless(s) if str(name) == "artifact.txt" else s
    def open_call(name, *args, **kwargs):
        assert str(name) != "artifact.txt"
        return original_open(name, *args, **kwargs)
    monkeypatch.setattr(fs.os, "stat", stat_call)
    monkeypatch.setattr(fs.os, "open", open_call)
    assert "NOT_LOCAL" in codes(run(path, "doctor"))


def test_eg10_identity_mismatch_and_read_race(tmp_path, monkeypatch):
    path, graph, n = fixture(tmp_path)
    artifact = tmp_path / "artifact.txt"
    original_bytes = artifact.read_bytes()
    artifact.write_bytes(b"changed bytes under the same version")
    assert "IDENTITY_MISMATCH" in codes(run(path, "doctor"))
    artifact.write_bytes(original_bytes)
    original_read = fs.os.read
    inode = artifact.stat().st_ino
    changed = False
    def read(fd, count):
        nonlocal changed
        data = original_read(fd, count)
        if os.fstat(fd).st_ino == inode and not changed:
            changed = True
            with artifact.open("ab") as stream:
                stream.write(b" concurrent change")
        return data
    monkeypatch.setattr(fs.os, "read", read)
    assert "VERSION_DRIFT" in codes(run(path, "doctor"))


def test_eg11_multiple_current_heads_are_unresolved(tmp_path):
    path, graph, n = fixture(tmp_path)
    newer = dict(n["evidence"], version="2", id=n["evidence"]["logical_id"] + "@2")
    graph["nodes"].append(newer)
    save(path, graph)
    assert "VERSION_FORK_UNRESOLVED" in codes(run(path, "doctor"))


def test_eg12_historical_supersession_preserves_citation(tmp_path):
    path, graph, n = fixture(tmp_path)
    newer = dict(n["evidence"], version="2", id=n["evidence"]["logical_id"] + "@2")
    graph["nodes"].append(newer)
    graph["edges"].append(edge("SUPERSEDES", newer, n["evidence"], "newer"))
    save(path, graph)
    assert "STALE_CURRENT_REFERENCE" in codes(run(path, "doctor"))
    graph["edges"][0]["citation_context"] = "historical"
    save(path, graph)
    report = run(path, "trace", claim=n["claim"]["id"])
    assert "SUPERSEDED_HISTORICAL_CITATION" in codes(report)
    assert "STALE_CURRENT_REFERENCE" not in codes(report)
    assert n["evidence"]["id"] in {x["id"] for x in report["nodes_visited"]}


def test_eg13_invalid_supersession_and_cycles(tmp_path):
    path, original, n = fixture(tmp_path)
    for variant in ("type", "logical", "cycle"):
        graph = copy.deepcopy(original)
        if variant == "type":
            graph["edges"].append(edge("SUPERSEDES", n["protocol"], n["evidence"], "bad"))
        else:
            newer = dict(n["evidence"], version="2", id=n["evidence"]["logical_id"] + "@2")
            if variant == "logical":
                newer.update(logical_id="urn:rak:b1test:evidence:other", id="urn:rak:b1test:evidence:other@2")
            graph["nodes"].append(newer)
            graph["edges"].append(edge("SUPERSEDES", newer, n["evidence"], "supersede"))
            if variant == "cycle":
                graph["edges"].append(edge("SUPERSEDES", n["evidence"], newer, "cycle"))
        save(path, graph)
        assert exit_code(run(path)) == 1


def test_eg14_combined_dependency_cycle(tmp_path):
    path, graph, n = fixture(tmp_path)
    second = node("Evidence", "other", description="Another declared observation", source_refs=[])
    graph["nodes"].append(second)
    graph["edges"].extend([edge("DERIVED_FROM", n["evidence"], second, "dep-a"),
                           edge("DEPENDS_ON", second, n["evidence"], "dep-b")])
    save(path, graph)
    assert "DEPENDENCY_CYCLE" in codes(run(path))


def test_eg15_support_and_contradict_no_truth_inference(tmp_path):
    path, graph, n = fixture(tmp_path)
    graph["edges"].append(edge("CONTRADICTS", n["evidence"], n["claim"], "counter"))
    save(path, graph)
    result = run(path, "trace", claim=n["claim"]["id"])
    assert "SUPPORT_AND_CONTRADICTION_DECLARED" in codes(result)
    assert {x["type"] for x in result["edges_visited"]} >= {"SUPPORTS", "CONTRADICTS"}
    assert result["scope_limits"]["scientific_adjudication"] == "NOT_PERFORMED"


def test_eg16_reciprocal_contradiction_is_finite(tmp_path):
    path, graph, n = fixture(tmp_path)
    second = node("Claim", "opposite", statement="Opposing declaration", resolution="UNRESOLVED")
    graph["nodes"].append(second)
    graph["edges"].extend([edge("CONTRADICTS", n["claim"], second, "a-b"),
                           edge("CONTRADICTS", second, n["claim"], "b-a")])
    save(path, graph)
    report = run(path, "trace", claim=n["claim"]["id"])
    assert "DEPENDENCY_CYCLE" not in codes(report)
    assert len(report["nodes_visited"]) <= len(graph["nodes"])


def test_eg17_forged_mechanical_label_is_only_a_declaration(tmp_path):
    path, graph, n = fixture(tmp_path)
    n["artifact"]["assertion_level"] = "MECHANICALLY_VERIFIED"
    (tmp_path / "artifact.txt").unlink()
    save(path, graph)
    report = run(path, "doctor")
    assert "INPUT_VERIFICATION_LABEL_IS_DECLARATION" in codes(report)
    assert report["artifact_observations"][0]["status"] == "MISSING"


def test_eg18_external_adjudication_scope_is_explicit(tmp_path):
    path, graph, n = fixture(tmp_path)
    n["claim"].update(assertion_level="SCIENTIFICALLY_ADJUDICATED", external_adjudication={"identity": "external reviewer"})
    save(path, graph)
    assert "EXTERNAL_ADJUDICATION_INCOMPLETE" in codes(run(path, "doctor"))
    n["claim"]["external_adjudication"].update(method="supplied review", scope="declared scope", record_ref=n["artifact"]["id"])
    save(path, graph)
    report = run(path, "doctor")
    assert "EXTERNAL_ADJUDICATION_RECORDED_NOT_VALIDATED" in codes(report)
    assert report["scope_limits"]["scientific_adjudication"] == "NOT_PERFORMED"
    for bad in (None, [], {"identity": []}, {"record_ref": 7}, {"scope": ""}):
        n["claim"]["external_adjudication"] = bad
        save(path, graph)
        assert "EXTERNAL_ADJUDICATION_FORMAT_INVALID" in codes(run(path))


def test_eg19_abstain_and_unresolved_preserved(tmp_path):
    path, graph, n = fixture(tmp_path)
    result = run(path, "doctor")
    assert {"EXPLICIT_ABSTAIN", "EXPLICIT_UNRESOLVED"} <= codes(result)
    decision = next(x for x in result["nodes_visited"] if x["type"] == "Decision")
    assert decision["outcome"] == "ABSTAIN" and decision["rationale"] == n["decision"]["rationale"]
    assert exit_code(result) == 2


def test_eg20_portable_order_and_result_digests(tmp_path):
    left, graph, n = fixture(tmp_path / "left")
    first = run(left, "doctor")
    right, _, _ = fixture(tmp_path / "right")
    graph["nodes"].reverse()
    graph["edges"].reverse()
    n["evidence"]["source_refs"].reverse()
    save(right, graph)
    second = run(right, "doctor")
    assert first == second


def test_eg21_budgets_malformed_nonfinite_and_deep_json(tmp_path):
    path, graph, n = fixture(tmp_path)
    assert exit_code(run(path, limits=replace(Limits(), nodes=1))) == 1
    assert "GRAPH_BUDGET_EXCEEDED" in codes(run(path, limits=replace(Limits(), graph_bytes=16)))
    for raw in ('{bad', '{"n":NaN}', '{"n":1e9999}', '[' * 100 + '0' + ']' * 100, '{"text":"\\ud800"}'):
        path.write_text(raw)
        assert exit_code(run(path)) == 1
    save(path, graph)
    assert exit_code(run(path, "doctor", limits=replace(Limits(), artifact_bytes=1))) == 2


def test_eg22_output_alias_escape_collision_and_atomic_report(tmp_path):
    root = tmp_path / "root"
    path, graph, n = fixture(root)
    before = {p.name: p.read_bytes() for p in root.iterdir()}
    (root / "hardlink").hardlink_to(root / "artifact.txt")
    (root / "symlink").symlink_to(tmp_path / "outside.json")
    for output in (path, root / "artifact.txt", root / "hardlink", root / "symlink", "../outside.json", tmp_path / "absolute.json"):
        assert exit_code(run(path, "doctor", output=output)) == 1
        for name, data in before.items():
            assert (root / name).read_bytes() == data
    (root / "hardlink").unlink()
    (root / "symlink").unlink()
    report = run(path, "doctor", output="report.json")
    assert json.loads((root / "report.json").read_text()) == report
    assert not list(root.glob(".rak-evidence-*.tmp"))
    assert exit_code(run(path, "doctor", output="report.json")) == 1


def test_eg23_existing_cli_and_audit_contract(tmp_path, capsys):
    parser = build_parser()
    choices = next(x for x in parser._actions if x.__class__.__name__ == "_SubParsersAction").choices
    assert {"audit", "freeze", "verify", "gate", "evidence"} <= set(choices)
    root = Path(__file__).parents[1]
    target = root / "examples/audit_demo/pass_repo"
    expected = (root / "examples/audit_demo/expected/pass.txt").read_text().rstrip()
    assert main(["audit", str(target)]) == 0
    assert capsys.readouterr().out.rstrip() == expected
    assert main(["audit", str(target), "--format", "json"]) == 0
    old = json.loads(capsys.readouterr().out)
    assert old["schema_version"] == "researchauditkit.audit/v1"
    path, graph, n = fixture(tmp_path)
    assert main(["evidence", "validate", str(path)]) == 0
    assert json.loads(capsys.readouterr().out)["schema"] == SCHEMA


def test_eg24_no_execution_network_or_source_writes(tmp_path, monkeypatch):
    path, graph, n = fixture(tmp_path)
    before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in tmp_path.iterdir()}
    def forbidden(*args, **kwargs):
        raise AssertionError("Execution or network is forbidden")
    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    original_open = fs.os.open
    def readonly(name, flags, *args, **kwargs):
        assert not flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)
        return original_open(name, flags, *args, **kwargs)
    monkeypatch.setattr(fs.os, "open", readonly)
    report = run(path, "doctor")
    assert report["artifact_observations"][0]["status"] == "MECHANICALLY_VERIFIED"
    assert {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in tmp_path.iterdir()} == before
    # Even a failed verification of the Darwin no-download guard must restore it.
    class Function:
        def __init__(self, callback):
            self.callback = callback
        def __call__(self, *args):
            return self.callback(*args)
    class Policy:
        def __init__(self):
            self.value = 0
            self.sets = []
            self.getiopolicy_np = Function(lambda *args: 0)
            self.setiopolicy_np = Function(self.set)
        def set(self, kind, scope, value):
            self.value = value
            self.sets.append(value)
            return 0
    policy = Policy()
    monkeypatch.setattr(fs.sys, "platform", "darwin")
    monkeypatch.setattr(fs.ctypes, "CDLL", lambda *a, **k: policy)
    with pytest.raises(fs.EvidenceError, match="NO_DOWNLOAD_GUARD_UNAVAILABLE"):
        with fs.no_download():
            raise AssertionError("A failed guard must not enter the read branch")
    assert policy.sets == [1, 0] and policy.value == 0


def test_eg25_explicitly_approved_real_receipt_demo():
    location = os.environ.get("RAK_EVIDENCE_APPROVED_DEMO_ROOT")
    if not location:
        pytest.skip("Requires a separately approved real local evidence scope; synthetic data is not a substitute")
    root = Path(location)
    approval = json.loads((root / "APPROVED_SCOPE.json").read_text())
    assert approval["authorized_scope"] == "V4.3 own execution receipts only"
    graph = root / "graph.json"
    originals = {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()}
    report = run(graph, "trace", claim=approval["claim_id"])
    assert report["artifact_observations"]
    assert all(x["status"] == "MECHANICALLY_VERIFIED" for x in report["artifact_observations"])
    assert {x["type"] for x in report["nodes_visited"]} >= {"Claim", "Evidence", "Artifact", "ExperimentRun", "Protocol"}
    assert report["scope_limits"]["scientific_adjudication"] == "NOT_PERFORMED"
    assert {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()} == originals
