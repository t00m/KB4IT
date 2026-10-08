#!/usr/bin/python

"""
Log module.

File: log.py
Author: Tomás Vírseda
License: GPL v3
"""

import logging

_PATTERN = ("%(levelname)10s | %(lineno)4d | %(name)-15s | %(message)s")
_DATEFMT = "%d/%m/%Y %H:%M:%S"


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
