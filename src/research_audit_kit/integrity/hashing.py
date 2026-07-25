"""Deterministic SHA-256 utilities."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from ..exceptions import IntegrityFailure


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    target = Path(path)
    before = target.stat()
    digest = hashlib.sha256()
    with target.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    after = target.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise IntegrityFailure(f"file changed while hashing: {target.name}")
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
