#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Log module.
File: mod_log.py
Author: Tomás Vírseda
License: GPL v3
"""

import logging
from kb4it.core.env import ENV

_PATTERN = (
    "%(levelname)10s | %(lineno)4d | %(name)-20s | "
    "%(asctime)s.%(msecs)03d | %(message)s"
)

_DATEFMT = "%d/%m/%Y %H:%M:%S"


def setup_logging(
    level: str = "INFO",
    logfile: str | None = None,
):
    """
    Configure root logger once.
    """

    if level is not None:
        level_dict = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        severity = level_dict.get(level, logging.DEBUG)
    else:
        severity = logging.INFO

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    # ~ root.setLevel(getattr(logging, level.upper(), severity))

    if root.handlers:
        return  # Already configured

    formatter = logging.Formatter(_PATTERN, datefmt=_DATEFMT)

    # Console handler
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    console.setLevel(severity)
    root.addHandler(console)

    # File handler
    logfile = logfile or ENV["FILE"]["LOG"]
    file_handler = logging.FileHandler(logfile, mode="w")
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger.
    """
    return logging.getLogger(name)


def redirect_logs(logfile: str):
    """
    Redirect file logging to a new file at runtime.
    """
    root = logging.getLogger()

    formatter = logging.Formatter(_PATTERN, datefmt=_DATEFMT)

    # Remove only existing FileHandlers
    for handler in root.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            handler.flush()
            handler.close()
            root.removeHandler(handler)

    # Add new file handler
    file_handler = logging.FileHandler(logfile, mode="a")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    root.addHandler(file_handler)
