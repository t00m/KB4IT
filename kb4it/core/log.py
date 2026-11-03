#!/usr/bin/python

"""
Log module.

KB4IT logs through its own logger tree, "kb4it", and never configures the root logger:
a program that runs KB4IT in its own process (the TUI, kb4it serve, a Python caller)
keeps its logging as it set it up. The libraries KB4IT drives log under their own
names; their warnings and errors reach the KB4IT log, their debug lines do not.

File: log.py
Author: Tomás Vírseda
License: GPL v3
"""

import logging
import os
import re
import time

_PATTERN = "%(levelname)10s | %(threadName)-12s | %(shortname)-15s | %(module)s:%(lineno)d | %(message)s"
# The file has the time of each line in front; the console, read as it happens, does not.
_FILE_PATTERN = "%(asctime)s | " + _PATTERN
_DATEFMT = "%Y-%m-%d %H:%M:%S"
LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}
# Logs of earlier builds kept beside <repo>/var/log/kb4it.log: kb4it.log.old, kb4it.log.old.2...
LOG_KEEP = 3

# Parent of every KB4IT logger; get_logger("Backend") is "kb4it.Backend".
KB4IT_LOGGER = "kb4it"
# Libraries whose own loggers are noisy at DEBUG: Python-Markdown logs every extension it
# loads, three lines per page, and Pillow logs the chunks of every PNG.
LIBRARY_LOGGERS = ("MARKDOWN", "PIL")
LIBRARY_LEVEL = logging.WARNING

# Each run logs to <KB4IT_HOME>/var/log/kb4it.log.<uuid1 time> until it knows its repository.
# A run that ends normally removes its own file; this age limit sweeps the ones crashes and
# failed runs leave behind. Files written recently may belong to a run still going on.
TEMP_LOG_MAX_AGE_DAYS = 7
_TEMP_LOG_NAME = re.compile(r"^kb4it\.log\.\d+$")


def q(value) -> str:
    """value as text for a key=value detail, in double quotes when it has spaces, quotes or '='."""
    text = str(value)
    if text and not any(char.isspace() or char in '"=' for char in text):
        return text
    escaped = text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")
    return f'"{escaped}"'


class _Formatter(logging.Formatter):
    """The KB4IT line format; with tracebacks=False, an error stays on one line."""

    def __init__(self, tracebacks: bool = True, timestamps: bool = False):
        super().__init__(_FILE_PATTERN if timestamps else _PATTERN, datefmt=_DATEFMT)
        self.tracebacks = tracebacks

    def format(self, record: logging.LogRecord) -> str:
        name = record.name
        record.shortname = name[len(KB4IT_LOGGER) + 1:] if name.startswith(KB4IT_LOGGER + ".") else name
        if self.tracebacks:
            return super().format(record)
        # Another handler may already have cached the traceback text on the record.
        saved = record.exc_info, record.exc_text, record.stack_info
        record.exc_info = record.exc_text = record.stack_info = None
        try:
            return super().format(record)
        finally:
            record.exc_info, record.exc_text, record.stack_info = saved


def _not_file_only(record: logging.LogRecord) -> bool:
    """Keep off the console the records logged with extra={"file_only": True}."""
    return not getattr(record, "file_only", False)


class _LibraryFilter(logging.Filter):
    """Let KB4IT's own records through, and only warnings and errors of the libraries."""

    def filter(self, record: logging.LogRecord) -> bool:
        name = record.name
        return name == KB4IT_LOGGER or name.startswith(KB4IT_LOGGER + ".") or record.levelno >= LIBRARY_LEVEL


def kb4it_logger() -> logging.Logger:
    """The parent of every KB4IT logger; add a handler here to see all of KB4IT's records."""
    return logging.getLogger(KB4IT_LOGGER)


def _loggers() -> list[logging.Logger]:
    """The loggers that carry KB4IT's handlers: its own tree and the libraries it drives."""
    return [kb4it_logger()] + [logging.getLogger(name) for name in LIBRARY_LOGGERS]


def _attach(handler: logging.Handler) -> None:
    handler.addFilter(_LibraryFilter())
    for logger in _loggers():
        logger.addHandler(handler)


def _detach(handler: logging.Handler) -> None:
    for logger in _loggers():
        logger.removeHandler(handler)


def _file_handler(logfile: str, mode: str) -> logging.FileHandler:
    handler = logging.FileHandler(logfile, mode=mode, encoding="utf-8")
    handler.setFormatter(_Formatter(tracebacks=True, timestamps=True))
    handler.setLevel(logging.DEBUG)
    return handler


