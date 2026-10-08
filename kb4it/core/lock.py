#!/usr/bin/env python

"""
Cross-platform exclusive file lock.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3

POSIX uses flock() on the whole file. Windows uses msvcrt.locking() on one
byte far past the PID text, because Windows locks are mandatory and a lock on
the PID bytes would stop the busy-lock message from reading them. Both
mechanisms release the lock when the process ends, even after a crash.
"""

import os
import sys

from kb4it.core.exceptions import LockBusyError

# Offset of the byte locked on Windows; any offset past the PID text works.
_WINDOWS_LOCK_OFFSET = 1 << 20


class _PosixBackend:
    def lock(self, fd):
        import fcntl
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def unlock(self, fd):
        import fcntl
        fcntl.flock(fd, fcntl.LOCK_UN)


class _WindowsBackend:
    def lock(self, fd):
        import msvcrt
        os.lseek(fd, _WINDOWS_LOCK_OFFSET, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)

    def unlock(self, fd):
        import msvcrt
        os.lseek(fd, _WINDOWS_LOCK_OFFSET, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)


def backend_for(platform=None):
    """Lock backend for a sys.platform value (the running one by default)."""
    platform = sys.platform if platform is None else platform
    return _WindowsBackend() if platform == "win32" else _PosixBackend()


def read_holder(path):
    """PID written by the holder of the lock at path, or None."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read(32).strip()
    except OSError:
        return None
    return int(text) if text.isdigit() else None


class FileLock:
    """Exclusive, non-blocking lock on a file; usable as a context manager."""

    def __init__(self, path, backend=None):
        self.path = str(path)
        self.backend = backend or backend_for()
        self._fd = None

    @property
    def held(self) -> bool:
        return self._fd is not None

    def acquire(self):
        """Take the lock or raise LockBusyError naming the holder's PID."""
        if self._fd is not None:
            return self
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        # O_RDWR|O_CREAT never truncates, so a busy lock keeps the holder's PID readable.
        fd = os.open(self.path, os.O_RDWR | os.O_CREAT, 0o644)
        try:
            self.backend.lock(fd)
        except OSError:
            os.close(fd)
            raise LockBusyError(self.path, read_holder(self.path)) from None
        os.lseek(fd, 0, os.SEEK_SET)
        os.ftruncate(fd, 0)
        os.write(fd, str(os.getpid()).encode("ascii"))
        self._fd = fd
        return self

    def release(self):
        """Release the lock; harmless when it is not held."""
        if self._fd is None:
            return
        fd, self._fd = self._fd, None
        try:
            self.backend.unlock(fd)
        except OSError:
            pass
        finally:
            os.close(fd)

    def __enter__(self):
        return self.acquire()

    def __exit__(self, *exc):
        self.release()
        return False
