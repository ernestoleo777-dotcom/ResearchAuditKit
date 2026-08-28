from __future__ import annotations

from email import policy
from email.parser import BytesParser
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import urllib.parse
import zipfile

import pytest
import yaml

from research_audit_kit import __version__
from research_audit_kit.cli import build_parser

from _toml_compat import tomllib


ROOT = Path(__file__).parents[1]
DEMO = ROOT / "examples" / "repository_integrity_demo"
AUDIT_DEMO = ROOT / "examples" / "audit_demo"
CURATED_DOCS = {
    "docs/audit_command.md",
    "docs/quickstart.md",
    "docs/command_reference.md",
    "docs/use_cases.md",
    "docs/limitations.md",
    "docs/architecture.md",
    "docs/ci_integration.md",
    "docs/extension_boundaries.md",
    "docs/github_action.md",
    "docs/rc2_readiness.md",
    "docs/integrity_model.md",
    "docs/custody_isolation.md",
    "docs/support_audit.md",
    "docs/validation_audit.md",
    "docs/productization/EXISTING_PRODUCT_SURFACE.md",
    "docs/research_release_workflow.md",
    "docs/releases/RC1_TO_RC2_DELTA.md",
    "docs/releases/RC2_DISTRIBUTION_AUDIT.md",
    "docs/releases/v0.1.0-rc.2.md",
}


