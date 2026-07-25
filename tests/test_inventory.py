from pathlib import Path

import pytest

from research_audit_kit.exceptions import UnsafePathError
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


def test_unicode_and_space_paths(clean_repo, policy):
    (clean_repo / "space name.csv").write_text("id,value\na,1\n")
    (clean_repo / "数据.csv").write_text("id,value\nb,2\n")
    paths = {row["path"] for row in build_inventory(clean_repo, policy)}
    assert {"space name.csv", "数据.csv"} <= paths
