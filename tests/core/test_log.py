"""Logging: the kb4it logger tree, the line format, tracebacks, and the log files under KB4IT_HOME and the repository."""

import logging
import os
import re
import threading

import pytest

from kb4it.core.log import (current_log_file, discard_log_file, get_logger, kb4it_logger, prune_temp_logs, q,
                            release_log_file, reset_logging, rotate_log, setup_logging)
from tests.helpers import mini_theme, page, run_kb4it, write_repo

DAY = 86400


def test_release_log_file_closes_only_its_handlers(tmp_path):
    root = kb4it_logger()
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
    root = kb4it_logger()
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


@pytest.fixture
def configured(tmp_path, capsys):
    """Start setup_logging() at DEBUG into tmp_path/kb4it.log; returns a reader for the file and the console.

    Call it in the test body: the console handler keeps the stderr of the phase it was made in.
    """
    logfile = tmp_path / "kb4it.log"

    def start():
        reset_logging()
        setup_logging("DEBUG", str(logfile))

        def read():
            for handler in kb4it_logger().handlers:
                handler.flush()
            return logfile.read_text(encoding="utf-8"), capsys.readouterr().err
        return read
    try:
        yield start
    finally:
        reset_logging()


def test_get_logger_puts_every_logger_under_kb4it():
    assert get_logger("Backend").name == "kb4it.Backend"
    assert get_logger("kb4it.core.serve").name == "kb4it.core.serve"
    assert get_logger("kb4it").name == "kb4it"


@pytest.mark.parametrize("value, expected", [
    ("SAP-NOTE.md", "SAP-NOTE.md"),
    (42, "42"),
    ("SAP Basis", '"SAP Basis"'),
    ("", '""'),
    ('say "hi"', '"say \\"hi\\""'),
    ("a=b", '"a=b"'),
    ("two\nlines", '"two\\nlines"'),
])
def test_q_quotes_values_that_would_break_key_value_parsing(value, expected):
    assert q(value) == expected


def test_root_logger_is_left_to_the_caller(configured):
    read = configured()
    root = logging.getLogger()
    before = list(root.handlers)
    get_logger("Backend").info("[BACKEND] HELLO")
    assert root.handlers == before
    assert kb4it_logger().propagate is False
    text, _ = read()
    assert "[BACKEND] HELLO" in text


def test_line_names_thread_logger_and_place(configured):
    read = configured()
    get_logger("Backend").info("[BACKEND] MAIN_LINE")
    worker = threading.Thread(target=lambda: get_logger("Compiler").info("[COMPILER] WORKER_LINE"), name="compile_3")
    worker.start()
    worker.join()
    text, _ = read()
    main_line = next(line for line in text.splitlines() if "MAIN_LINE" in line)
    worker_line = next(line for line in text.splitlines() if "WORKER_LINE" in line)
    assert "| MainThread   | Backend         | test_log:" in main_line
    assert "| compile_3    | Compiler" in worker_line
    assert "kb4it.Backend" not in main_line


def test_library_debug_stays_out_and_warnings_come_in(configured):
    read = configured()
    markdown, pil = logging.getLogger("MARKDOWN"), logging.getLogger("PIL.PngImagePlugin")
    old = markdown.level, logging.getLogger().level
    markdown.setLevel(logging.DEBUG)
    logging.getLogger().setLevel(logging.DEBUG)  # as a caller that logs everything would
    try:
        markdown.debug('Successfully loaded extension "markdown.extensions.toc.TocExtension".')
        pil.debug("STREAM b'IHDR' 16 13")
        markdown.warning("Unknown extension option")
    finally:
        markdown.setLevel(old[0])
        logging.getLogger().setLevel(old[1])
    text, console = read()
    assert "Successfully loaded extension" not in text
    assert "STREAM" not in text
    assert "MARKDOWN" in text and "Unknown extension option" in text
    assert "Unknown extension option" in console


