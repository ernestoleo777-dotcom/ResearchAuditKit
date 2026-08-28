from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from research_audit_kit.integrity.audit import (
    AUDIT_SCHEMA_VERSION,
    FINDING_STATUSES,
    audit_exit_code,
    audit_repository,
    built_in_audit_policy,
    format_audit_human,
)


ROOT = Path(__file__).parents[1]
DEMO = ROOT / "examples" / "audit_demo"


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


def _assert_shape(result: dict[str, object]) -> None:
    schema = json.loads((ROOT / "schemas" / "audit-result-v1.schema.json").read_text())
    assert set(result) == set(schema["required"])
    assert result["schema_version"] == AUDIT_SCHEMA_VERSION
    assert result["command"] == "audit"
    assert result["status"] in schema["properties"]["status"]["enum"]
    assert set(result["counts"]) == set(FINDING_STATUSES)
    for finding in result["findings"]:
        assert set(finding) == {"check_id", "location", "message", "status"}
        assert finding["status"] in FINDING_STATUSES


def test_zero_configuration_pass_is_mechanical_and_stable():
    first = audit_repository(DEMO / "pass_repo")
    second = audit_repository(DEMO / "pass_repo")
    _assert_shape(first)
    assert first == second
    assert first["status"] == "PASS"
    assert first["policy"] == {
        "available": False,
        "mode": "built-in",
        "path": None,
        "policy_id": "rak-generic-release-v1",
    }
    assert first["inventory"]["asset_count"] == 3
    assert len(first["inventory"]["content_sha256"]) == 64
    assert audit_exit_code(first, fail_on="release-blocker") == 0
    assert "not scientific correctness" in " ".join(first["limitations"])


def test_zero_configuration_warning_and_fail_on_behavior():
    result = audit_repository(DEMO / "warning_repo")
    _assert_shape(result)
    assert result["status"] == "WARNING"
    assert result["counts"]["WARNING"] == 1
    assert audit_exit_code(result, fail_on="release-blocker") == 0
    assert audit_exit_code(result, fail_on="warning") == 2
    finding = next(item for item in result["findings"] if item["status"] == "WARNING")
    assert finding["check_id"] == "repository.license"
    assert finding["location"] == "LICENSE"


def test_auto_detected_project_policy_creates_exact_blocker():
    result = audit_repository(DEMO / "blocker_repo")
    _assert_shape(result)
    assert result["status"] == "RELEASE_BLOCKER"
    assert result["policy"] == {
        "available": True,
        "mode": "project",
        "path": ".rak/policy.yaml",
        "policy_id": "synthetic-release-policy-v1",
    }
    blockers = [item for item in result["findings"] if item["status"] == "RELEASE_BLOCKER"]
    assert blockers == [
        {
            "check_id": "policy.required-file",
            "location": "artifacts/model.bin",
            "message": "A file required by the declared policy is missing.",
            "status": "RELEASE_BLOCKER",
        }
    ]
    assert audit_exit_code(result, fail_on="release-blocker") == 2


def test_explicit_policy_is_applied_without_initialization(tmp_path: Path):
    policy = tmp_path / "policy.yaml"
    policy.write_text(
        "policy:\n"
        "  id: explicit-policy\n"
        "  include_patterns: ['**/*']\n"
        "  required_files: [README.md]\n",
        encoding="utf-8",
    )
    result = audit_repository(DEMO / "pass_repo", policy_path=policy)
    assert result["status"] == "PASS"
    assert result["policy"]["mode"] == "project"
    assert result["policy"]["path"] == "<external-policy>"
    assert result["policy"]["policy_id"] == "explicit-policy"


def test_missing_or_invalid_policy_abstains(tmp_path: Path):
    missing = audit_repository(DEMO / "pass_repo", policy_path=tmp_path / "missing.yaml")
    assert missing["status"] == "ABSTAIN"
    assert missing["counts"]["UNRESOLVED"] == 1
    assert audit_exit_code(missing, fail_on="release-blocker") == 2

    invalid = tmp_path / "invalid.yaml"
    invalid.write_text("policy: []\n", encoding="utf-8")
    malformed = audit_repository(DEMO / "pass_repo", policy_path=invalid)
    assert malformed["status"] == "ABSTAIN"
    assert malformed["policy"]["mode"] == "unresolved"

    invalid.write_text("policy: [unterminated\n", encoding="utf-8")
    syntax_error = audit_repository(DEMO / "pass_repo", policy_path=invalid)
    assert syntax_error["status"] == "ABSTAIN"
    assert syntax_error["counts"]["UNRESOLVED"] == 1


