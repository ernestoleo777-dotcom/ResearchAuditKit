# SPDX-License-Identifier: Apache-2.0
"""Descriptor-confined, bounded local observations; never hydrate or execute inputs."""
from __future__ import annotations

from contextlib import contextmanager
import ctypes
import errno
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import stat
import sys
import uuid

DATALESS = 0x40000000


class EvidenceError(Exception):
    def __init__(self, code: str, severity: str = "INVALID"):
        self.code = code
        self.severity = severity
        super().__init__(code)


def relative_path(value: object) -> str:
    if (not isinstance(value, str) or not value or len(value) > 4096
            or value.startswith("/") or PureWindowsPath(value).drive
            or "\\" in value or any(ord(c) < 32 or ord(c) == 127 for c in value)
            or any(p in ("", ".", "..") for p in value.split("/"))):
        raise EvidenceError("UNSAFE_PATH")
    return value


def signature(s: os.stat_result) -> tuple:
    return (s.st_dev, s.st_ino, s.st_mode, s.st_nlink, s.st_size,
            s.st_mtime_ns, s.st_ctime_ns, getattr(s, "st_flags", 0))


def _open_absolute(path: Path) -> int:
    fd = os.open(path.anchor, os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:]:
            new = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = new
        return fd
    except BaseException:
        os.close(fd)
        raise


@contextmanager
def no_download():
    """Darwin materialization policy is thread-scoped; restore the previous value."""
    lib = None
    old = None
    if sys.platform == "darwin":
        lib = ctypes.CDLL("/usr/lib/libSystem.B.dylib", use_errno=True)
        lib.getiopolicy_np.argtypes = [ctypes.c_int, ctypes.c_int]
        lib.setiopolicy_np.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
        old = lib.getiopolicy_np(3, 1)
        if old < 0:
            raise EvidenceError("NO_DOWNLOAD_GUARD_UNAVAILABLE", "UNRESOLVED")
        try:
            if lib.setiopolicy_np(3, 1, 1) != 0 or lib.getiopolicy_np(3, 1) != 1:
                raise EvidenceError("NO_DOWNLOAD_GUARD_UNAVAILABLE", "UNRESOLVED")
        except BaseException:
            lib.setiopolicy_np(3, 1, old)
            raise
    try:
        yield
    finally:
        if lib is not None and old is not None:
            if lib.setiopolicy_np(3, 1, old) != 0 or lib.getiopolicy_np(3, 1) != old:
                raise EvidenceError("NO_DOWNLOAD_RESTORE_FAILED", "UNRESOLVED")


