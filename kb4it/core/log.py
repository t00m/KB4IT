#!/usr/bin/python

"""
Log module.

File: log.py
Author: Tomás Vírseda
License: GPL v3
"""

import logging
import os
import re
import time

_PATTERN = ("%(levelname)10s | %(lineno)4d | %(name)-15s | %(message)s")
_DATEFMT = "%d/%m/%Y %H:%M:%S"

# Each run logs to <KB4IT_HOME>/var/log/kb4it.log.<uuid1 time> until it knows its repository.
# A run that ends normally removes its own file; this age limit sweeps the ones crashes and
# failed runs leave behind. Files written recently may belong to a run still going on.
TEMP_LOG_MAX_AGE_DAYS = 7
_TEMP_LOG_NAME = re.compile(r"^kb4it\.log\.\d+$")


def setup_logging(level: str = "INFO", logfile: str | None = None):
    """Configure root logger once."""
    if level is not None:
        level_dict = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        severity = level_dict.get(level, logging.DEBUG)
    else:
        severity = logging.INFO

    root = logging.getLogger()
    root.setLevel(severity)

    if any(isinstance(h, logging.FileHandler) for h in root.handlers):
        return  # File handler already configured

    formatter = logging.Formatter(_PATTERN, datefmt=_DATEFMT)

    # Console handler
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    console.setLevel(severity)
    root.addHandler(console)

    # File handler
    file_handler = logging.FileHandler(logfile, mode="w", encoding="utf-8")
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)


def reset_logging():
    """Remove every root handler, so the next KB4IT instance in this process sets up logging from scratch.

    setup_logging() returns early while a file handler exists; the TUI and kb4it serve
    build several times in one process and call this before each build.
    """
    root = logging.getLogger()
    for handler in list(root.handlers):
        try:
            handler.flush()
            handler.close()
        except Exception:
            pass
        root.removeHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger."""
    return logging.getLogger(name)


def release_log_file(logfile: str):
    """Close the file handlers still writing to logfile, so it can be moved or removed.

    A second build in the same process finds the handler of the first one open on
    var/log/kb4it.log, and Windows does not remove an open file.
    """
    target = os.path.abspath(logfile)
    root = logging.getLogger()
    for handler in root.handlers[:]:
        if isinstance(handler, logging.FileHandler) and os.path.abspath(handler.baseFilename) == target:
            handler.flush()
            handler.close()
            root.removeHandler(handler)


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
    """Redirect logging to a new file at runtime."""
    root = logging.getLogger()
    formatter = logging.Formatter(_PATTERN, datefmt=_DATEFMT)

    # Remove only existing FileHandlers
    for handler in root.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            handler.flush()
            handler.close()
            root.removeHandler(handler)

    # Add new file handler
    file_handler = logging.FileHandler(logfile, mode="a", encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    root.addHandler(file_handler)
