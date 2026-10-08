"""The file lock works the same on every platform and names the process that holds it."""

import os
import subprocess
import sys
import types

import pytest

from kb4it.core import lock as lockmod
from kb4it.core.exceptions import LockBusyError
from kb4it.core.lock import FileLock
from tests.helpers import ROOT


def test_second_lock_on_the_same_file_is_refused(tmp_path):
    path = tmp_path / "var" / "kb4it.lock"
    with FileLock(path):
        with pytest.raises(LockBusyError) as busy:
            FileLock(path).acquire()
    assert busy.value.pid == os.getpid()
    assert str(os.getpid()) in str(busy.value)


def test_lock_is_free_again_after_release(tmp_path):
    path = tmp_path / "kb4it.lock"
    first = FileLock(path).acquire()
    first.release()
    assert not first.held
    with FileLock(path) as second:
        assert second.held


def test_lock_of_a_killed_process_can_be_taken(tmp_path):
    path = tmp_path / "kb4it.lock"
    code = ("import sys, time; from kb4it.core.lock import FileLock; FileLock(sys.argv[1]).acquire(); "
            "print('held', flush=True); time.sleep(60)")
    proc = subprocess.Popen([sys.executable, "-c", code, str(path)], stdout=subprocess.PIPE, text=True,
                            encoding="utf-8", env=dict(os.environ, PYTHONPATH=str(ROOT)))
    try:
        assert proc.stdout.readline().strip() == "held"
        with pytest.raises(LockBusyError) as busy:
            FileLock(path).acquire()
        assert busy.value.pid == proc.pid
    finally:
        proc.kill()
        proc.wait()
    with FileLock(path):
        pass


def test_windows_backend_locks_one_byte_past_the_pid(monkeypatch, tmp_path):
    calls = []
    fake = types.SimpleNamespace(LK_NBLCK=2, LK_UNLCK=0,
                                 locking=lambda fd, mode, size: calls.append((os.lseek(fd, 0, os.SEEK_CUR), mode, size)))
    monkeypatch.setitem(sys.modules, "msvcrt", fake)
    path = tmp_path / "kb4it.lock"
    with FileLock(path, backend=lockmod.backend_for("win32")):
        assert lockmod.read_holder(path) == os.getpid()
    assert calls[0] == (lockmod._WINDOWS_LOCK_OFFSET, fake.LK_NBLCK, 1)
    assert calls[-1][1] == fake.LK_UNLCK


def test_windows_backend_reports_a_busy_lock(monkeypatch, tmp_path):
    def locking(fd, mode, size):
        if mode == 2:
            raise PermissionError(13, "Permission denied")
    monkeypatch.setitem(sys.modules, "msvcrt", types.SimpleNamespace(LK_NBLCK=2, LK_UNLCK=0, locking=locking))
    path = tmp_path / "kb4it.lock"
    path.write_text("4242", encoding="utf-8")
    with pytest.raises(LockBusyError) as busy:
        FileLock(path, backend=lockmod.backend_for("win32")).acquire()
    assert busy.value.pid == 4242


def test_backend_choice():
    assert isinstance(lockmod.backend_for("win32"), lockmod._WindowsBackend)
    assert isinstance(lockmod.backend_for("linux"), lockmod._PosixBackend)
    assert isinstance(lockmod.backend_for("darwin"), lockmod._PosixBackend)


def test_registry_lock_waits_then_gives_up(tmp_path, monkeypatch):
    held = lockmod.registry_lock(timeout=0.2)
    with held:
        with pytest.raises(LockBusyError):
            with lockmod.registry_lock(timeout=0.2):
                pass
    with lockmod.registry_lock(timeout=0.2):
        pass


def test_lock_paths_per_action(tmp_path):
    from kb4it.core.main import lock_path_for
    cfg = tmp_path / "kb" / "config" / "repo.json"
    assert lock_path_for({"action": "build", "config": str(cfg)}) == str(tmp_path / "kb" / "var" / "kb4it.lock")
    assert lock_path_for({"action": "themes"}) is None
    assert lock_path_for({"action": "verify", "config": str(cfg)}) is None
    create = lock_path_for({"action": "create", "repo_path": str(tmp_path / "new")})
    assert not create.startswith(str(tmp_path / "new"))