def test_missing_target_abstains_without_absolute_path(tmp_path: Path):
    result = audit_repository(tmp_path / "absent")
    assert result["status"] == "ABSTAIN"
    assert result["target"]["root_identifier"] == "absent"
    assert str(tmp_path) not in json.dumps(result)


def test_output_inside_target_does_not_self_pollute(tmp_path: Path):
    target = tmp_path / "pass_repo"
    shutil.copytree(DEMO / "pass_repo", target)
    output = target / "audit-result.json"
    first = audit_repository(target, output_path=output)
    output.write_text(json.dumps(first), encoding="utf-8")
    second = audit_repository(target, output_path=output)
    assert first == second


def test_in_root_symlink_warns_and_escape_blocks(tmp_path: Path):
    if not hasattr(os, "symlink"):
        pytest.skip("symlinks are unavailable")
    target = tmp_path / "repository"
    shutil.copytree(DEMO / "pass_repo", target)
    (target / "readme-link").symlink_to("README.md")
    warning = audit_repository(target)
    assert warning["status"] == "WARNING"
    assert any(item["check_id"] == "repository.symlink" for item in warning["findings"])

    (target / "escape-link").symlink_to(tmp_path / "outside")
    blocker = audit_repository(target)
    assert blocker["status"] == "RELEASE_BLOCKER"
    assert any(item["check_id"] == "repository.path-safety" for item in blocker["findings"])
    assert str(tmp_path) not in json.dumps(blocker)


@pytest.mark.parametrize(
    ("fixture", "expected_code", "expected_status"),
    [
        ("pass_repo", 0, "PASS"),
        ("warning_repo", 0, "WARNING"),
        ("blocker_repo", 2, "RELEASE_BLOCKER"),
    ],
)
def test_cli_json_and_output_contract(
    fixture: str, expected_code: int, expected_status: str, tmp_path: Path
):
    output = tmp_path / f"{fixture}.json"
    result = run_cli("audit", DEMO / fixture, "--format", "json", "--output", output)
    assert result.returncode == expected_code
    stdout = json.loads(result.stdout)
    written = json.loads(output.read_text(encoding="utf-8"))
    assert stdout == written
    assert written["status"] == expected_status
    _assert_shape(written)


def test_cli_default_path_and_warning_threshold():
    default = run_cli("audit", "--format", "json", cwd=DEMO / "pass_repo")
    assert default.returncode == 0
    assert json.loads(default.stdout)["target"]["root_identifier"] == "pass_repo"

    warning = run_cli(
        "audit", ".", "--format", "json", "--fail-on", "warning", cwd=DEMO / "warning_repo"
    )
    assert warning.returncode == 2
    assert json.loads(warning.stdout)["status"] == "WARNING"


def test_human_output_is_deterministic_and_contains_boundary():
    result = audit_repository(DEMO / "warning_repo")
    first = format_audit_human(result)
    assert first == format_audit_human(result)
    assert "Result: WARNING" in first
    assert "repository.license [LICENSE]" in first
    assert "not scientific correctness or certification" in first


@pytest.mark.parametrize("fixture", ["pass_repo", "warning_repo", "blocker_repo"])
def test_human_output_matches_committed_fixture(fixture: str):
    result = audit_repository(DEMO / fixture)
    expected = (DEMO / "expected" / f"{fixture.removesuffix('_repo')}.txt").read_text(
        encoding="utf-8"
    )
    assert format_audit_human(result) + "\n" == expected


def test_schema_and_result_json_are_strictly_parseable():
    schema = json.loads((ROOT / "schemas" / "audit-result-v1.schema.json").read_text())
    assert schema["additionalProperties"] is False
    assert schema["properties"]["schema_version"]["const"] == AUDIT_SCHEMA_VERSION
    result = audit_repository(DEMO / "pass_repo")
    assert json.loads(json.dumps(result, allow_nan=False)) == result


def test_documented_default_policy_matches_built_in_policy():
    import yaml

    documented = yaml.safe_load((ROOT / "configs" / "audit_policy.default.yaml").read_text())
    assert documented == built_in_audit_policy().to_dict()
