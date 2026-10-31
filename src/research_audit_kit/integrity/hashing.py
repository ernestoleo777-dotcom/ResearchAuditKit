# SPDX-License-Identifier: Apache-2.0
"""Deterministic SHA-256 utilities."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path
from typing import Any, Iterable

from ..exceptions import IntegrityFailure


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _file_signature(value: os.stat_result) -> tuple:
    return (value.st_dev, value.st_ino, value.st_mode, value.st_nlink,
            value.st_size, value.st_mtime_ns, value.st_ctime_ns,
            getattr(value, "st_flags", 0))


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    """Hash one stable regular file; reject observable replacement or mutation.

    This is an identity check, not root confinement or historical proof. Callers
    that need confined paths and hydration controls must provide them separately.
    """
    if type(chunk_size) is not int or chunk_size <= 0:
        raise ValueError("chunk_size must be a positive integer")
    target = Path(path)
    before = target.lstat()
    if not stat.S_ISREG(before.st_mode):
        raise IntegrityFailure(f"not a regular file: {target.name}")
    expected = _file_signature(before)
    digest = hashlib.sha256()
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        fd = os.open(target, flags)
    except OSError as exc:
        raise IntegrityFailure(f"file unavailable while hashing: {target.name}") from exc
    try:
        if _file_signature(os.fstat(fd)) != expected:
            raise IntegrityFailure(f"file changed while hashing: {target.name}")
        remaining = before.st_size
        while remaining:
            chunk = os.read(fd, min(chunk_size, remaining))
            if not chunk:
                raise IntegrityFailure(f"file changed while hashing: {target.name}")
            digest.update(chunk)
            remaining -= len(chunk)
        try:
            after = target.lstat()
        except OSError as exc:
            raise IntegrityFailure(f"file changed while hashing: {target.name}") from exc
        if (_file_signature(os.fstat(fd)) != expected
                or _file_signature(after) != expected):
            raise IntegrityFailure(f"file changed while hashing: {target.name}")
    finally:
        os.close(fd)
    return digest.hexdigest()


def stable_object_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256_bytes(payload.encode("utf-8"))


def relative_file_set_hash(root: str | Path, paths: Iterable[str]) -> str:
    base = Path(root).resolve()
    rows = [(path, sha256_file(base / path)) for path in sorted(paths)]
    return stable_object_hash(rows)


def manifest_self_exclusions(manifest: str | Path) -> set[str]:
    name = Path(manifest).name
    return {name, name + ".sha256", name + ".tmp"}
