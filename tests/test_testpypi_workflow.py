from __future__ import annotations

import subprocess
from pathlib import Path

import yaml


ROOT = Path(__file__).parents[1]
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "publish-testpypi.yml"

EXPECTED = {
    "EXPECTED_REPOSITORY": "ernestoleo777-dotcom/ResearchAuditKit",
    "EXPECTED_TAG": "v0.1.0-rc.1",
    "EXPECTED_COMMIT": "9ae2bfeead9cbf4c6779011b601666ffc0cff833",
    "EXPECTED_WHEEL": "research_audit_kit-0.1.0rc1-py3-none-any.whl",
    "EXPECTED_WHEEL_SHA256": "b5120bb0e4777baecfcff21eabba87953b7859ba65141e380fe067096b04455a",
    "EXPECTED_SDIST": "research_audit_kit-0.1.0rc1.tar.gz",
    "EXPECTED_SDIST_SHA256": "d5c2b9dc63d0f76db1006032a2eb3dfac8a80139370c90f2aae6a56bf9663e10",
    "EXPECTED_VERSION": "0.1.0rc1",
    "EXPECTED_DISTRIBUTION": "research-audit-kit",
}


def _workflow() -> tuple[dict[str, object], str]:
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    data = yaml.load(text, Loader=yaml.BaseLoader)
    assert isinstance(data, dict)
    return data, text


def _steps(workflow: dict[str, object]) -> list[dict[str, object]]:
    jobs = workflow["jobs"]
    assert isinstance(jobs, dict)
    publish = jobs["publish-audited-rc"]
    assert isinstance(publish, dict)
    steps = publish["steps"]
    assert isinstance(steps, list)
    return steps


def test_testpypi_workflow_has_only_manual_dispatch_and_minimal_permissions():
    workflow, _ = _workflow()
    assert set(workflow["on"]) == {"workflow_dispatch"}
    assert workflow["on"]["workflow_dispatch"] == ""
    assert workflow["permissions"] == {"contents": "read", "id-token": "write"}

    jobs = workflow["jobs"]
    assert isinstance(jobs, dict)
    publish = jobs["publish-audited-rc"]
    assert isinstance(publish, dict)
    assert publish["runs-on"] == "ubuntu-latest"
    assert publish["environment"] == "testpypi"


def test_testpypi_workflow_fixes_and_verifies_rc1_provenance():
    workflow, text = _workflow()
    jobs = workflow["jobs"]
    assert isinstance(jobs, dict)
    publish = jobs["publish-audited-rc"]
    assert isinstance(publish, dict)
    assert publish["env"] == EXPECTED

    commands = "\n".join(str(step.get("run", "")) for step in _steps(workflow))
    for required in (
        "isPrerelease",
        "isDraft",
        "len(assets) == 3",
        "git/ref/tags",
        "git/tags/$tag_object_sha",
        "tag[\"object\"][\"sha\"] == \"9ae2bfeead9cbf4c6779011b601666ffc0cff833\"",
        "sha256sum -c SHA256SUMS",
        "assert len(checksum_lines) == 2",
        "test \"$(find dist -maxdepth 1 -type f | wc -l)\" = 2",
        "License-Expression",
        "rak = research_audit_kit.cli:main",
    ):
        assert required in commands
    assert "pypa/gh-action-pypi-publish@release/v1" in text
    assert "repository-url: https://test.pypi.org/legacy/" in text
    assert "packages-dir: dist/" in text


def test_testpypi_workflow_rejects_unsafe_publish_patterns_and_shell_is_valid():
    workflow, text = _workflow()
    forbidden = (
        "push:",
        "pull_request:",
        "pull_request_target",
        "release:",
        "schedule:",
        "workflow_run",
        "repository_dispatch",
        "secrets.",
        "TWINE_USERNAME",
        "TWINE_PASSWORD",
        "skip-existing",
        "continue-on-error",
        "contents: write",
        "packages: write",
        "actions: write",
        "python -m build",
        "pip wheel",
        "setup.py",
        "curl | bash",
        "eval ",
    )
    assert not [pattern for pattern in forbidden if pattern in text]
    assert "GH_TOKEN: ${{ github.token }}" in text
    assert "workflow_dispatch:\n    inputs:" not in text

    for step in _steps(workflow):
        script = step.get("run")
        if script:
            result = subprocess.run(
                ["bash", "-n"], input=str(script), text=True, capture_output=True, check=False
            )
            assert result.returncode == 0, result.stderr
