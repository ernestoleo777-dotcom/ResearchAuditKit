from __future__ import annotations

import ast
import subprocess
import sys
import tomllib
from pathlib import Path

from research_audit_kit import __version__

ROOT = Path(__file__).parents[1]


def test_single_version_source():
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert "version" not in metadata["project"]
    assert metadata["tool"]["setuptools"]["dynamic"]["version"]["attr"].endswith(".__version__")
    assert __version__ == "0.1.0"


def test_cli_version_matches_package():
    result = subprocess.run([sys.executable, "-m", "research_audit_kit.cli", "--version"], cwd=ROOT, env={"PYTHONPATH": str(ROOT / "src")}, text=True, capture_output=True, check=False)
    assert result.returncode == 0
    assert result.stdout.strip().endswith(__version__)


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
