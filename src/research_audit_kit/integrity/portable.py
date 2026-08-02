# SPDX-License-Identifier: Apache-2.0
"""Portable identifier and relative-reference validation."""

from __future__ import annotations

from pathlib import Path, PureWindowsPath

from ..exceptions import InputValidationError


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
