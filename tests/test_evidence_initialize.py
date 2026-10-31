from __future__ import annotations

import copy
from contextlib import contextmanager
from dataclasses import replace
import hashlib
import json
import os

import pytest

from research_audit_kit.cli import main
from research_audit_kit.evidence import Limits, exit_code, run
from research_audit_kit.evidence import fs
from research_audit_kit.evidence import initialize as module
from research_audit_kit.evidence.initialize import ASSET_LIST_SCHEMA, initialize


def setup_manifest(root, *, claims=True):
    (root / "record.txt").write_bytes(b"user-listed synthetic record\n")
    data = {"schema": ASSET_LIST_SCHEMA,
            "assets": [{"name": "record", "path": "record.txt", "media_type": "text/plain"}]}
    if claims:
        data["claims"] = [{"name": "main", "statement": "A user-written declaration.",
                           "supports": ["record"]}]
    path = root / "assets.json"
    path.write_text(json.dumps(data))
    return path, data


def codes(result):
    return {row["code"] for row in result["findings"]}


def test_init_captures_current_identity_and_only_user_declared_links(tmp_path):
    path, data = setup_manifest(tmp_path)
    result = initialize(path, output="graph.json")
    assert exit_code(result) == 0 and result["output_created"]
    assert result["generated_node_counts"] == {"Artifact": 1, "Evidence": 1, "Claim": 1}
    graph = json.loads((tmp_path / "graph.json").read_text())
    artifact = next(node for node in graph["nodes"] if node["type"] == "Artifact")
    claim = next(node for node in graph["nodes"] if node["type"] == "Claim")
    assert artifact["sha256"] == hashlib.sha256((tmp_path / "record.txt").read_bytes()).hexdigest()
    assert claim["statement"] == data["claims"][0]["statement"]
    assert claim["resolution"] == "UNRESOLVED"
    assert all(node["assertion_level"] == "DECLARED" for node in graph["nodes"])
    assert [edge["type"] for edge in graph["edges"]] == ["SUPPORTS"]
    assert result["artifact_observations"][0]["status"] == "IDENTITY_CAPTURED"
    assert run(tmp_path / "graph.json")["status"] == "PASS"
    doctor = run(tmp_path / "graph.json", "doctor")
    assert doctor["status"] == "UNRESOLVED"
    assert doctor["artifact_observations"][0]["status"] == "MECHANICALLY_VERIFIED"


def test_no_claim_or_unlisted_relationship_is_inferred(tmp_path):
    path, data = setup_manifest(tmp_path, claims=False)
    assert initialize(path, output="first.json")["status"] == "PASS"
    graph = json.loads((tmp_path / "first.json").read_text())
    assert {node["type"] for node in graph["nodes"]} == {"Artifact", "Evidence"}
    assert graph["edges"] == []
    data["claims"] = [{"name": "unlinked", "statement": "Explicit but not linked"}]
    path.write_text(json.dumps(data))
    initialize(path, output="second.json")
    graph = json.loads((tmp_path / "second.json").read_text())
    assert graph["edges"] == []
    assert "CLAIM_EVIDENCE_CHAIN_MISSING" in codes(run(tmp_path / "second.json", "doctor"))


def test_missing_asset_stays_unresolved_in_generated_graph_and_impact(tmp_path):
    path, _ = setup_manifest(tmp_path)
    (tmp_path / "record.txt").unlink()
    result = initialize(path, output="graph.json")
    assert exit_code(result) == 2 and result["output_created"]
    graph = json.loads((tmp_path / "graph.json").read_text())
    artifact = next(node for node in graph["nodes"] if node["type"] == "Artifact")
    assert "sha256" not in artifact and artifact["unresolved_reason"] == "MISSING"
    impact = run(tmp_path / "graph.json", "impact")["impact_analysis"]
    assert impact["potentially_affected_claim_ids"] == ["urn:rak:project:claim:main@1"]


def test_manifest_order_does_not_change_graph_bytes(tmp_path):
    path, data = setup_manifest(tmp_path)
    data["assets"].append({"name": "other", "path": "other.txt"})
    (tmp_path / "other.txt").write_bytes(b"other")
    data["claims"][0]["contradicts"] = ["other"]
    path.write_text(json.dumps(data))
    first = initialize(path, output="first.json", namespace="sample", version="2")
    data["assets"].reverse()
    path.write_text(json.dumps(data))
    second = initialize(path, output="second.json", namespace="sample", version="2")
    assert first["graph_content_sha256"] == second["graph_content_sha256"]
    assert (tmp_path / "first.json").read_bytes() == (tmp_path / "second.json").read_bytes()


@pytest.mark.parametrize("mutation", [
    lambda m: m.update(unexpected=True),
    lambda m: m["assets"][0].update(path="../secret"),
    lambda m: m["assets"][0].update(path="a/../secret"),
    lambda m: m["assets"][0].update(name=[]),
    lambda m: m["assets"][0].update(media_type=[]),
    lambda m: m["assets"].append(copy.deepcopy(m["assets"][0])),
    lambda m: m["claims"][0].update(supports=["unknown"]),
    lambda m: m["claims"][0].update(supports=[[]]),
    lambda m: m["claims"][0].update(supports=["record", "record"]),
    lambda m: m["claims"][0].update(assertion_level="SCIENTIFICALLY_ADJUDICATED"),
])
def test_invalid_declarations_rejected_before_asset_reads(tmp_path, monkeypatch, mutation):
    path, data = setup_manifest(tmp_path)
    mutation(data)
    path.write_text(json.dumps(data))
    read = fs.Root.read
    def manifest_only(self, relative, *args, **kwargs):
        assert relative == "assets.json"
        return read(self, relative, *args, **kwargs)
    monkeypatch.setattr(fs.Root, "read", manifest_only)
    assert initialize(path, output="graph.json")["status"] == "INVALID"
    assert not (tmp_path / "graph.json").exists()