class Root:
    def __init__(self, path: str | Path):
        self.path = Path(os.path.abspath(path))
        try:
            self.fd = _open_absolute(self.path)
        except OSError as exc:
            raise EvidenceError("ROOT_UNAVAILABLE_OR_SYMLINK") from exc
        s = os.fstat(self.fd)
        self.identity = (s.st_dev, s.st_ino)

    def close(self):
        os.close(self.fd)

    def check_root(self):
        try:
            fd = _open_absolute(self.path)
            try:
                s = os.fstat(fd)
                if (s.st_dev, s.st_ino) != self.identity:
                    raise EvidenceError("ROOT_CHANGED")
            finally:
                os.close(fd)
        except OSError as exc:
            raise EvidenceError("PATH_RACE_OR_SYMLINK") from exc

    @contextmanager
    def parent(self, rel: str):
        parts = relative_path(rel).split("/")
        self.check_root()
        fd = os.dup(self.fd)
        try:
            for part in parts[:-1]:
                new = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd)
                fd = new
                if os.fstat(fd).st_dev != self.identity[0]:
                    raise EvidenceError("MOUNT_ESCAPE")
            yield fd, parts[-1]
        finally:
            os.close(fd)

    def anchored(self, rel: str, fd: int):
        with self.parent(rel) as (fresh, _):
            a, b = os.fstat(fresh), os.fstat(fd)
            if (a.st_dev, a.st_ino) != (b.st_dev, b.st_ino):
                raise EvidenceError("PARENT_CHANGED")

    def read(self, rel: str, limit: int, *, keep_bytes: bool = False,
             budget: dict | None = None) -> dict:
        try:
            with self.parent(rel) as (pfd, leaf):
                before = os.stat(leaf, dir_fd=pfd, follow_symlinks=False)
                if before.st_dev != self.identity[0]:
                    raise EvidenceError("MOUNT_ESCAPE")
                if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
                    raise EvidenceError("SYMLINK_OR_NONREGULAR_ARTIFACT")
                if getattr(before, "st_flags", 0) & DATALESS:
                    raise EvidenceError("NOT_LOCAL", "UNRESOLVED")
                if not before.st_mode & 0o444:
                    raise EvidenceError("UNREADABLE", "UNRESOLVED")
                if before.st_size > limit:
                    raise EvidenceError("ARTIFACT_BUDGET_EXCEEDED", "UNRESOLVED")
                fd = os.open(leaf, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=pfd)
                try:
                    if signature(os.fstat(fd)) != signature(before):
                        raise EvidenceError("VERSION_DRIFT")
                    self.anchored(rel, pfd)
                    h = hashlib.sha256()
                    count = 0
                    chunks = []
                    while count < before.st_size:
                        amount = min(65536, before.st_size - count, limit - count)
                        if budget is not None:
                            amount = min(amount, budget["remaining"])
                            if amount <= 0:
                                raise EvidenceError("TOTAL_ARTIFACT_BUDGET_EXCEEDED", "UNRESOLVED")
                        chunk = os.read(fd, amount)
                        if budget is not None:
                            # Debit actual I/O even if subsequent identity checks fail.
                            budget["remaining"] -= len(chunk)
                        if not chunk:
                            break
                        count += len(chunk)
                        h.update(chunk)
                        if keep_bytes:
                            chunks.append(chunk)
                    self.anchored(rel, pfd)
                    after = os.stat(leaf, dir_fd=pfd, follow_symlinks=False)
                    if (signature(after) != signature(before)
                            or signature(os.fstat(fd)) != signature(before)
                            or count != before.st_size):
                        raise EvidenceError("VERSION_DRIFT")
                    result = {"sha256": h.hexdigest(), "bytes": count, "stable_read": True}
                    if keep_bytes:
                        result["data"] = b"".join(chunks)
                    return result
                finally:
                    os.close(fd)
        except EvidenceError:
            raise
        except FileNotFoundError as exc:
            raise EvidenceError("MISSING", "UNRESOLVED") from exc
        except PermissionError as exc:
            raise EvidenceError("UNREADABLE", "UNRESOLVED") from exc
        except OSError as exc:
            code = "PATH_RACE_OR_SYMLINK" if exc.errno in (errno.ELOOP, errno.ENOTDIR) else "UNREADABLE"
            raise EvidenceError(code, "INVALID" if code != "UNREADABLE" else "UNRESOLVED") from exc

    def output_relative(self, output: str | Path, protected: set[str]) -> str:
        raw = str(output)
        if Path(raw).is_absolute():
            try:
                raw = str(Path(raw).relative_to(self.path))
            except ValueError as exc:
                raise EvidenceError("OUTPUT_OUTSIDE_ROOT") from exc
        rel = relative_path(raw)
        if rel in protected:
            raise EvidenceError("OUTPUT_ALIASES_INPUT")
        try:
            with self.parent(rel) as (fd, leaf):
                try:
                    os.stat(leaf, dir_fd=fd, follow_symlinks=False)
                except FileNotFoundError:
                    return rel
                raise EvidenceError("OUTPUT_ALREADY_EXISTS")
        except OSError as exc:
            raise EvidenceError("OUTPUT_PARENT_UNAVAILABLE_OR_SYMLINK") from exc

    def publish(self, rel: str, result: dict):
        """Publish a complete new report exclusively; never replace an existing path."""
        payload = (json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()
        with self.parent(rel) as (pfd, leaf):
            temporary = ".rak-evidence-" + uuid.uuid4().hex + ".tmp"
            fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600, dir_fd=pfd)
            identity = os.fstat(fd).st_ino
            published = False
            try:
                view = memoryview(payload)
                while view:
                    n = os.write(fd, view)
                    if n <= 0:
                        raise EvidenceError("OUTPUT_WRITE_FAILED")
                    view = view[n:]
                os.fsync(fd)
                self.anchored(rel, pfd)
                try:
                    os.link(temporary, leaf, src_dir_fd=pfd, dst_dir_fd=pfd, follow_symlinks=False)
                except FileExistsError as exc:
                    raise EvidenceError("OUTPUT_ALREADY_EXISTS") from exc
                published = True
                self.anchored(rel, pfd)
                os.fsync(pfd)
            except BaseException:
                # Only remove this call's newly created output if a publication race occurred.
                if published and os.stat(leaf, dir_fd=pfd, follow_symlinks=False).st_ino == identity:
                    os.unlink(leaf, dir_fd=pfd)
                raise
            finally:
                os.close(fd)
                if os.stat(temporary, dir_fd=pfd, follow_symlinks=False).st_ino == identity:
                    os.unlink(temporary, dir_fd=pfd)
                os.fsync(pfd)
