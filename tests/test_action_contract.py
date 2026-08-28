from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
import yaml

from research_audit_kit.integrity.audit import audit_repository


ROOT = Path(__file__).parents[1]
DEMO = ROOT / "examples" / "audit_demo"


def _run_action(tmp_path: Path, fixture: str, *, fail_on: str = "release-blocker"):
    runtime_dir = tmp_path / f"{fixture}-runtime"
    runtime_dir.mkdir()
    result_file = runtime_dir / "audit-result.json"
    summary = tmp_path / "summary.md"
    outputs = tmp_path / "outputs.txt"
    env = os.environ.copy()
    env.update(
        {
            "GITHUB_WORKSPACE": str(ROOT),
            "GITHUB_OUTPUT": str(outputs),
            "GITHUB_STEP_SUMMARY": str(summary),
            "RAK_ACTION_ROOT": str(ROOT),
            "RAK_ACTION_RUNTIME_DIR": str(runtime_dir),
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
    assert set(action["outputs"]) == {"status", "result-file", "exit-code"}
    assert len(action["runs"]["steps"]) == 3
    setup = action["runs"]["steps"][0]
    assert setup["uses"] == (
        "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1"
    )
    assert setup["with"]["python-version"] == "3.12.14"
    assert "GITHUB_TOKEN" not in action_text
    assert "secrets." not in action_text
    assert "curl " not in action_text
    assert "wget " not in action_text
    assert "github.action_path" in action_text


def test_action_bootstrap_is_hash_locked_and_runner_temporary():
    bootstrap = (ROOT / "action" / "bootstrap.sh").read_text(encoding="utf-8")
    lock = (ROOT / "action" / "requirements.lock").read_text(encoding="utf-8")
    runner = (ROOT / "action" / "runner.py").read_text(encoding="utf-8")
    entrypoint = (ROOT / "action" / "run-audit.sh").read_text(encoding="utf-8")

    assert "RUNNER_TEMP" in bootstrap
    assert "mktemp -d" in bootstrap
    assert "--require-hashes" in bootstrap
    assert "--only-binary=:all:" in bootstrap
    assert "--no-deps" in bootstrap
    assert "--no-cache-dir" in bootstrap
    assert 'TMPDIR="$runtime_dir/tmp"' in bootstrap
    assert "PyYAML==6.0.3" in lock
    assert lock.count("--hash=sha256:") == 10
    assert "ACTION_ROOT = Path(__file__).resolve().parents[1]" in runner
    assert 'sys.path.insert(0, str(ACTION_SOURCE))' in runner
    assert "PYTHONPATH" not in bootstrap + runner + entrypoint
    assert ' -I "$RAK_ACTION_ROOT/action/runner.py"' in entrypoint
    assert "pip install" not in entrypoint


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
    assert f"exit-code={expected_code}" in output_text


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

    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    result_file = runtime_dir / "audit-result.json"
    env = os.environ.copy()
    env.update(
        {
            "GITHUB_WORKSPACE": str(target),
            "RAK_ACTION_ROOT": str(ROOT),
            "RAK_ACTION_RUNTIME_DIR": str(runtime_dir),
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


def test_action_isolated_mode_blocks_shadow_modules_and_target_execution(tmp_path: Path):
    target = tmp_path / "target repository ; quoted"
    target.mkdir()
    (target / "README.md").write_text("# Target\n", encoding="utf-8")
    (target / "LICENSE").write_text("Test license\n", encoding="utf-8")
    canary = tmp_path / "target-code-executed"
    payload = (
        "from pathlib import Path\n"
        f"Path({str(canary)!r}).write_text('executed', encoding='utf-8')\n"
        "raise RuntimeError('target code executed')\n"
    )
    for relative in (
        "research_audit_kit/__init__.py",
        "yaml/__init__.py",
        "sitecustomize.py",
        "usercustomize.py",
        "json.py",
        "setup.py",
        "canary_backend.py",
        "analysis.py",
    ):
        path = target / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding="utf-8")
    (target / "pyproject.toml").write_text(
        '[build-system]\nrequires = []\nbuild-backend = "canary_backend"\n',
        encoding="utf-8",
    )

    runtime_dir = tmp_path / "runtime with spaces"
    runtime_dir.mkdir()
    result_file = runtime_dir / "audit-result.json"
    env = os.environ.copy()
    env.update(
        {
            "GITHUB_WORKSPACE": str(target),
            "RAK_ACTION_ROOT": str(ROOT),
            "RAK_ACTION_RUNTIME_DIR": str(runtime_dir),
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
    assert not canary.exists()


def test_action_invalid_policy_abstains_without_disclosing_raw_path(tmp_path: Path):
    raw = "../outside-secret.txt"
    target = tmp_path / "invalid policy target"
    policy = target / ".rak" / "policy.yaml"
    policy.parent.mkdir(parents=True)
    (target / "README.md").write_text("# Target\n", encoding="utf-8")
    (target / "LICENSE").write_text("Test license\n", encoding="utf-8")
    policy.write_text(
        yaml.safe_dump({"policy": {"id": "unsafe", "required_files": [raw]}}),
        encoding="utf-8",
    )
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    summary = tmp_path / "summary.md"
    outputs = tmp_path / "outputs.txt"
    env = os.environ.copy()
    env.update(
        {
            "GITHUB_OUTPUT": str(outputs),
            "GITHUB_STEP_SUMMARY": str(summary),
            "GITHUB_WORKSPACE": str(target),
            "RAK_ACTION_ROOT": str(ROOT),
            "RAK_ACTION_RUNTIME_DIR": str(runtime_dir),
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

    emitted = "".join(
        (
            completed.stdout,
            completed.stderr,
            (runtime_dir / "audit-result.json").read_text(encoding="utf-8"),
            summary.read_text(encoding="utf-8"),
            outputs.read_text(encoding="utf-8"),
        )
    )
    assert completed.returncode == 2
    assert "status=ABSTAIN" in emitted
    assert "exit-code=2" in emitted
    assert "PARENT_TRAVERSAL" in emitted
    assert raw not in emitted


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


def test_summary_renderer_cannot_disclose_an_invalid_required_path(tmp_path: Path):
    raw = "../../outside.txt"
    target = tmp_path / "target"
    policy_path = target / ".rak" / "policy.yaml"
    policy_path.parent.mkdir(parents=True)
    (target / "README.md").write_text("# Target\n", encoding="utf-8")
    policy_path.write_text(
        yaml.safe_dump(
            {"policy": {"id": "unsafe", "required_files": [raw]}}, sort_keys=True
        ),
        encoding="utf-8",
    )
    namespace: dict[str, object] = {}
    exec((ROOT / "action" / "render-summary.py").read_text(encoding="utf-8"), namespace)

    rendered = namespace["render"](audit_repository(target))

    assert raw not in rendered
    assert "PARENT_TRAVERSAL" in rendered
    assert "policy.required_files[0]" in rendered
