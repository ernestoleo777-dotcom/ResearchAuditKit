from __future__ import annotations

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
    assert "support-audit" in result.stdout


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

