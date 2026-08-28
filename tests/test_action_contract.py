from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
import yaml


ROOT = Path(__file__).parents[1]
DEMO = ROOT / "examples" / "audit_demo"


def _run_action(tmp_path: Path, fixture: str, *, fail_on: str = "release-blocker"):
    result_file = tmp_path / f"{fixture}.json"
    summary = tmp_path / "summary.md"
    outputs = tmp_path / "outputs.txt"
    env = os.environ.copy()
    env.update(
        {
            "GITHUB_WORKSPACE": str(ROOT),
            "GITHUB_OUTPUT": str(outputs),
            "GITHUB_STEP_SUMMARY": str(summary),
            "RAK_ACTION_RESULT_FILE": str(result_file),
            "RAK_ACTION_ROOT": str(ROOT),
            "RAK_INPUT_FAIL_ON": fail_on,
            "RAK_INPUT_FORMAT": "human",
            "RAK_INPUT_PATH": str(DEMO / fixture),
            "RAK_INPUT_POLICY": "",
            "RAK_PYTHON_COMMAND": sys.executable,
            "RUNNER_TEMP": str(tmp_path),
        }
    )
    completed = subprocess.run(
        ["bash", str(ROOT / "action" / "run-audit.sh")],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    return completed, result_file, summary, outputs


def test_composite_action_contract_is_local_and_minimal():
    action_text = (ROOT / "action.yml").read_text(encoding="utf-8")
    action = yaml.load(action_text, Loader=yaml.BaseLoader)
    assert action["runs"]["using"] == "composite"
    assert set(action["inputs"]) == {"path", "policy", "fail-on", "output-format"}
    assert set(action["outputs"]) == {"status", "result-file"}
    assert len(action["runs"]["steps"]) == 1
    assert "GITHUB_TOKEN" not in action_text
    assert "secrets." not in action_text
    assert "pip install" not in action_text
    assert "curl " not in action_text
    assert "wget " not in action_text


@pytest.mark.parametrize(
    ("fixture", "expected_code", "expected_status"),
    [
        ("pass_repo", 0, "PASS"),
        ("warning_repo", 0, "WARNING"),
        ("blocker_repo", 2, "RELEASE_BLOCKER"),
    ],
)
def test_action_replay_preserves_cli_status_and_writes_summary(
    tmp_path: Path, fixture: str, expected_code: int, expected_status: str
):
    completed, result_file, summary, outputs = _run_action(tmp_path, fixture)
    assert completed.returncode == expected_code, completed.stdout + completed.stderr
    result = json.loads(result_file.read_text(encoding="utf-8"))
    assert result["status"] == expected_status
    summary_text = summary.read_text(encoding="utf-8")
    assert "ResearchAuditKit audit" in summary_text
    assert f"**Status:** `{expected_status}`" in summary_text
    assert "not scientific correctness" in summary_text
    output_text = outputs.read_text(encoding="utf-8")
    assert f"status={expected_status}" in output_text
    assert f"result-file={result_file}" in output_text


def test_action_warning_threshold_is_preserved(tmp_path: Path):
    completed, result_file, _, _ = _run_action(tmp_path, "warning_repo", fail_on="warning")
    assert completed.returncode == 2
    assert json.loads(result_file.read_text(encoding="utf-8"))["status"] == "WARNING"


def test_action_does_not_import_a_target_shadow_package(tmp_path: Path):
    target = tmp_path / "target"
    shadow = target / "research_audit_kit"
    shadow.mkdir(parents=True)
    (target / "README.md").write_text("# Target\n", encoding="utf-8")
    (target / "LICENSE").write_text("Test license\n", encoding="utf-8")
    (shadow / "__init__.py").write_text(
        "raise RuntimeError('target package executed')\n", encoding="utf-8"
    )

    result_file = tmp_path / "result.json"
    env = os.environ.copy()
    env.update(
        {
            "GITHUB_WORKSPACE": str(target),
            "RAK_ACTION_RESULT_FILE": str(result_file),
            "RAK_ACTION_ROOT": str(ROOT),
            "RAK_INPUT_PATH": ".",
            "RAK_PYTHON_COMMAND": sys.executable,
            "RUNNER_TEMP": str(tmp_path),
        }
    )
    completed = subprocess.run(
        ["bash", str(ROOT / "action" / "run-audit.sh")],
        cwd=target,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert json.loads(result_file.read_text(encoding="utf-8"))["status"] == "PASS"


def test_summary_renderer_escapes_markdown_and_html():
    namespace: dict[str, object] = {}
    exec((ROOT / "action" / "render-summary.py").read_text(encoding="utf-8"), namespace)
    result = {
        "counts": {"PASS": 0, "WARNING": 1, "RELEASE_BLOCKER": 0, "NOT_APPLICABLE": 0, "UNRESOLVED": 0},
        "findings": [
            {
                "check_id": "x|y",
                "location": "<script>",
                "message": "line one\nline two",
                "status": "WARNING",
            }
        ],
        "policy": {"mode": "built-in", "policy_id": "policy"},
        "schema_version": "researchauditkit.audit/v1",
        "status": "WARNING",
        "target": {"root_identifier": "fixture"},
    }
    rendered = namespace["render"](result)
    assert "<script>" not in rendered
    assert "&lt;script&gt;" in rendered
    assert "x&#124;y" in rendered
    assert "line one line two" in rendered
