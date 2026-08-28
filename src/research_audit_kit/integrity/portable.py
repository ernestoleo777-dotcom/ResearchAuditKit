# SPDX-License-Identifier: Apache-2.0
"""Portable identifier and relative-reference validation."""

from __future__ import annotations

from collections import deque
import os
from os import lstat as _lstat
from os import readlink as _readlink
from pathlib import Path, PureWindowsPath
import re
import stat
import unicodedata
from typing import Iterable

from ..exceptions import InputValidationError, PolicyError, RequiredFilePathError


_WINDOWS_DRIVE = re.compile(r"^[A-Za-z]:")
_WINDOWS_DEVICE_PREFIXES = ("\\\\?\\", "\\\\.\\", "//?/", "//./")


def normalize_portable_reference(value: object, *, code: str, field: str) -> str:
    """Return an opaque identifier or normalized safe relative path.

    References without a path separator remain opaque identifiers. Path-like
    references must already be normalized portable relative paths.
    """
    if not isinstance(value, str) or not value.strip():
        raise InputValidationError(f"{code}: {field} must be a non-empty string")
    if Path(value).is_absolute() or PureWindowsPath(value).is_absolute() or PureWindowsPath(value).drive:
        raise InputValidationError(f"{code}: {field} must not be absolute")
    if value in {".", ".."}:
        raise InputValidationError(f"{code}: {field} must be a normalized relative path")
    if "/" not in value and "\\" not in value:
        return value

    normalized = value.replace("\\", "/")
    parts = normalized.split("/")
    if (
        normalized.startswith("/")
        or "" in parts
        or any(part in {".", ".."} for part in parts)
    ):
        raise InputValidationError(f"{code}: {field} must be a normalized relative path")
    return normalized


def validate_required_file_paths(values: object) -> tuple[str, ...]:
    """Validate canonical portable policy.required_files entries without I/O."""

    if not isinstance(values, (list, tuple)):
        raise PolicyError(
            "POLICY_REQUIRED_FILES_TYPE: policy.required_files must be a list"
        )

    validated: list[str] = []
    for index, value in enumerate(values):
        if not isinstance(value, str) or not value or not value.strip():
            raise RequiredFilePathError(index=index, reason_code="EMPTY_PATH")
        if any(unicodedata.category(character) == "Cc" for character in value):
            raise RequiredFilePathError(index=index, reason_code="CONTROL_CHARACTER")
        if value.startswith(_WINDOWS_DEVICE_PREFIXES):
            raise RequiredFilePathError(index=index, reason_code="WINDOWS_DEVICE_PATH")
        if value.startswith(("\\\\", "//")):
            raise RequiredFilePathError(index=index, reason_code="UNC_PATH")
        if _WINDOWS_DRIVE.match(value) or PureWindowsPath(value).drive:
            raise RequiredFilePathError(index=index, reason_code="WINDOWS_DRIVE_PATH")
        if value.startswith("/"):
            raise RequiredFilePathError(index=index, reason_code="ABSOLUTE_PATH")

        portable_parts = value.replace("\\", "/").split("/")
        if ".." in portable_parts:
            raise RequiredFilePathError(index=index, reason_code="PARENT_TRAVERSAL")
        if "\\" in value or any(part in {"", "."} for part in portable_parts):
            raise RequiredFilePathError(index=index, reason_code="NON_CANONICAL_PATH")
        validated.append(value)
    return tuple(validated)


def validate_required_file_confinement(
    root: str | Path, required_files: Iterable[str]
) -> None:
    """Reject required paths whose existing symlink chain leaves ``root``.

    Only path components lexically inside the root are inspected. An escaping
    symlink is rejected from its link text before any outside target is probed.
    """

    values = validate_required_file_paths(tuple(required_files))
    base = Path(root).resolve()
    for index, value in enumerate(values):
        _validate_required_file_resolution(base, value, index=index)


def _validate_required_file_resolution(base: Path, value: str, *, index: int) -> None:
    pending = deque(value.split("/"))
    current_parts: list[str] = []
    seen_symlinks: set[Path] = set()

    while pending:
        current_parts.append(pending.popleft())
        candidate = base.joinpath(*current_parts)
        try:
            metadata = _lstat(candidate)
        except (FileNotFoundError, NotADirectoryError):
            return
        if not stat.S_ISLNK(metadata.st_mode):
            continue

        if candidate in seen_symlinks:
            raise RequiredFilePathError(index=index, reason_code="SYMLINK_CYCLE")
        seen_symlinks.add(candidate)
        target_text = _readlink(candidate)

        target_windows = PureWindowsPath(target_text)
        if target_windows.drive and not Path(target_text).is_absolute():
            raise RequiredFilePathError(index=index, reason_code="RESOLVED_OUTSIDE_ROOT")
        portable_target = target_text.replace("\\", "/")
        target_path = Path(portable_target)
        if target_path.is_absolute():
            target_absolute = Path(os.path.abspath(target_path))
        else:
            target_absolute = Path(os.path.abspath(candidate.parent / target_path))
        try:
            target_relative = target_absolute.relative_to(base)
        except ValueError as exc:
            raise RequiredFilePathError(
                index=index, reason_code="RESOLVED_OUTSIDE_ROOT"
            ) from exc

        remaining = list(pending)
        pending = deque([*target_relative.parts, *remaining])
        current_parts = []
