from __future__ import annotations

import ast
import hashlib
import re
import subprocess
import sys
from pathlib import Path

from packaging.requirements import Requirement
import pytest
import yaml
from research_audit_kit import __version__

from _toml_compat import TOML_BACKEND, tomllib

ROOT = Path(__file__).parents[1]
CURRENT_RELEASE_VERSION = "0.1.0rc1"


def test_single_version_source():
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert "version" not in metadata["project"]
    assert metadata["tool"]["setuptools"]["dynamic"]["version"]["attr"].endswith(".__version__")
    assert __version__ == CURRENT_RELEASE_VERSION


def test_cli_version_matches_package():
    result = subprocess.run([sys.executable, "-m", "research_audit_kit.cli", "--version"], cwd=ROOT, env={"PYTHONPATH": str(ROOT / "src")}, text=True, capture_output=True, check=False)
    assert result.returncode == 0
    assert result.stdout.strip().endswith(__version__)


def test_release_candidate_documents_and_tag_mapping_are_consistent():
    citation = yaml.safe_load((ROOT / "CITATION.cff").read_text())
    assert citation["version"] == CURRENT_RELEASE_VERSION
    assert f"## {CURRENT_RELEASE_VERSION} — Release Candidate 1" in (ROOT / "CHANGELOG.md").read_text()
    assert "# ResearchAuditKit v0.1.0-rc.1" in (
        ROOT / "license_release" / "RELEASE_NOTES_DRAFT.md"
    ).read_text()

    match = re.fullmatch(r"(?P<base>\d+\.\d+\.\d+)rc(?P<number>\d+)", __version__)
    assert match is not None
    assert f"v{match['base']}-rc.{match['number']}" == "v0.1.0-rc.1"


def test_readme_current_wheel_example_uses_release_candidate_version():
    readme = (ROOT / "README.md").read_text()
    assert f"research_audit_kit-{CURRENT_RELEASE_VERSION}-py3-none-any.whl" in readme


def test_readme_declares_all_cli_commands():
    readme = (ROOT / "README.md").read_text()
    for command in ("init", "inventory", "freeze", "verify", "support-audit", "pareto-audit", "split-audit", "gate", "deviation record", "claims evaluate"):
        assert f"rak {command}" in readme


def test_package_source_has_no_network_imports():
    forbidden = {"requests", "httpx", "urllib.request", "socket", "aiohttp"}
    imported: set[str] = set()
    for path in (ROOT / "src").rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
    assert not imported & forbidden


def test_tracked_tree_has_no_forbidden_binary_assets():
    tracked = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines()
    forbidden_suffixes = {"." + "pkl", "." + "pickle", ".xlsx", ".xls", ".pdf"}
    assert not [path for path in tracked if Path(path).suffix.lower() in forbidden_suffixes]


def test_apache_license_text_and_metadata_are_consistent():
    license_bytes = (ROOT / "LICENSE").read_bytes()
    assert hashlib.sha256(license_bytes).hexdigest() == "c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4"
    assert license_bytes.endswith(b"\n")
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert metadata["project"]["license"] == "Apache-2.0"


def test_license_documents_are_consistent():
    assert "LICENSE_SELECTED_APACHE_2_0" in (ROOT / "LICENSE_STATUS.md").read_text()
    assert "Licensed under the Apache License, Version 2.0." in (ROOT / "README.md").read_text()
    citation = yaml.safe_load((ROOT / "CITATION.cff").read_text())
    assert citation["license"] == "Apache-2.0"
    notice = (ROOT / "license_release" / "NOTICE_DECISION.md").read_text()
    assert "NOTICE_NOT_REQUIRED_FOR_CURRENT_CONTENTS" in notice
    assert not (ROOT / "NOTICE").exists()


def test_package_source_has_one_apache_spdx_header_per_file():
    source_files = sorted((ROOT / "src" / "research_audit_kit").rglob("*.py"))
    assert len(source_files) == 43
    for path in source_files:
        assert path.read_text(encoding="utf-8").count("SPDX-License-Identifier: Apache-2.0") == 1


def test_toml_compatibility_interface_and_backend():
    assert callable(tomllib.load)
    assert callable(tomllib.loads)
    assert issubclass(tomllib.TOMLDecodeError, Exception)
    assert TOML_BACKEND == ("tomli" if sys.version_info < (3, 11) else "tomllib")


def test_toml_compatibility_parses_text_and_binary_file(tmp_path):
    content = '[project]\nname = "example"\nenabled = true\n'
    assert tomllib.loads(content)["project"] == {"name": "example", "enabled": True}
    path = tmp_path / "example.toml"
    path.write_bytes(content.encode("utf-8"))
    with path.open("rb") as handle:
        assert tomllib.load(handle)["project"]["name"] == "example"


def test_toml_compatibility_rejects_invalid_toml():
    with pytest.raises(tomllib.TOMLDecodeError):
        tomllib.loads("[project\nname = 'example'")


def test_tomli_is_conditional_dev_dependency_only():
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text())
    dev_requirements = [Requirement(item) for item in metadata["project"]["optional-dependencies"]["dev"]]
    tomli = [requirement for requirement in dev_requirements if requirement.name == "tomli"]
    assert len(tomli) == 1
    assert tomli[0].marker is not None
    assert tomli[0].marker.evaluate({"python_version": "3.10"})
    assert not tomli[0].marker.evaluate({"python_version": "3.11"})
    assert all(Requirement(item).name != "tomli" for item in metadata["project"]["dependencies"])


def test_python_support_and_ci_dev_install_are_preserved():
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert metadata["project"]["requires-python"] == ">=3.10"
    workflow = yaml.safe_load((ROOT / ".github" / "workflows" / "ci.yml").read_text())
    assert workflow["jobs"]["test"]["strategy"]["matrix"]["python-version"] == ["3.10", "3.11", "3.12"]
    install_step = next(step for step in workflow["jobs"]["test"]["steps"] if step.get("name") == "Install local package and tests")
    assert ".[dev]" in install_step["run"]
    assert "pip install tomli" not in install_step["run"]
