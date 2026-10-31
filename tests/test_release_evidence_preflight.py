from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest
import yaml

from research_audit_kit import __version__
from research_audit_kit.evidence.fs import EvidenceError

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("release_preflight", ROOT / "tools/release_evidence_preflight.py")
preflight = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preflight)


def candidates(root):
    # Controlled fixture bytes exercise the gate, not package validity or real acceptance.
    for name in preflight.names(__version__).values():
        (root / name).write_bytes(b"Controlled identity fixture, not a release package.\n")
    return preflight.capture(root, __version__)["capture_receipt_sha256"]


def test_first_party_gate_preserves_claim_uncertainty(tmp_path):
    digest = candidates(tmp_path)
    result = preflight.check(tmp_path, __version__, digest)
    assert result["status"] == "PASS" and all(result["checks"].values())
    assert result["evidence_status"] == "UNRESOLVED" and result["claim_resolution"] == "UNRESOLVED"
    assert result["candidate_only"] and not result["publication_performed"]
    assert json.loads((tmp_path / "release-gate.json").read_text()) == result


@pytest.mark.parametrize("fault", ["bytes-changed", "missing", "graph-rewritten"])
def test_candidate_faults_fail_gate_without_rewriting_baseline(tmp_path, fault):
    digest = candidates(tmp_path)
    before = (tmp_path / "release-capture.json").read_bytes()
    wheel = tmp_path / preflight.names(__version__)["wheel"]
    if fault == "bytes-changed":
        wheel.write_bytes(b"changed")
    elif fault == "missing":
        wheel.unlink()
    else:
        graph = json.loads((tmp_path / "release-graph.json").read_text())
        next(node for node in graph["nodes"] if node["type"] == "Claim")["statement"] += " rewritten"
        (tmp_path / "release-graph.json").write_text(json.dumps(graph))
    result = preflight.check(tmp_path, __version__, digest)
    assert result["status"] == "FAIL"
    assert (tmp_path / "release-capture.json").read_bytes() == before
    if fault != "graph-rewritten":
        assert result["potentially_affected_claim_ids"] == [f"urn:rak:rak-release:claim:candidate@{__version__}"]


@pytest.mark.parametrize("fault", ["anchor", "manifest", "missing-anchor"])
def test_capture_anchor_and_manifest_identity_are_required(tmp_path, fault):
    digest = candidates(tmp_path)
    if fault == "anchor":
        (tmp_path / "release-capture.json").write_text('{}')
        expected = "CAPTURE_ANCHOR_MISMATCH"
    elif fault == "manifest":
        (tmp_path / "release-assets.json").write_text('{}')
        expected = "ASSET_LIST_CHANGED_AFTER_CAPTURE"
    else:
        digest = None
        expected = "CAPTURE_ANCHOR_REQUIRED"
    with pytest.raises(EvidenceError, match=expected):
        preflight.check(tmp_path, __version__, digest)
    assert not (tmp_path / "release-gate.json").exists()


def test_repeated_capture_never_rebaselines_existing_files(tmp_path):
    candidates(tmp_path)
    before = {name: (tmp_path / name).read_bytes() for name in ["release-assets.json", "release-graph.json", "release-capture.json"]}
    with pytest.raises(EvidenceError, match="OUTPUT_ALREADY_EXISTS"):
        preflight.capture(tmp_path, __version__)
    assert {name: (tmp_path / name).read_bytes() for name in before} == before


def test_missing_or_empty_package_cannot_create_a_pass_capture(tmp_path):
    for name in preflight.names(__version__).values():
        (tmp_path / name).touch()
    with pytest.raises(EvidenceError, match="CANDIDATE_CAPTURE_INCOMPLETE"):
        preflight.capture(tmp_path, __version__)
    assert not (tmp_path / "release-capture.json").exists()


def test_cli_invalid_input_fails_closed_without_traceback(tmp_path, capsys):
    assert preflight.main(["capture", "--root", str(tmp_path), "--version", "../other"]) == 1
    result = json.loads(capsys.readouterr().out)
    assert result["error"] == "PACKAGE_VERSION_MISMATCH" and not result["publication_performed"]
    assert list(tmp_path.iterdir()) == []


def test_release_workflow_captures_before_check_and_cannot_publish():
    text = (ROOT / ".github/workflows/release-evidence.yml").read_text()
    workflow = yaml.load(text, Loader=yaml.BaseLoader)
    assert workflow["permissions"] == {"contents": "read"}
    assert "pull_request_target" not in workflow["on"]
    steps = workflow["jobs"]["candidate-evidence"]["steps"]
    all_runs = "\n".join(step.get("run", "") for step in steps)
    assert all_runs.index("preflight.py capture") < all_runs.index("preflight.py check")
    assert "--capture-sha256" in all_runs and "--ignore-installed --no-index --no-deps" in all_runs
    assert "rak.__file__" in all_runs and "sys.prefix" in all_runs
    assert not any("upload" in step.get("uses", "") or "publish" in step.get("uses", "") for step in steps)
    assert "gh release" not in all_runs and "twine" not in all_runs


def test_real_built_wheel_runs_the_candidate_gate_from_its_installed_package(tmp_path):
    checkout = tmp_path / "checkout"
    shutil.copytree(ROOT, checkout, ignore=shutil.ignore_patterns(
        ".git", ".pytest_cache", "__pycache__", "build", "dist", "*.egg-info"))
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(checkout / "src")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PIP_NO_INDEX"] = "1"
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    def invoke(args, **kwargs):
        done = subprocess.run(args, env=env, capture_output=True, text=True, check=False,
                              timeout=120, **kwargs)
        assert done.returncode == 0, done.stdout + done.stderr
        return done
    invoke([sys.executable, "-m", "build", "--no-isolation", "--outdir", str(candidate), "."], cwd=checkout)
    script = checkout / "tools/release_evidence_preflight.py"
    captured = invoke([sys.executable, str(script), "capture", "--root", str(candidate), "--version", __version__])
    digest = json.loads(captured.stdout)["capture_receipt_sha256"]
    runtime = tmp_path / "runtime"
    invoke([sys.executable, "-m", "venv", "--system-site-packages", str(runtime)])
    python = runtime / "bin/python"
    invoke([str(python), "-m", "pip", "install", "--ignore-installed", "--no-index", "--no-deps",
            str(candidate / preflight.names(__version__)["wheel"])])
    invoke([str(python), "-I", "-c", "import pathlib,sys,research_audit_kit as r; assert pathlib.Path(r.__file__).resolve().is_relative_to(pathlib.Path(sys.prefix).resolve())"])
    checked = invoke([str(python), "-I", str(script), "check", "--root", str(candidate), "--version", __version__,
                      "--capture-sha256", digest])
    result = json.loads(checked.stdout)
    assert result["status"] == "PASS" and result["evidence_status"] == "UNRESOLVED"
    assert len(result["artifact_observations"]) == 2