def run_cli(*args: object, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    return subprocess.run(
        [sys.executable, "-m", "research_audit_kit.cli", *map(str, args)],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def parser_commands() -> set[str]:
    parser = build_parser()
    subparsers = next(
        action for action in parser._actions if action.__class__.__name__ == "_SubParsersAction"
    )
    return set(subparsers.choices)


def read_expected(name: str, root: Path = DEMO) -> dict[str, object]:
    return json.loads((root / "expected" / name).read_text(encoding="utf-8"))


def test_synthetic_demo_replays_from_a_temporary_copy(tmp_path: Path):
    copied = tmp_path / "repository_integrity_demo"
    shutil.copytree(DEMO, copied)

    pass_result = run_cli(
        "inventory",
        "--root",
        copied / "pass_repo",
        "--policy",
        copied / "policy.yaml",
        "--out",
        tmp_path / "pass",
    )
    issue_result = run_cli(
        "inventory",
        "--root",
        copied / "issue_repo",
        "--policy",
        copied / "policy.yaml",
        "--out",
        tmp_path / "issue",
    )

    assert pass_result.returncode == 0
    assert issue_result.returncode == 2
    assert json.loads(pass_result.stdout) == read_expected("pass_summary.json", copied)
    assert json.loads(issue_result.stdout) == read_expected("issue_summary.json", copied)
    assert json.loads((tmp_path / "pass" / "summary.json").read_text()) == read_expected(
        "pass_summary.json", copied
    )
    assert json.loads((tmp_path / "issue" / "summary.json").read_text()) == read_expected(
        "issue_summary.json", copied
    )

    issue_inventory = json.loads((tmp_path / "issue" / "inventory.json").read_text())
    missing = [row for row in issue_inventory["assets"] if row["gate_status"] == "MISSING_REQUIRED"]
    assert missing == [
        {
            "category": "scientific_asset",
            "exclusion_reason": "required file is missing",
            "gate_status": "MISSING_REQUIRED",
            "modified_at": "",
            "path": "README.md",
            "sha256": "",
            "size_bytes": 0,
        }
    ]


def _readme_quickstart_script() -> str:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    marked = readme.split("<!-- quickstart-commands:start -->", 1)[1].split(
        "<!-- quickstart-commands:end -->", 1
    )[0]
    match = re.search(r"```bash\n(?P<script>.*?)\n```", marked, flags=re.DOTALL)
    assert match is not None
    return match["script"]


@pytest.mark.skipif(shutil.which("bash") is None, reason="README quickstart uses POSIX shell")
def test_every_readme_quickstart_command_executes_in_a_fresh_environment(tmp_path: Path):
    checkout = tmp_path / "checkout"
    shutil.copytree(
        ROOT,
        checkout,
        ignore=shutil.ignore_patterns(
            ".git", ".pytest_cache", "__pycache__", "build", "dist", "*.egg-info"
        ),
    )
    environment = tmp_path / "venv"
    subprocess.run(
        [sys.executable, "-m", "venv", "--system-site-packages", str(environment)],
        check=True,
        text=True,
        capture_output=True,
    )
    temp_root = tmp_path / "tmp"
    temp_root.mkdir()
    pip_config = tmp_path / "pip.conf"
    pip_config.write_text("[install]\nno-build-isolation = false\n", encoding="utf-8")
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env["PATH"] = str(environment / "bin") + os.pathsep + env["PATH"]
    env["TMPDIR"] = str(temp_root)
    env["PIP_CONFIG_FILE"] = str(pip_config)
    env["PIP_NO_INDEX"] = "1"
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"

    result = subprocess.run(
        ["bash", "-u", "-o", "pipefail", "-c", _readme_quickstart_script()],
        cwd=checkout,
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"rak {__version__}" in result.stdout
    assert "Result: PASS" in result.stdout
    assert "Result: WARNING" in result.stdout
    assert "Result: RELEASE_BLOCKER" in result.stdout


def test_readme_example_output_matches_executed_demo_expectations():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    section = readme.split("Real terminal output from the committed `pass_repo` fixture:", 1)[1]
    documented = re.search(r"```text\n(.*?)\n```", section, re.DOTALL)
    assert documented is not None
    expected = (AUDIT_DEMO / "expected" / "pass.txt").read_text(encoding="utf-8").rstrip()
    assert documented.group(1) == expected
    replay = run_cli("audit", AUDIT_DEMO / "pass_repo")
    assert replay.returncode == 0
    assert replay.stdout.rstrip() == expected


def test_documented_command_inventory_matches_real_parser_and_help():
    commands = parser_commands()
    assert commands == {
        "audit",
        "init",
        "inventory",
        "freeze",
        "verify",
        "prediction-seal",
        "prediction-verify",
        "isolation-audit",
        "evidence-index",
        "support-audit",
        "pareto-audit",
        "split-audit",
        "gate",
        "deviation",
        "claims",
    }
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    reference = (ROOT / "docs" / "command_reference.md").read_text(encoding="utf-8")
    for command in commands - {"deviation", "claims"}:
        assert f"rak {command}" in readme
        assert f"`rak {command}`" in reference
        assert run_cli(command, "--help").returncode == 0
    for nested in ("deviation record", "claims evaluate"):
        assert f"rak {nested}" in readme
        assert f"`rak {nested}`" in reference
        assert run_cli(*nested.split(), "--help").returncode == 0
    assert run_cli("--help").returncode == 0


def test_ci_example_is_valid_yaml_and_uses_real_commands():
    document = (ROOT / "docs" / "ci_integration.md").read_text(encoding="utf-8")
    match = re.search(r"```yaml\n(?P<workflow>.*?)\n```", document, flags=re.DOTALL)
    assert match is not None
    workflow = yaml.load(match["workflow"], Loader=yaml.BaseLoader)
    assert workflow["permissions"] == {"contents": "read"}
    assert set(workflow["on"]) == {"push", "pull_request"}
    jobs = workflow["jobs"]
    steps = jobs["repository-audit"]["steps"]
    scripts = "\n".join(step.get("run", "") for step in steps)
    uses = [step.get("uses", "") for step in steps]
    assert any(value.startswith("ernestoleo777-dotcom/ResearchAuditKit@") for value in uses)
    assert "pip install" not in scripts
    assert "secrets." not in match["workflow"]
    for command in re.findall(r"\brak\s+([a-z][a-z-]*)", scripts):
        assert command in parser_commands()


def test_public_markdown_relative_links_resolve():
    markdown_files = [
        ROOT / "README.md",
        ROOT / "PROJECT_STATUS.md",
        ROOT / "CONTRIBUTING.md",
        ROOT / "SECURITY.md",
        ROOT / ".github" / "pull_request_template.md",
        *sorted((ROOT / "docs").rglob("*.md")),
        *sorted((ROOT / "examples").rglob("README.md")),
    ]
    missing: list[str] = []
    pattern = re.compile(r"!?\[[^]]*\]\(([^)]+)\)")
    for source in markdown_files:
        for raw_target in pattern.findall(source.read_text(encoding="utf-8")):
            target = raw_target.strip().split()[0].strip("<>")
            parsed = urllib.parse.urlparse(target)
            if parsed.scheme or target.startswith("#"):
                continue
            relative = urllib.parse.unquote(target.split("#", 1)[0])
            if relative and not (source.parent / relative).exists():
                missing.append(f"{source.relative_to(ROOT)} -> {target}")
    assert not missing, missing


def test_public_structured_files_parse():
    json_files = sorted(ROOT.rglob("*.json"))
    yaml_files = sorted(ROOT.rglob("*.yaml")) + sorted(ROOT.rglob("*.yml"))
    toml_files = sorted(ROOT.rglob("*.toml"))
    for path in json_files:
        json.loads(path.read_text(encoding="utf-8"))
    for path in [*yaml_files, ROOT / "CITATION.cff"]:
        yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    for path in toml_files:
        tomllib.loads(path.read_text(encoding="utf-8"))


def test_public_productization_text_has_no_private_or_secret_material():
    paths = [
        ROOT / "README.md",
        ROOT / "CHANGELOG.md",
        ROOT / "CONTRIBUTING.md",
        ROOT / "action.yml",
        ROOT / "MANIFEST.in",
        *sorted((ROOT / "action").rglob("*")),
        *sorted((ROOT / "docs").rglob("*.md")),
        *sorted((ROOT / "examples" / "audit_demo").rglob("*")),
        *sorted((ROOT / "examples" / "repository_integrity_demo").rglob("*")),
        *sorted((ROOT / "schemas").rglob("*.json")),
        *sorted((ROOT / ".github" / "ISSUE_TEMPLATE").rglob("*.yml")),
        ROOT / ".github" / "pull_request_template.md",
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in paths if path.is_file())
    absolute_user_path = re.compile(r"/(?:Users|home)/|[A-Za-z]:\\Users\\")
    credential = re.compile(
        r"BEGIN [A-Z ]*PRIVATE KEY|github_pat_[A-Za-z0-9_]{20,}|"
        r"gh[pousr]_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{20,}"
    )
    private_names = (
        "E" + "WF",
        "V" + "BR",
        "V" + "RC",
        "Trust" + "Edit-RC",
        "Research" + "Premortem",
    )
    assert absolute_user_path.search(text) is None
    assert credential.search(text) is None
    assert not [name for name in private_names if name in text]


def test_version_and_status_are_consistent():
    assert __version__ == "0.1.0rc3.dev0"
    citation = yaml.safe_load((ROOT / "CITATION.cff").read_text(encoding="utf-8"))
    assert citation["version"] == "0.1.0rc2"
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert f"development source version v{__version__} — unpublished — no stable release" in readme
    project_status = (ROOT / "PROJECT_STATUS.md").read_text(encoding="utf-8")
    assert f"DISTRIBUTION_SOURCE_VERSION = {__version__}" in project_status
    assert "LATEST_PUBLIC_RELEASE = 0.1.0rc2" in project_status
    assert "FUTURE_RELEASE_TARGET = v0.1.0-rc.3" in project_status
    assert "RC3_RELEASED = FALSE" in project_status
    assert "STABLE_RELEASED = FALSE" in project_status
    assert "STABLE_RELEASE = NONE" in project_status
    assert "DISTRIBUTION_AUTHORITY = GITHUB_RELEASES" in project_status
    assert "PYPI_DISTRIBUTION = NONE" in project_status
    assert "CURRENT_VERSION = 0.1.0rc2" in (
        ROOT / "docs" / "rc2_readiness.md"
    ).read_text(encoding="utf-8")


def test_wheel_and_sdist_public_content_contract(tmp_path: Path):
    checkout = tmp_path / "checkout"
    shutil.copytree(
        ROOT,
        checkout,
        ignore=shutil.ignore_patterns(
            ".git", ".pytest_cache", "__pycache__", "build", "dist", "*.egg-info"
        ),
    )
    dist = tmp_path / "dist"
    dist.mkdir()
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "build",
            "--no-isolation",
            "--outdir",
            str(dist),
            ".",
        ],
        cwd=checkout,
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    wheel = dist / "research_audit_kit-0.1.0rc3.dev0-py3-none-any.whl"
    sdist = dist / "research_audit_kit-0.1.0rc3.dev0.tar.gz"
    assert wheel.is_file() and sdist.is_file()

    with zipfile.ZipFile(wheel) as archive:
        wheel_names = set(archive.namelist())
        metadata_name = next(name for name in wheel_names if name.endswith(".dist-info/METADATA"))
        metadata = BytesParser(policy=policy.default).parsebytes(archive.read(metadata_name))
        assert metadata["Version"] == __version__
        assert "Audit and freeze an ML repository before public release" in metadata.get_payload()
        assert not [name for name in wheel_names if name.startswith(("docs/", "examples/"))]

    with tarfile.open(sdist) as archive:
        names = set(archive.getnames())
        prefix = next(
            name.removesuffix("/README.md")
            for name in names
            if name.count("/") == 1 and name.endswith("/README.md")
        )
        required = {
            "README.md",
            "PROJECT_STATUS.md",
            "action.yml",
            *CURATED_DOCS,
            "action/run-audit.sh",
            "action/bootstrap.sh",
            "action/render-summary.py",
            "action/requirements.lock",
            "action/runner.py",
            "schemas/audit-result-v1.schema.json",
            "configs/audit_policy.default.yaml",
            "examples/audit_demo/README.md",
            "examples/audit_demo/expected/pass.txt",
            "examples/audit_demo/expected/warning.txt",
            "examples/audit_demo/expected/blocker.txt",
            "examples/audit_demo/pass_repo/README.md",
            "examples/audit_demo/pass_repo/LICENSE",
            "examples/audit_demo/pass_repo/analysis.py",
            "examples/audit_demo/warning_repo/README.md",
            "examples/audit_demo/warning_repo/analysis.py",
            "examples/audit_demo/blocker_repo/.rak/policy.yaml",
            "examples/audit_demo/blocker_repo/README.md",
            "examples/audit_demo/blocker_repo/LICENSE",
            "examples/audit_demo/blocker_repo/analysis.py",
            "examples/repository_integrity_demo/README.md",
            "examples/repository_integrity_demo/policy.yaml",
            "examples/repository_integrity_demo/expected/pass_summary.json",
            "examples/repository_integrity_demo/expected/issue_summary.json",
            "examples/repository_integrity_demo/pass_repo/README.md",
            "examples/repository_integrity_demo/pass_repo/analysis.py",
            "examples/repository_integrity_demo/pass_repo/measurements.csv",
            "examples/repository_integrity_demo/issue_repo/analysis.py",
            "examples/repository_integrity_demo/issue_repo/measurements.csv",
        }
        missing = [path for path in required if f"{prefix}/{path}" not in names]
        assert not missing, missing
