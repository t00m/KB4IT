"""Log files: the project log is rotated safely, and the temporary run logs under KB4IT_HOME do not pile up."""

import logging
import os

from kb4it.core.log import discard_log_file, prune_temp_logs, release_log_file
from tests.helpers import mini_theme, page, run_kb4it, write_repo

DAY = 86400


def test_release_log_file_closes_only_its_handlers(tmp_path):
    root = logging.getLogger()
    mine = logging.FileHandler(tmp_path / "kb4it.log", encoding="utf-8")
    other = logging.FileHandler(tmp_path / "other.log", encoding="utf-8")
    root.addHandler(mine)
    root.addHandler(other)
    try:
        release_log_file(tmp_path / "kb4it.log")
        assert mine not in root.handlers
        assert mine.stream is None
        assert other in root.handlers
        # Windows refuses to remove a file that a handler keeps open.
        (tmp_path / "kb4it.log").unlink()
    finally:
        for handler in (mine, other):
            handler.close()
            root.removeHandler(handler)


def _aged(path, days, now):
    path.write_text("x", encoding="utf-8")
    os.utime(path, (now - days * DAY, now - days * DAY))
    return path


def test_prune_removes_only_old_temporary_logs(tmp_path):
    now = 1_800_000_000
    old = _aged(tmp_path / "kb4it.log.139965290208298090", 8, now)
    fresh = _aged(tmp_path / "kb4it.log.140130277484113750", 1, now)
    # The project log, its rotation and other files under var/log are never temporary run logs.
    kept = [_aged(tmp_path / name, 30, now) for name in ("kb4it.log", "kb4it.log.old", "trace.json", "kb4it.log.abc")]
    assert prune_temp_logs(str(tmp_path), now=now) == 1
    assert not old.exists()
    assert fresh.exists()
    assert all(path.exists() for path in kept)


def test_prune_of_a_missing_folder_does_nothing(tmp_path):
    assert prune_temp_logs(str(tmp_path / "nope")) == 0


def test_discard_closes_the_handler_and_removes_the_file(tmp_path):
    logfile = tmp_path / "kb4it.log.1"
    root = logging.getLogger()
    handler = logging.FileHandler(logfile, encoding="utf-8")
    root.addHandler(handler)
    try:
        assert discard_log_file(str(logfile))
        assert handler not in root.handlers
        assert not logfile.exists()
        assert not discard_log_file(str(logfile))
    finally:
        handler.close()
        root.removeHandler(handler)


def _temp_logs(home):
    folder = home / ".kb4it" / "var" / "log"
    return sorted(p.name for p in folder.glob("kb4it.log.*")) if folder.exists() else []


def test_commands_leave_no_temporary_log(tmp_path, home):
    assert run_kb4it("themes", cwd=tmp_path, home=home).returncode == 0
    theme = mini_theme(tmp_path / "mini")
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "mini", {"a.md": page("A", Tag="x")}, theme_path=str(theme))
    assert run_kb4it("build", cfg, cwd=repo, home=home).returncode == 0
    # Nothing to compile: the build ends before the deploy step.
    assert run_kb4it("build", cfg, cwd=repo, home=home).returncode == 0
    assert _temp_logs(home) == []
    assert "[WORKFLOW] END" in (repo / "var" / "log" / "kb4it.log").read_text(encoding="utf-8")


def test_a_failed_command_keeps_its_temporary_log(tmp_path, home):
    result = run_kb4it("build", tmp_path / "nope" / "repo.json", cwd=tmp_path, home=home)
    assert result.returncode == 1
    logs = _temp_logs(home)
    assert len(logs) == 1
    text = (home / ".kb4it" / "var" / "log" / logs[0]).read_text(encoding="utf-8")
    assert "CONFIG_MISSING" in text


def test_old_temporary_logs_are_swept_at_start(tmp_path, home):
    folder = home / ".kb4it" / "var" / "log"
    folder.mkdir(parents=True)
    old = folder / "kb4it.log.139965290208298090"
    old.write_text("old run", encoding="utf-8")
    past = os.path.getmtime(old) - 30 * DAY
    os.utime(old, (past, past))
    assert run_kb4it("themes", cwd=tmp_path, home=home).returncode == 0
    assert not old.exists()