def test_traceback_goes_to_the_file_and_not_the_console(configured):
    read = configured()
    try:
        {}["Date"]
    except KeyError:
        get_logger("Compiler").error("[COMPILER] ERROR doc=a.md error=Date", exc_info=True)
    text, console = read()
    assert "Traceback (most recent call last)" in text
    assert "KeyError: 'Date'" in text
    assert "[COMPILER] ERROR doc=a.md error=Date" in console
    assert "Traceback" not in console


def test_file_only_records_stay_off_the_console(configured):
    read = configured()
    get_logger("KB4IT").error("[CONTROLLER] UNEXPECTED_ERROR type=KeyError", extra={"file_only": True})
    text, console = read()
    assert "UNEXPECTED_ERROR" in text
    assert "UNEXPECTED_ERROR" not in console


def test_reset_detaches_from_the_libraries_too(configured):
    read = configured()
    reset_logging()
    assert kb4it_logger().handlers == []
    assert logging.getLogger("MARKDOWN").handlers == []
    assert kb4it_logger().propagate is True


def test_unexpected_error_keeps_one_screen_line_and_logs_the_traceback(monkeypatch, capsys):
    import sys
    from pathlib import Path

    from kb4it.core import main as main_module
    from kb4it.core.env import ENV

    def boom(self):
        raise RuntimeError("boom in run")
    monkeypatch.setattr(main_module.KB4IT, "run", boom)
    monkeypatch.setattr(sys, "argv", ["kb4it", "themes"])
    monkeypatch.setenv("CI", "1")  # no help notice
    folder = Path(ENV["LPATH"]["LOG"])
    before = set(folder.glob("kb4it.log.*")) if folder.exists() else set()
    reset_logging()
    try:
        with pytest.raises(SystemExit) as exit_info:
            main_module.main()
        for handler in kb4it_logger().handlers:
            handler.flush()
    finally:
        reset_logging()
    assert exit_info.value.code == 1
    out, err = capsys.readouterr()
    assert "Error: RuntimeError: boom in run" in out
    assert "Traceback" not in out + err
    assert "UNEXPECTED_ERROR" not in out + err
    (log,) = set(folder.glob("kb4it.log.*")) - before
    text = log.read_text(encoding="utf-8")
    assert '[CONTROLLER] UNEXPECTED_ERROR type=RuntimeError reason="boom in run"' in text
    assert "Traceback (most recent call last)" in text
    log.unlink()


def test_file_lines_start_with_the_time_and_the_console_lines_do_not(configured):
    read = configured()
    get_logger("Backend").info("[BACKEND] TIMED")
    text, console = read()
    file_line = next(line for line in text.splitlines() if "TIMED" in line)
    console_line = next(line for line in console.splitlines() if "TIMED" in line)
    assert re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} \|       INFO \| ", file_line)
    assert console_line.startswith("      INFO | ")


def test_the_file_gets_debug_lines_at_any_console_level(tmp_path, capsys):
    logfile = tmp_path / "kb4it.log"
    reset_logging()
    try:
        setup_logging("WARNING", str(logfile))
        get_logger("Backend").debug("[BACKEND] QUIET_STEP")
        get_logger("Backend").warning("[BACKEND] LOUD_STEP")
        for handler in kb4it_logger().handlers:
            handler.flush()
    finally:
        reset_logging()
    text = logfile.read_text(encoding="utf-8")
    console = capsys.readouterr().err
    assert "QUIET_STEP" in text and "LOUD_STEP" in text
    assert "QUIET_STEP" not in console and "LOUD_STEP" in console


def test_an_unknown_level_warns_and_uses_info(tmp_path, capsys):
    logfile = tmp_path / "kb4it.log"
    reset_logging()
    try:
        setup_logging("VERBOSE", str(logfile))
        get_logger("Backend").debug("[BACKEND] HIDDEN_ON_CONSOLE")
        for handler in kb4it_logger().handlers:
            handler.flush()
    finally:
        reset_logging()
    console = capsys.readouterr().err
    assert "[LOG] LEVEL_UNKNOWN level=VERBOSE used=INFO" in console
    assert "HIDDEN_ON_CONSOLE" not in console
    assert "HIDDEN_ON_CONSOLE" in logfile.read_text(encoding="utf-8")