@pytest.mark.parametrize("settings", [
    {"namespace": "../outside"}, {"version": "latest"},
    {"limits": replace(Limits(), total_artifact_bytes=False)},
    {"limits": replace(Limits(), total_artifact_bytes="bad")},
    {"limits": replace(Limits(), nodes=1)},
])
def test_invalid_identity_or_budget_does_not_publish(tmp_path, settings):
    path, _ = setup_manifest(tmp_path)
    assert initialize(path, output="graph.json", **settings)["status"] == "INVALID"
    assert not (tmp_path / "graph.json").exists()


@pytest.mark.parametrize("output", ["assets.json", "record.txt", "../outside.json", "existing.json"])
def test_output_alias_escape_and_collision_preserve_inputs(tmp_path, output):
    path, _ = setup_manifest(tmp_path)
    (tmp_path / "existing.json").write_bytes(b"preserve")
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    assert initialize(path, output=output)["status"] == "INVALID"
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == before


@pytest.mark.parametrize("kind", ["symlink", "hardlink", "fifo"])
def test_nonregular_or_linked_asset_is_not_opened_or_published(tmp_path, kind):
    path, _ = setup_manifest(tmp_path)
    asset = tmp_path / "record.txt"
    asset.unlink()
    if kind == "fifo":
        os.mkfifo(asset)
    else:
        other = tmp_path / "other.txt"
        other.write_bytes(b"never reuse as a linked input")
        if kind == "symlink":
            asset.symlink_to(other)
        else:
            asset.hardlink_to(other)
    result = initialize(path, output="graph.json")
    assert result["status"] == "INVALID"
    assert not result["output_created"] and not (tmp_path / "graph.json").exists()


def test_unresolved_read_budget_produces_explicit_partial_identities(tmp_path):
    path, data = setup_manifest(tmp_path)
    data["assets"].append({"name": "z", "path": "z.txt"})
    (tmp_path / "z.txt").write_bytes(b"z")
    path.write_text(json.dumps(data))
    size = (tmp_path / "record.txt").stat().st_size
    result = initialize(path, output="graph.json", limits=replace(Limits(), total_artifact_bytes=size))
    assert result["status"] == "UNRESOLVED" and result["output_created"]
    assert result["scope_limits"]["artifact_bytes_read"] == size
    assert "TOTAL_ARTIFACT_BUDGET_EXCEEDED" in codes(result)


def test_generated_graph_must_fit_the_readable_graph_budget(tmp_path):
    path, _ = setup_manifest(tmp_path, claims=False)
    result = initialize(path, output="graph.json", limits=replace(Limits(), graph_bytes=400))
    assert "GENERATED_GRAPH_BUDGET_EXCEEDED" in codes(result)
    assert not (tmp_path / "graph.json").exists()


def test_duplicate_json_keys_are_rejected(tmp_path):
    path = tmp_path / "assets.json"
    path.write_text('{"schema":"first", "schema":"second"}')
    assert "DUPLICATE_JSON_KEY" in codes(initialize(path, output="graph.json"))


def test_guard_covers_reads_and_restores_before_publish(tmp_path, monkeypatch):
    path, _ = setup_manifest(tmp_path)
    active = False
    original_read, original_publish = fs.Root.read, fs.Root.publish
    @contextmanager
    def guard():
        nonlocal active
        active = True
        try:
            yield
        finally:
            active = False
    def read(*args, **kwargs):
        assert active
        return original_read(*args, **kwargs)
    def publish(*args, **kwargs):
        assert not active
        return original_publish(*args, **kwargs)
    monkeypatch.setattr(module, "no_download", guard)
    monkeypatch.setattr(fs.Root, "read", read)
    monkeypatch.setattr(fs.Root, "publish", publish)
    assert initialize(path, output="graph.json")["output_created"]


def test_guard_restore_failure_cannot_publish_success(tmp_path, monkeypatch):
    path, _ = setup_manifest(tmp_path)
    @contextmanager
    def guard():
        yield
        raise fs.EvidenceError("NO_DOWNLOAD_RESTORE_FAILED", "UNRESOLVED")
    monkeypatch.setattr(module, "no_download", guard)
    result = initialize(path, output="graph.json")
    assert result["status"] == "UNRESOLVED" and not result["output_created"]
    assert not (tmp_path / "graph.json").exists()


def test_cli_initialization_has_human_default_and_explicit_json(tmp_path, capsys):
    path, _ = setup_manifest(tmp_path)
    assert main(["evidence", "init", "--manifest", str(path), "--out", "graph.json"]) == 0
    human = capsys.readouterr().out
    assert "Graph: graph.json (created)" in human and "claims remain UNRESOLVED" in human
    assert main(["evidence", "init", "--manifest", str(path), "--out", "other.json", "--format", "json"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["schema"] == "researchauditkit.evidence-init/v1" and result["output_created"]
