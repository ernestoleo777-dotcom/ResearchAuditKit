from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).parents[1]


def test_action_end_to_end_workflow_executes_local_action_without_prerequisites():
    workflow_path = ROOT / ".github" / "workflows" / "action-e2e.yml"
    workflow_text = workflow_path.read_text(encoding="utf-8")
    workflow = yaml.load(workflow_text, Loader=yaml.BaseLoader)
    assert workflow["permissions"] == {"contents": "read"}
    assert set(workflow["on"]) == {"pull_request"}
    steps = workflow["jobs"]["action-e2e"]["steps"]
    assert sum(step.get("uses") == "./" for step in steps) == 8
    assert not [
        step
        for step in steps
        if str(step.get("uses", "")).startswith("actions/setup-python@")
    ]
    assert "pip install" not in workflow_text
    assert "secrets." not in workflow_text
    assert "actions/upload-artifact" not in workflow_text
    assert "actions/cache" not in workflow_text
    assert "pull_request_target" not in workflow_text
    for required_case in (
        "Default-policy PASS",
        "Explicit-policy PASS",
        "WARNING below default",
        "WARNING at strict",
        "Configured RELEASE_BLOCKER",
        "Invalid policy ABSTAIN",
        "Escaping required-file symlink ABSTAIN",
        "Repeat canonical JSON",
        "sitecustomize.py",
        "research_audit_kit/__init__.py",
        "yaml/__init__.py",
        "pyproject.toml",
        "target-code-executed",
    ):
        assert required_case in workflow_text
