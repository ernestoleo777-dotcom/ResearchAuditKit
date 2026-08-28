from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]


def run_cli(*args):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    return subprocess.run(
        [sys.executable, "-m", "research_audit_kit.cli", *map(str, args)],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_cli_help():
    result = run_cli("--help")
    assert result.returncode == 0
    assert "Local-first release-engineering and integrity checks" in result.stdout
    assert "support-audit" in result.stdout
    assert "prediction-seal" in result.stdout
    assert "isolation-audit" in result.stdout
    assert "evidence-index" in result.stdout


def test_cli_phase1_custody_commands(tmp_path):
    declaration = {
        "declaration_id": "synthetic-cli",
        "declared_at": "2026-01-01T00:00:00Z",
        "predictions": [{"prediction_id": "p", "subject_ref": "subject", "prediction_value": "opaque", "producer_role": "author", "method_version": "v1"}],
    }
    declaration_path = tmp_path / "declaration.json"
    declaration_path.write_text(json.dumps(declaration))
    seal = tmp_path / "seal.json"
    other_file = tmp_path / "unrelated.txt"
    other_file.write_text("preserve this file\n")
    assert run_cli("prediction-seal", "--input", declaration_path, "--out", seal).returncode == 0
    original_sha256 = hashlib.sha256(seal.read_bytes()).hexdigest()
    collision = run_cli("prediction-seal", "--input", declaration_path, "--out", seal)
    assert collision.returncode != 0
    assert "prediction seal already exists" in json.loads(collision.stderr)["error"]
    assert "--force" in json.loads(collision.stderr)["error"]
    assert "Traceback" not in collision.stderr
    assert hashlib.sha256(seal.read_bytes()).hexdigest() == original_sha256
    assert other_file.read_text() == "preserve this file\n"
    declaration["predictions"][0]["prediction_value"] = "updated opaque value"
    declaration_path.write_text(json.dumps(declaration))
    assert run_cli("prediction-seal", "--input", declaration_path, "--out", seal, "--force").returncode == 0
    assert hashlib.sha256(seal.read_bytes()).hexdigest() != original_sha256
    assert other_file.read_text() == "preserve this file\n"
    verify = run_cli("prediction-verify", "--input", declaration_path, "--seal", seal, "--out", tmp_path / "verify")
    assert verify.returncode == 0
    assert json.loads((tmp_path / "verify" / "summary.json").read_text())["status"] == "PASS"

    root = tmp_path / "workspaces"
    (root / "one").mkdir(parents=True)
    (root / "two").mkdir()
    isolation_path = tmp_path / "isolation.json"
    isolation_path.write_text(json.dumps({"version": 1, "workspaces": [{"workspace_id": "one", "role": "author", "path": "one"}, {"workspace_id": "two", "role": "inspector", "path": "two"}]}))
    isolation = run_cli("isolation-audit", "--root", root, "--manifest", isolation_path, "--out", tmp_path / "isolation")
    assert isolation.returncode == 0
    assert (tmp_path / "isolation" / "isolation_audit.json").exists()

    roles = tmp_path / "roles.json"
    records = tmp_path / "records.json"
    roles.write_text(json.dumps({"roles": [{"role_id": "author", "role_label": "Author"}]}))
    records.write_text(json.dumps({"records": [{"evidence_id": "e", "role_id": "author", "evidence_kind": "note", "subject_ref": "subject", "recorded_at": "2026-01-01T00:00:00Z", "custody_status": "DECLARED"}]}))
    indexed = run_cli("evidence-index", "--roles", roles, "--records", records, "--out", tmp_path / "evidence")
    assert indexed.returncode == 0
    assert (tmp_path / "evidence" / "evidence_index.csv").exists()


def test_cli_prediction_verify_failure_is_machine_readable(tmp_path):
    declaration = {
        "declaration_id": "synthetic-cli",
        "declared_at": "2026-01-01T00:00:00Z",
        "predictions": [{"prediction_id": "p", "subject_ref": "subject", "prediction_value": "opaque", "producer_role": "author", "method_version": "v1"}],
    }
    source = tmp_path / "declaration.json"
    source.write_text(json.dumps(declaration))
    seal = tmp_path / "seal.json"
    run_cli("prediction-seal", "--input", source, "--out", seal)
    declaration["predictions"][0]["prediction_value"] = "changed"
    source.write_text(json.dumps(declaration))
    result = run_cli("prediction-verify", "--input", source, "--seal", seal, "--out", tmp_path / "verify")
    assert result.returncode == 2
    summary = json.loads((tmp_path / "verify" / "summary.json").read_text())
    assert summary["failure_codes"] == ["PREDICTION_VERIFY_DIGEST_MISMATCH"]


def test_cli_phase1_contract_errors_are_machine_readable(tmp_path):
    invalid_declaration = tmp_path / "invalid.json"
    invalid_declaration.write_text('{"declaration_id":"a","declaration_id":"b"}')
    prediction = run_cli("prediction-seal", "--input", invalid_declaration, "--out", tmp_path / "seal.json")
    assert prediction.returncode == 2
    assert "PREDICTION_SEAL_INVALID_INPUT" in json.loads(prediction.stderr)["error"]

    roles = tmp_path / "roles.json"
    records = tmp_path / "records.json"
    roles.write_text('{"roles":[],"roles":[]}')
    records.write_text('{"records":[]}')
    index = run_cli("evidence-index", "--roles", roles, "--records", records, "--out", tmp_path / "out")
    assert index.returncode == 2
    assert "EVIDENCE_INDEX_INVALID_ROLES" in json.loads(index.stderr)["error"]


def test_cli_custody_demo_files(tmp_path):
    demo = ROOT / "examples" / "custody_demo"
    seal = tmp_path / "custody-demo-seal.json"
    verify_dir = tmp_path / "custody-demo-verify"
    isolation_dir = tmp_path / "custody-demo-isolation"
    evidence_dir = tmp_path / "custody-demo-evidence"
    assert run_cli("prediction-seal", "--input", demo / "declaration.json", "--out", seal).returncode == 0
    assert run_cli("prediction-verify", "--input", demo / "declaration.json", "--seal", seal, "--out", verify_dir).returncode == 0
    assert run_cli("isolation-audit", "--root", demo / "workspaces", "--manifest", demo / "workspaces.json", "--out", isolation_dir).returncode == 0
    assert run_cli("evidence-index", "--roles", demo / "roles.json", "--records", demo / "records.json", "--out", evidence_dir).returncode == 0


def test_cli_argument_error_nonzero():
    assert run_cli("inventory").returncode != 0


def test_cli_inventory(tmp_path):
    result = run_cli("inventory", "--root", ROOT / "examples/integrity_demo", "--policy", ROOT / "configs/integrity_policy.example.yaml", "--out", tmp_path / "out")
    assert result.returncode == 0
    assert (tmp_path / "out/inventory.csv").exists()


def test_cli_freeze_and_verify(tmp_path):
    baseline = tmp_path / "baseline.csv"
    freeze = run_cli("freeze", "--root", ROOT / "examples/integrity_demo", "--policy", ROOT / "configs/integrity_policy.example.yaml", "--baseline", baseline)
    verify = run_cli("verify", "--root", ROOT / "examples/integrity_demo", "--baseline", baseline, "--out", tmp_path / "verify")
    assert freeze.returncode == verify.returncode == 0
    assert json.loads(verify.stdout)["gate_status"] == "PASS"


def test_cli_baseline_overwrite_nonzero(tmp_path):
    baseline = tmp_path / "baseline.csv"
    command = ("freeze", "--root", ROOT / "examples/integrity_demo", "--policy", ROOT / "configs/integrity_policy.example.yaml", "--baseline", baseline)
    assert run_cli(*command).returncode == 0
    assert run_cli(*command).returncode != 0


def test_cli_force_records_overwrite(tmp_path):
    baseline = tmp_path / "baseline.csv"
    command = ("freeze", "--root", ROOT / "examples/integrity_demo", "--policy", ROOT / "configs/integrity_policy.example.yaml", "--baseline", baseline)
    run_cli(*command)
    result = run_cli(*command, "--force")
    assert json.loads(result.stdout)["forced_overwrite"] is True


def test_cli_failed_gate_nonzero(tmp_path):
    metrics = tmp_path / "metrics.json"
    metrics.write_text('{"change_abs": 0.01}')
    result = run_cli("gate", "--metrics", metrics, "--policy", ROOT / "configs/gate_policy.example.yaml", "--out", tmp_path / "gate")
    assert result.returncode != 0


def test_cli_inconclusive_gate_is_not_failure(tmp_path):
    result = run_cli("gate", "--metrics", ROOT / "examples/gate_demo/metrics.json", "--policy", ROOT / "examples/gate_demo/policy.yaml", "--out", tmp_path / "gate")
    assert result.returncode == 0
    assert json.loads(result.stdout)["status"] == "INCONCLUSIVE"


def test_cli_support_audit(tmp_path):
    result = run_cli("support-audit", "--data", ROOT / "examples/conditional_support_demo/data.csv", "--features", "architecture,optimizer,momentum,depth", "--discrete", "architecture,optimizer,momentum,depth", "--schema", ROOT / "configs/support_schema.example.yaml", "--out", tmp_path / "support")
    assert result.returncode == 0
    assert (tmp_path / "support/support_summary.json").exists()


def test_cli_verify_detects_change(tmp_path):
    repo = tmp_path / "repo"
    shutil.copytree(ROOT / "examples/integrity_demo", repo)
    baseline = tmp_path / "baseline.csv"
    run_cli("freeze", "--root", repo, "--policy", ROOT / "configs/integrity_policy.example.yaml", "--baseline", baseline)
    (repo / "results.csv").write_text("record,value\nchanged,99\n")
    result = run_cli("verify", "--root", repo, "--baseline", baseline, "--out", tmp_path / "verify")
    assert result.returncode != 0


def test_cli_malformed_yaml_has_no_traceback(tmp_path):
    policy = tmp_path / "broken.yaml"
    policy.write_text("policy: [unterminated")
    result = run_cli("inventory", "--root", ROOT / "examples/integrity_demo", "--policy", policy, "--out", tmp_path / "out")
    assert result.returncode != 0
    assert "Traceback" not in result.stderr


def test_inventory_output_inside_root_does_not_self_pollute(tmp_path):
    repo = tmp_path / "repo"
    shutil.copytree(ROOT / "examples/integrity_demo", repo)
    out = repo / "generated-audit"
    command = ("inventory", "--root", repo, "--policy", ROOT / "configs/integrity_policy.example.yaml", "--out", out)
    assert run_cli(*command).returncode == 0
    first = (out / "inventory.csv").read_text()
    assert run_cli(*command).returncode == 0
    assert (out / "inventory.csv").read_text() == first
