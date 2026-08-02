# SPDX-License-Identifier: Apache-2.0
"""Structural audit for declared local workspace isolation."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from ..constants import STATUS_FAIL, STATUS_PASS
from ..exceptions import InputValidationError
from ..io.json_io import write_json
from .portable import normalize_portable_reference

_MANIFEST_FIELDS = {"version", "workspaces"}
_WORKSPACE_FIELDS = {
    "workspace_id",
    "role",
    "path",
    "allowed_inputs",
    "allowed_outputs",
    "shared_with",
}


def _error(code: str, message: str) -> None:
    raise InputValidationError(f"{code}: {message}")


def _string(value: Mapping[str, Any], field: str, code: str) -> str:
    raw = value.get(field)
    if not isinstance(raw, str) or not raw.strip():
        _error(code, f"{field} must be a non-empty string")
    return raw


def _relative_path(value: object, *, code: str, field: str) -> str:
    result = normalize_portable_reference(value, code=code, field=field)
    if "/" not in result:
        return result
    return result


def _path_list(value: object, *, field: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        _error("ISOLATION_INVALID_MANIFEST", f"{field} must be an array")
    return [_relative_path(item, code="ISOLATION_UNSAFE_PATH", field=field) for item in value]


def _shared(value: object) -> dict[str, list[str]]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        _error("ISOLATION_INVALID_MANIFEST", "shared_with must be an object")
    result: dict[str, list[str]] = {}
    for peer, paths in value.items():
        if not isinstance(peer, str) or not peer.strip() or not isinstance(paths, list) or not paths:
            _error("ISOLATION_INVALID_MANIFEST", "shared_with entries need a role id and non-empty path list")
        normalized = [_relative_path(path, code="ISOLATION_UNSAFE_PATH", field="shared_with") for path in paths]
        if len(set(normalized)) != len(normalized):
            _error("ISOLATION_INVALID_MANIFEST", "shared_with paths must be unique")
        result[peer] = sorted(normalized)
    return result


def normalize_isolation_manifest(value: Mapping[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(value, Mapping) or set(value) != _MANIFEST_FIELDS:
        _error("ISOLATION_INVALID_MANIFEST", "manifest has missing or undeclared fields")
    if not isinstance(value["version"], int) or value["version"] < 1:
        _error("ISOLATION_INVALID_MANIFEST", "version must be a positive integer")
    raw_workspaces = value["workspaces"]
    if not isinstance(raw_workspaces, list) or not raw_workspaces:
        _error("ISOLATION_INVALID_MANIFEST", "workspaces must be a non-empty array")

    normalized: list[dict[str, Any]] = []
    identifiers: set[str] = set()
    for workspace in raw_workspaces:
        if not isinstance(workspace, Mapping) or not set(workspace).issubset(_WORKSPACE_FIELDS):
            _error("ISOLATION_INVALID_MANIFEST", "workspace has undeclared fields")
        for required in ("workspace_id", "role", "path"):
            if required not in workspace:
                _error("ISOLATION_INVALID_MANIFEST", f"workspace is missing {required}")
        workspace_id = _string(workspace, "workspace_id", "ISOLATION_INVALID_MANIFEST")
        if workspace_id in identifiers:
            _error("ISOLATION_DUPLICATE_WORKSPACE_ID", f"duplicate workspace_id {workspace_id!r}")
        identifiers.add(workspace_id)
        normalized.append(
            {
                "workspace_id": workspace_id,
                "role": _string(workspace, "role", "ISOLATION_INVALID_MANIFEST"),
                "path": _relative_path(workspace["path"], code="ISOLATION_UNSAFE_PATH", field="path"),
                "allowed_inputs": _path_list(workspace.get("allowed_inputs"), field="allowed_inputs"),
                "allowed_outputs": _path_list(workspace.get("allowed_outputs"), field="allowed_outputs"),
                "shared_with": _shared(workspace.get("shared_with")),
            }
        )
    return sorted(normalized, key=lambda item: item["workspace_id"])


def _contained(root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve(strict=False).relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _nested_path(left: str, right: str) -> bool:
    return left == right or left.startswith(right + "/") or right.startswith(left + "/")


def _workspace_symlink_escapes(root: Path, workspace: Path) -> bool:
    if workspace.is_symlink() and not _contained(root, workspace):
        return True
    for candidate in workspace.rglob("*"):
        if candidate.is_symlink() and not _contained(root, candidate):
            return True
    return False


def audit_isolation(root: str | Path, manifest: Mapping[str, Any]) -> dict[str, Any]:
    base = Path(root).resolve()
    if not base.is_dir():
        _error("ISOLATION_INVALID_MANIFEST", "root must be an existing directory")
    workspaces = normalize_isolation_manifest(manifest)
    findings: dict[str, set[str]] = {item["workspace_id"]: set() for item in workspaces}
    by_id = {item["workspace_id"]: item for item in workspaces}
    resolved_paths: dict[str, str] = {}

    for workspace in workspaces:
        target = base / workspace["path"]
        if target.is_symlink() and not _contained(base, target):
            findings[workspace["workspace_id"]].add("ISOLATION_SYMLINK_ESCAPE")
        elif not _contained(base, target):
            findings[workspace["workspace_id"]].add("ISOLATION_UNSAFE_PATH")
        elif not target.is_dir():
            findings[workspace["workspace_id"]].add("ISOLATION_WORKSPACE_MISSING")
        elif _workspace_symlink_escapes(base, target):
            findings[workspace["workspace_id"]].add("ISOLATION_SYMLINK_ESCAPE")
        else:
            resolved_paths[workspace["workspace_id"]] = target.resolve().relative_to(base).as_posix()

    for index, workspace in enumerate(workspaces):
        for other in workspaces[index + 1 :]:
            same_effective_path = (
                workspace["workspace_id"] in resolved_paths
                and other["workspace_id"] in resolved_paths
                and _nested_path(
                    resolved_paths[workspace["workspace_id"]],
                    resolved_paths[other["workspace_id"]],
                )
            )
            if _nested_path(workspace["path"], other["path"]) or same_effective_path:
                findings[workspace["workspace_id"]].add("ISOLATION_WORKSPACE_OVERLAP")
                findings[other["workspace_id"]].add("ISOLATION_WORKSPACE_OVERLAP")

    for workspace in workspaces:
        workspace_id = workspace["workspace_id"]
        for peer, paths in workspace["shared_with"].items():
            reciprocal = by_id.get(peer, {}).get("shared_with", {}).get(workspace_id)
            if peer == workspace_id or reciprocal != paths:
                findings[workspace_id].add("ISOLATION_SHARED_PATH_MISMATCH")
                if peer in findings:
                    findings[peer].add("ISOLATION_SHARED_PATH_MISMATCH")

    output = []
    for workspace in workspaces:
        codes = sorted(findings[workspace["workspace_id"]])
        output.append(
            {
                **workspace,
                "status": STATUS_FAIL if codes else STATUS_PASS,
                "failure_codes": codes,
            }
        )
    failure_codes = sorted({code for codes in findings.values() for code in codes})
    return {
        "status": STATUS_FAIL if failure_codes else STATUS_PASS,
        "failure_codes": failure_codes,
        "workspace_count": len(output),
        "role_counts": dict(sorted(Counter(item["role"] for item in output).items())),
        "workspaces": output,
        "limitation": "A structural pass does not prove human-role separation, access-control enforcement, absence of copies, or scientific blinding.",
    }


def write_isolation_audit(result: Mapping[str, Any], out_dir: str | Path) -> Path:
    return write_json(Path(out_dir) / "isolation_audit.json", dict(result))
