import os
from pathlib import Path

import pytest

from research_audit_kit.exceptions import UnsafePathError, UnsupportedFormatError
from research_audit_kit.integrity.inventory import build_inventory, safe_relative, write_inventory


def test_inventory_uses_relative_paths(clean_repo, policy):
    rows = build_inventory(clean_repo, policy)
    assert all(not Path(str(row["path"])).is_absolute() for row in rows)


def test_inventory_writes_csv_and_json(clean_repo, policy, tmp_path):
    paths = write_inventory(build_inventory(clean_repo, policy), tmp_path / "out")
    assert all(path.exists() for path in paths)


def test_missing_required_is_recorded(tmp_path, policy):
    rows = build_inventory(tmp_path, policy)
    assert any(row["gate_status"] == "MISSING_REQUIRED" for row in rows)


def test_safe_relative_rejects_escape(tmp_path):
    with pytest.raises(UnsafePathError):
        safe_relative(tmp_path / "inside", tmp_path / "outside.txt")


def test_symlink_root_escape_rejected(tmp_path, policy):
    root = tmp_path / "root"
    root.mkdir()
    (root / "README.md").write_text("fixture")
    outside = tmp_path / "outside.txt"
    outside.write_text("outside")
    (root / "escape.txt").symlink_to(outside)
    with pytest.raises(UnsafePathError):
        build_inventory(root, policy)


def test_broken_internal_symlink_is_recorded_without_following(tmp_path, policy):
    root = tmp_path / "root"
    root.mkdir()
    (root / "README.md").write_text("fixture")
    (root / "broken.csv").symlink_to(root / "missing.csv")
    rows = build_inventory(root, policy)
    row = next(item for item in rows if item["path"] == "broken.csv")
    assert row["exclusion_reason"] == "symlink recorded but target was not followed"


def test_fifo_is_rejected_as_unsupported_object(tmp_path, policy):
    root = tmp_path / "root"
    root.mkdir()
    (root / "README.md").write_text("fixture")
    fifo = root / "stream.csv"
    os.mkfifo(fifo)
    with pytest.raises(UnsupportedFormatError):
        build_inventory(root, policy)


def test_unicode_and_space_paths(clean_repo, policy):
    (clean_repo / "space name.csv").write_text("id,value\na,1\n")
    (clean_repo / "数据.csv").write_text("id,value\nb,2\n")
    paths = {row["path"] for row in build_inventory(clean_repo, policy)}
    assert {"space name.csv", "数据.csv"} <= paths