def setup_logging(level: str = "INFO", logfile: str | None = None):
    """Configure the kb4it logger once: the console at level, the file at DEBUG when logfile is given."""
    unknown = level is not None and str(level).upper() not in LEVELS
    severity = LEVELS.get(str(level).upper(), logging.INFO) if level is not None else logging.INFO

    logger = kb4it_logger()
    # The file always gets every line; the console shows the level asked for.
    logger.setLevel(logging.DEBUG if logfile else severity)
    # KB4IT's records go to its own handlers only; the root logger belongs to the caller.
    logger.propagate = False

    if any(isinstance(h, logging.FileHandler) for h in logger.handlers):
        return  # File handler already configured

    # The console keeps an error on one line; the file holds its traceback.
    console = logging.StreamHandler()
    console.setFormatter(_Formatter(tracebacks=False))
    console.setLevel(severity)
    console.addFilter(_not_file_only)
    _attach(console)

    if logfile:
        _attach(_file_handler(logfile, "w"))
    if unknown:
        get_logger("Log").warning(f"[LOG] LEVEL_UNKNOWN level={q(level)} used=INFO")


def current_log_file() -> str | None:
    """Path of the file KB4IT logs to now, or None when it logs to no file."""
    for handler in kb4it_logger().handlers:
        if isinstance(handler, logging.FileHandler):
            return handler.baseFilename
    return None


def rotate_log(logfile: str, keep: int = LOG_KEEP) -> None:
    """Move logfile to logfile.old, and the older ones up to logfile.old.<keep>; the oldest goes."""
    names = [f"{logfile}.old"] + [f"{logfile}.old.{n}" for n in range(2, keep + 1)]
    if not names or not os.path.exists(logfile):
        return
    try:
        if os.path.exists(names[-1]):
            os.remove(names[-1])
        for newer, older in reversed(list(zip(names, names[1:]))):
            if os.path.exists(newer):
                os.replace(newer, older)
        os.replace(logfile, names[0])
    except OSError as error:
        get_logger("Log").warning(f"[LOG] ROTATE_FAIL path={q(logfile)} reason={q(error)}")


def reset_logging():
    """Remove KB4IT's handlers, so the next KB4IT instance in this process sets up logging from scratch.

    setup_logging() returns early while a file handler exists; the TUI and kb4it serve
    build several times in one process and call this before each build.
    """
    for handler in list(kb4it_logger().handlers):
        try:
            handler.flush()
            handler.close()
        except Exception:
            pass
        _detach(handler)
    kb4it_logger().propagate = True


def get_logger(name: str) -> logging.Logger:
    """Return the KB4IT logger called name, under the kb4it logger."""
    if name == KB4IT_LOGGER or name.startswith(KB4IT_LOGGER + "."):
        return logging.getLogger(name)
    return logging.getLogger(f"{KB4IT_LOGGER}.{name}")


def release_log_file(logfile: str):
    """Close the file handlers still writing to logfile, so it can be moved or removed.

    A second build in the same process finds the handler of the first one open on
    var/log/kb4it.log, and Windows does not remove an open file.
    """
    target = os.path.abspath(logfile)
    for handler in kb4it_logger().handlers[:]:
        if isinstance(handler, logging.FileHandler) and os.path.abspath(handler.baseFilename) == target:
            handler.flush()
            handler.close()
            _detach(handler)


def discard_log_file(logfile: str) -> bool:
    """Close the handlers writing to logfile and remove it; True when it was removed."""
    release_log_file(logfile)
    try:
        os.remove(logfile)
    except FileNotFoundError:
        return False
    except OSError:
        return False  # Still open in another process on Windows; prune_temp_logs takes it later.
    return True


def prune_temp_logs(folder: str, max_age_days: float = TEMP_LOG_MAX_AGE_DAYS, now: float | None = None) -> int:
    """Remove the temporary run logs in folder not written for max_age_days; return how many went."""
    limit = (time.time() if now is None else now) - max_age_days * 86400
    removed = 0
    try:
        entries = list(os.scandir(folder))
    except OSError:
        return 0
    for entry in entries:
        if not _TEMP_LOG_NAME.match(entry.name):
            continue
        try:
            if entry.is_file(follow_symlinks=False) and entry.stat().st_mtime < limit:
                os.remove(entry.path)
                removed += 1
        except OSError:
            continue
    return removed


def redirect_logs(logfile: str):
    """Send the file log to logfile from now on, appending to it."""
    for handler in kb4it_logger().handlers[:]:
        if isinstance(handler, logging.FileHandler):
            handler.flush()
            handler.close()
            _detach(handler)
    _attach(_file_handler(logfile, "a"))
