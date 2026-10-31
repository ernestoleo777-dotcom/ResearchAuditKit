from __future__ import annotations

import hashlib
import os

import pytest

from research_audit_kit.exceptions import IntegrityFailure
from research_audit_kit.integrity import hashing


def mutate_after_read(monkeypatch, action):
    real = hashlib.sha256
    class Digest:
        def __init__(self):
            self.digest = real()
            self.changed = False
        def update(self, payload):
            self.digest.update(payload)
            if not self.changed:
                self.changed = True
                action()
        def hexdigest(self):
            return self.digest.hexdigest()
    monkeypatch.setattr(hashing.hashlib, "sha256", Digest)


def test_replacement_with_same_size_and_mtime_is_rejected(tmp_path, monkeypatch):
    path = tmp_path / "asset"
    path.write_bytes(b"old bytes")
    before = path.stat()
    replacement = tmp_path / "replacement"
    replacement.write_bytes(b"new bytes")
    os.utime(replacement, ns=(before.st_atime_ns, before.st_mtime_ns))
    mutate_after_read(monkeypatch, lambda: os.replace(replacement, path))
    with pytest.raises(IntegrityFailure):
        hashing.sha256_file(path)


def test_same_inode_rewrite_with_restored_mtime_is_rejected(tmp_path, monkeypatch):
    path = tmp_path / "asset"
    path.write_bytes(b"old bytes")
    before = path.stat()
    def rewrite():
        path.write_bytes(b"new bytes")
        os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
    mutate_after_read(monkeypatch, rewrite)
    with pytest.raises(IntegrityFailure):
        hashing.sha256_file(path)


@pytest.mark.parametrize("action", ["delete", "truncate", "grow"])
def test_changes_during_read_are_rejected(tmp_path, monkeypatch, action):
    path = tmp_path / "asset"
    path.write_bytes(b"abcdefgh")
    def change():
        if action == "delete":
            path.unlink()
        else:
            path.write_bytes(b"a" if action == "truncate" else b"x" * 32)
    mutate_after_read(monkeypatch, change)
    with pytest.raises(IntegrityFailure):
        hashing.sha256_file(path, chunk_size=2)


@pytest.mark.parametrize("chunk_size", [0, -1, True, 1.5, "2"])
def test_invalid_chunk_size_fails_before_open(tmp_path, chunk_size):
    with pytest.raises(ValueError):
        hashing.sha256_file(tmp_path / "absent", chunk_size=chunk_size)


def test_nonregular_inputs_are_rejected(tmp_path):
    target = tmp_path / "regular"
    target.write_bytes(b"payload")
    link = tmp_path / "link"
    link.symlink_to(target)
    fifo = tmp_path / "fifo"
    os.mkfifo(fifo)
    for path in (tmp_path, link, fifo):
        with pytest.raises(IntegrityFailure):
            hashing.sha256_file(path)


def test_empty_and_multichunk_hashes_match_standard_sha256(tmp_path):
    for payload in (b"", b"abc" * 1000):
        path = tmp_path / "asset"
        path.write_bytes(payload)
        assert hashing.sha256_file(path, chunk_size=7) == hashlib.sha256(payload).hexdigest()
