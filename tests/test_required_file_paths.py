from __future__ import annotations

import csv
import json
import os
from pathlib import Path

import pytest
import yaml

from research_audit_kit.cli import main
from research_audit_kit.exceptions import RequiredFilePathError
from research_audit_kit.integrity import inventory as inventory_module
from research_audit_kit.integrity import portable as portable_module
from research_audit_kit.integrity.audit import (
    audit_exit_code,
    audit_repository,
    format_audit_human,
)
from research_audit_kit.integrity.inventory import build_inventory
from research_audit_kit.integrity.policy import IntegrityPolicy
from research_audit_kit.integrity.verification import verify_baseline


VALID_REQUIRED_FILES = (
    "README.md",
    "LICENSE",
    ".github/workflows/ci.yml",
    "docs/release guide.md",
    "结果/摘要.md",
    "docs/.../notes.md",
)

EXAMPLE_MAC_HOME_PATH = "/" + "Users" + "/example/private.txt"
EXAMPLE_WINDOWS_FORWARD_PATH = "C:/" + "Users" + "/example/private.txt"

INVALID_REQUIRED_FILES = (
    ("../outside.txt", "PARENT_TRAVERSAL"),
    ("../../outside.txt", "PARENT_TRAVERSAL"),
    ("a/../../outside.txt", "PARENT_TRAVERSAL"),
    (EXAMPLE_MAC_HOME_PATH, "ABSOLUTE_PATH"),
    ("/etc/passwd", "ABSOLUTE_PATH"),
    (r"C:\Users\example\private.txt", "WINDOWS_DRIVE_PATH"),
    (EXAMPLE_WINDOWS_FORWARD_PATH, "WINDOWS_DRIVE_PATH"),
    ("C:private.txt", "WINDOWS_DRIVE_PATH"),
    (r"\\server\share\private.txt", "UNC_PATH"),
    ("//server/share/private.txt", "UNC_PATH"),
    (r"\\?\C:\private.txt", "WINDOWS_DEVICE_PATH"),
    (r"a\..\outside.txt", "PARENT_TRAVERSAL"),
    (".", "NON_CANONICAL_PATH"),
    ("", "EMPTY_PATH"),
    ("docs/./file.md", "NON_CANONICAL_PATH"),
    ("docs//file.md", "NON_CANONICAL_PATH"),
    ("docs/", "NON_CANONICAL_PATH"),
    ("docs/\x00private.txt", "CONTROL_CHARACTER"),
    ("docs/\nprivate.txt", "CONTROL_CHARACTER"),
)


def _policy(required: str) -> dict[str, object]:
    return {
        "policy": {
            "id": "required-path-test",
            "include_patterns": ["**/*"],
            "required_files": [required],
        }
    }


def _repository_with_policy(tmp_path: Path, required: str) -> tuple[Path, Path]:
    root = tmp_path / "repository"
    policy_path = root / ".rak" / "policy.yaml"
    policy_path.parent.mkdir(parents=True)
    (root / "README.md").write_text("# Fixture\n", encoding="utf-8")
    (root / "LICENSE").write_text("Fixture license\n", encoding="utf-8")
    policy_path.write_text(yaml.safe_dump(_policy(required), sort_keys=True), encoding="utf-8")
    return root, policy_path


def _assert_raw_value_absent(value: str, text: str) -> None:
    if len(value) > 1 and value.isprintable():
        assert value not in text
    assert "/" + "Users" + "/example" not in text
    assert "C:\\Users\\example" not in text
    assert "server\\share\\private" not in text


@pytest.mark.parametrize("required", VALID_REQUIRED_FILES)
def test_required_file_portable_grammar_preserves_valid_values(required: str):
    policy = IntegrityPolicy.from_dict(_policy(required))
    assert policy.required_files == (required,)
    assert policy.to_dict()["policy"]["required_files"] == [required]


def test_all_valid_required_paths_are_inventoried_without_normalization(tmp_path: Path):
    root = tmp_path / "repository"
    for required in VALID_REQUIRED_FILES:
        path = root / required
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"fixture for {required}\n", encoding="utf-8")
    policy = IntegrityPolicy.from_dict(
        {"policy": {"id": "valid-paths", "required_files": list(VALID_REQUIRED_FILES)}}
    )

    rows = build_inventory(root, policy)

    present = {str(row["path"]) for row in rows}
    assert set(VALID_REQUIRED_FILES) <= present
    assert not [row for row in rows if row["gate_status"] == "MISSING_REQUIRED"]


def test_invalid_required_path_reports_its_original_list_index():
    value = {
        "policy": {
            "id": "indexed",
            "required_files": ["README.md", "../outside.txt"],
        }
    }
    with pytest.raises(RequiredFilePathError) as caught:
        IntegrityPolicy.from_dict(value)
    assert caught.value.index == 1
    assert "policy.required_files[1]" in str(caught.value)
    assert "../outside.txt" not in str(caught.value)