def test_current_log_file_names_the_file_in_use(configured):
    configured()
    (handler,) = [h for h in kb4it_logger().handlers if isinstance(h, logging.FileHandler)]
    assert current_log_file() == handler.baseFilename
    reset_logging()
    assert current_log_file() is None


def test_rotate_keeps_the_last_builds(tmp_path):
    log = tmp_path / "kb4it.log"
    for build in range(1, 6):
        rotate_log(str(log), keep=3)
        log.write_text(f"build {build}", encoding="utf-8")
    assert log.read_text(encoding="utf-8") == "build 5"
    assert (tmp_path / "kb4it.log.old").read_text(encoding="utf-8") == "build 4"
    assert (tmp_path / "kb4it.log.old.2").read_text(encoding="utf-8") == "build 3"
    assert (tmp_path / "kb4it.log.old.3").read_text(encoding="utf-8") == "build 2"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["kb4it.log", "kb4it.log.old", "kb4it.log.old.2",
                                                          "kb4it.log.old.3"]


def test_rotate_without_a_log_does_nothing(tmp_path):
    rotate_log(str(tmp_path / "kb4it.log"))
    assert list(tmp_path.iterdir()) == []


def test_a_failed_build_names_its_log(tmp_path, home):
    theme = mini_theme(tmp_path / "mini")
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "mini", {"a.md": page("A", Tag="x")}, theme_path=str(theme))
    assert run_kb4it("build", cfg, cwd=repo, home=home).returncode == 0
    (repo / "source").rename(repo / "gone")
    result = run_kb4it("build", cfg, cwd=repo, home=home)
    assert result.returncode == 1
    assert f"Log: {repo / 'var' / 'log' / 'kb4it.log'}" in result.stdout


def test_a_command_failing_before_the_repository_names_its_temporary_log(tmp_path, home):
    result = run_kb4it("build", tmp_path / "nope" / "repo.json", cwd=tmp_path, home=home)
    assert result.returncode == 1
    (log,) = _temp_logs(home)
    assert f"Log: {home / '.kb4it' / 'var' / 'log' / log}" in result.stdout


def test_builds_keep_their_earlier_logs_and_one_line_per_document(tmp_path, home):
    theme = mini_theme(tmp_path / "mini")
    repo = tmp_path / "repo"
    cfg = write_repo(repo, "mini", {"a.md": page("A", Tag="x, y", Team="SAP Basis")}, theme_path=str(theme))
    for _ in range(3):
        assert run_kb4it("build", cfg, cwd=repo, home=home).returncode == 0
    logs = repo / "var" / "log"
    assert (logs / "kb4it.log.old").exists() and (logs / "kb4it.log.old.2").exists()
    text = (logs / "kb4it.log").read_text(encoding="utf-8")
    assert "KV_ADD" not in text
    assert re.search(r"\[DATABASE\] DOC_KEYS doc=a\.md keys=\d+ values=\d+", text)


def test_the_hint_ignores_a_log_another_run_still_holds(tmp_path):
    import argparse

    from kb4it.core.main import _log_of_run
    own = tmp_path / "repo" / "var" / "log" / "kb4it.log"
    own.parent.mkdir(parents=True)
    own.write_text("", encoding="utf-8")
    other = tmp_path / "other.log"
    stale = logging.FileHandler(other, encoding="utf-8")
    kb4it_logger().addHandler(stale)
    try:
        params = argparse.Namespace(config=str(tmp_path / "repo" / "config" / "repo.json"))
        assert _log_of_run(params) == str(own)
    finally:
        kb4it_logger().removeHandler(stale)
        stale.close()
