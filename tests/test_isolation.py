from __future__ import annotations

import os

import pytest

from research_audit_kit.exceptions import InputValidationError
from research_audit_kit.integrity.isolation import audit_isolation, normalize_isolation_manifest


def manifest(workspaces: list[dict]) -> dict:
    return {"version": 1, "workspaces": workspaces}


def workspace(identifier: str, path: str, **extra: object) -> dict:
    return {"workspace_id": identifier, "role": identifier + "-role", "path": path, **extra}


def test_isolation_accepts_disjoint_workspaces_and_symmetric_sharing(tmp_path):
    (tmp_path / "author").mkdir()
    (tmp_path / "inspector").mkdir()
    value = manifest(
        [
            workspace("author", "author", shared_with={"inspector": ["shared/notes"]}),
            workspace("inspector", "inspector", shared_with={"author": ["shared/notes"]}),
        ]
    )
    result = audit_isolation(tmp_path, value)
    assert result["status"] == "PASS"
    assert result["role_counts"] == {"author-role": 1, "inspector-role": 1}


def test_isolation_reports_missing_overlap_and_asymmetric_share(tmp_path):
    (tmp_path / "one").mkdir()
    (tmp_path / "one" / "nested").mkdir()
    result = audit_isolation(
        tmp_path,
        manifest(
            [
                workspace("one", "one", shared_with={"two": ["shared/path"]}),
                workspace("two", "one/nested"),
                workspace("three", "missing"),
            ]
        ),
    )
    assert result["status"] == "FAIL"
    assert set(result["failure_codes"]) == {
        "ISOLATION_SHARED_PATH_MISMATCH",
        "ISOLATION_WORKSPACE_MISSING",
        "ISOLATION_WORKSPACE_OVERLAP",
    }


@pytest.mark.skipif(os.name == "nt", reason="symlink permissions differ on Windows")
def test_isolation_detects_internal_symlink_alias_overlap(tmp_path):
    (tmp_path / "actual").mkdir()
    os.symlink(tmp_path / "actual", tmp_path / "alias")
    result = audit_isolation(
        tmp_path,
        manifest([workspace("actual", "actual"), workspace("alias", "alias")]),
    )
    assert result["failure_codes"] == ["ISOLATION_WORKSPACE_OVERLAP"]


@pytest.mark.skipif(os.name == "nt", reason="symlink permissions differ on Windows")
def test_isolation_reports_escaping_symlink(tmp_path):
    outside = tmp_path.parent / "synthetic-outside"
    outside.mkdir(exist_ok=True)
    os.symlink(outside, tmp_path / "linked")
    result = audit_isolation(tmp_path, manifest([workspace("linked", "linked")]))
    assert result["failure_codes"] == ["ISOLATION_SYMLINK_ESCAPE"]


@pytest.mark.parametrize(
    ("value", "code"),
    [
        ({"version": 0, "workspaces": []}, "ISOLATION_INVALID_MANIFEST"),
        (
            manifest([workspace("same", "one"), workspace("same", "two")]),
            "ISOLATION_DUPLICATE_WORKSPACE_ID",
        ),
        (manifest([workspace("unsafe", "../outside")]), "ISOLATION_UNSAFE_PATH"),
        (manifest([workspace("unsafe", "/absolute")]), "ISOLATION_UNSAFE_PATH"),
    ],
)
def test_isolation_rejects_invalid_manifests(value, code):
    with pytest.raises(InputValidationError, match=code):
        normalize_isolation_manifest(value)