@pytest.mark.parametrize(("required", "reason"), INVALID_REQUIRED_FILES)
def test_required_file_portable_grammar_rejects_without_echo(required: str, reason: str):
    with pytest.raises(RequiredFilePathError) as caught:
        IntegrityPolicy.from_dict(_policy(required))
    assert caught.value.index == 0
    assert caught.value.reason_code == reason
    assert caught.value.error_code == f"POLICY_REQUIRED_FILE_PATH_{reason}"
    _assert_raw_value_absent(required, str(caught.value))


@pytest.mark.parametrize(("required", "reason"), INVALID_REQUIRED_FILES)
def test_invalid_audit_policy_abstains_deterministically_and_never_inventories(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    required: str,
    reason: str,
):
    root, _ = _repository_with_policy(tmp_path, required)

    def forbidden_inventory(*args: object, **kwargs: object):
        raise AssertionError("invalid lexical policy reached repository inventory")

    monkeypatch.setattr("research_audit_kit.integrity.audit.build_inventory", forbidden_inventory)
    first_output = tmp_path / "first.json"
    second_output = tmp_path / "second.json"

    first_code = main(["audit", str(root), "--format", "json", "--output", str(first_output)])
    first = capsys.readouterr()
    second_code = main(["audit", str(root), "--format", "json", "--output", str(second_output)])
    second = capsys.readouterr()

    assert first_code == second_code == 2
    assert first.out == second.out
    assert first.err == second.err == ""
    assert first_output.read_bytes() == second_output.read_bytes()
    result = json.loads(first.out)
    assert result["status"] == "ABSTAIN"
    assert result["counts"]["UNRESOLVED"] == 1
    assert result["inventory"] == {"asset_count": 0, "content_sha256": None}
    assert audit_exit_code(result, fail_on="release-blocker") == 2
    assert result["findings"] == [
        {
            "check_id": f"policy.required-file-path.{reason}",
            "location": ".rak/policy.yaml",
            "message": (
                f"Project policy could not be applied: POLICY_REQUIRED_FILE_PATH_{reason}: "
                "policy.required_files[0]: invalid non-confined path"
            ),
            "status": "UNRESOLVED",
        }
    ]
    emitted = (
        first.out
        + first.err
        + first_output.read_text(encoding="utf-8")
        + format_audit_human(result)
    )
    _assert_raw_value_absent(required, emitted)


@pytest.mark.parametrize(("required", "reason"), INVALID_REQUIRED_FILES)
def test_invalid_policy_fails_inventory_and_freeze_without_partial_output(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    required: str,
    reason: str,
):
    root, policy_path = _repository_with_policy(tmp_path, required)
    inventory_out = tmp_path / "inventory-output"
    baseline = tmp_path / "baseline.csv"

    inventory_first = main(
        [
            "inventory",
            "--root",
            str(root),
            "--policy",
            str(policy_path),
            "--out",
            str(inventory_out),
        ]
    )
    first_inventory_text = capsys.readouterr()
    inventory_second = main(
        [
            "inventory",
            "--root",
            str(root),
            "--policy",
            str(policy_path),
            "--out",
            str(inventory_out),
        ]
    )
    second_inventory_text = capsys.readouterr()

    freeze_first = main(
        [
            "freeze",
            "--root",
            str(root),
            "--policy",
            str(policy_path),
            "--baseline",
            str(baseline),
        ]
    )
    first_freeze_text = capsys.readouterr()
    freeze_second = main(
        [
            "freeze",
            "--root",
            str(root),
            "--policy",
            str(policy_path),
            "--baseline",
            str(baseline),
        ]
    )
    second_freeze_text = capsys.readouterr()

    assert inventory_first == inventory_second == 2
    assert freeze_first == freeze_second == 2
    assert first_inventory_text == second_inventory_text
    assert first_freeze_text == second_freeze_text
    assert not inventory_out.exists()
    assert not baseline.exists()
    assert not baseline.with_name(baseline.name + ".sha256").exists()
    emitted = (
        first_inventory_text.out
        + first_inventory_text.err
        + first_freeze_text.out
        + first_freeze_text.err
    )
    assert f"POLICY_REQUIRED_FILE_PATH_{reason}" in emitted
    assert "policy.required_files[0]" in emitted
    _assert_raw_value_absent(required, emitted)


@pytest.mark.parametrize(("required", "reason"), INVALID_REQUIRED_FILES)
def test_direct_policy_construction_cannot_probe_or_bypass_lexical_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    required: str,
    reason: str,
):
    root = tmp_path / "repository"
    root.mkdir()
    policy = IntegrityPolicy(policy_id="direct", required_files=(required,))

    def forbidden_lstat(path: object):
        raise AssertionError(f"filesystem was probed: {type(path).__name__}")

    monkeypatch.setattr(portable_module, "_lstat", forbidden_lstat)
    with pytest.raises(RequiredFilePathError) as caught:
        build_inventory(root, policy)
    assert caught.value.reason_code == reason
    _assert_raw_value_absent(required, str(caught.value))


def test_escaping_required_symlink_never_probes_or_hashes_outside_and_is_stable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    root, _ = _repository_with_policy(tmp_path, "artifact.bin")
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    outside_file = outside_dir / "private.bin"
    outside_file.write_bytes(b"outside secret bytes")
    (root / "artifact.bin").symlink_to(outside_file)

    observed_lstat: list[Path] = []
    observed_readlink: list[Path] = []
    real_lstat = portable_module._lstat
    real_readlink = portable_module._readlink
    resolved_root = root.resolve()

    def confined_lstat(path: object):
        candidate = Path(os.path.abspath(os.fspath(path)))
        candidate.relative_to(resolved_root)
        observed_lstat.append(candidate)
        return real_lstat(path)

    def confined_readlink(path: object):
        candidate = Path(os.path.abspath(os.fspath(path)))
        candidate.relative_to(resolved_root)
        observed_readlink.append(candidate)
        return real_readlink(path)

    def forbidden_hash(path: object):
        raise AssertionError(f"content hashing was reached: {type(path).__name__}")

    monkeypatch.setattr(portable_module, "_lstat", confined_lstat)
    monkeypatch.setattr(portable_module, "_readlink", confined_readlink)
    monkeypatch.setattr(inventory_module, "sha256_file", forbidden_hash)

    with_outside = audit_repository(root)
    outside_file.unlink()
    without_outside = audit_repository(root)

    assert with_outside == without_outside
    assert with_outside["status"] == "ABSTAIN"
    assert with_outside["inventory"] == {"asset_count": 0, "content_sha256": None}
    finding = with_outside["findings"][0]
    assert finding["check_id"] == "policy.required-file-path.RESOLVED_OUTSIDE_ROOT"
    assert finding["location"] == ".rak/policy.yaml"
    assert "policy.required_files[0]" in finding["message"]
    emitted = json.dumps(with_outside, sort_keys=True) + format_audit_human(with_outside)
    assert str(outside_file) not in emitted
    assert "../outside" not in emitted
    assert observed_lstat
    assert observed_readlink
    assert all(path == resolved_root / "artifact.bin" for path in observed_lstat)
    assert all(path == resolved_root / "artifact.bin" for path in observed_readlink)


def test_escaping_required_symlink_fails_inventory_and_freeze_without_outputs(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
):
    root, policy_path = _repository_with_policy(tmp_path, "artifact.bin")
    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"outside")
    (root / "artifact.bin").symlink_to(outside)
    inventory_out = tmp_path / "inventory"
    baseline = tmp_path / "baseline.csv"

    inventory_code = main(
        [
            "inventory",
            "--root",
            str(root),
            "--policy",
            str(policy_path),
            "--out",
            str(inventory_out),
        ]
    )
    inventory_text = capsys.readouterr()
    freeze_code = main(
        [
            "freeze",
            "--root",
            str(root),
            "--policy",
            str(policy_path),
            "--baseline",
            str(baseline),
        ]
    )
    freeze_text = capsys.readouterr()

    assert inventory_code == freeze_code == 2
    assert not inventory_out.exists()
    assert not baseline.exists()
    emitted = inventory_text.err + freeze_text.err
    assert "POLICY_REQUIRED_FILE_PATH_RESOLVED_OUTSIDE_ROOT" in emitted
    assert str(outside) not in emitted


def test_verify_rejects_an_unsafe_required_path_embedded_in_baseline(tmp_path: Path):
    raw = EXAMPLE_MAC_HOME_PATH
    baseline = tmp_path / "baseline.csv"
    fields = [
        "baseline_id",
        "policy_id",
        "created_at",
        "root_identifier",
        "path",
        "size_bytes",
        "sha256",
        "category",
        "policy_json",
        "forced_overwrite",
    ]
    row = {
        "baseline_id": "unsafe-baseline",
        "policy_id": "unsafe-policy",
        "created_at": "2026-01-01T00:00:00+00:00",
        "root_identifier": "repository",
        "path": "README.md",
        "size_bytes": "0",
        "sha256": "",
        "category": "scientific_asset",
        "policy_json": json.dumps(_policy(raw), sort_keys=True, separators=(",", ":")),
        "forced_overwrite": "false",
    }
    with baseline.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow(row)

    with pytest.raises(RequiredFilePathError) as caught:
        verify_baseline(tmp_path, baseline)
    assert caught.value.reason_code == "ABSOLUTE_PATH"
    assert raw not in str(caught.value)
