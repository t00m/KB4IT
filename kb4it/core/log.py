#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Log module.
# File: mod_log.py
# Author: Tomás Vírseda
# License: GPL v3
# Description: log module
"""

import os
import logging

from kb4it.core.env import ENV

_PATTERN = "%(levelname)10s | %(lineno)4d | %(name)-15s | %(asctime)s.%(msecs)03d | %(message)s"


def get_logger(name, level='INFO') -> logging.Logger:
    """Return a new logger with custom levels."""
    level_dict = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
    severity = level_dict.get(level, logging.DEBUG)
    logger = logging.getLogger(name)
    logger.setLevel(severity)

    # Prevent duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler()  # temporary / console
        formatter = logging.Formatter(
            _PATTERN,
            datefmt="%d/%m/%Y %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        file_handler = logging.FileHandler(ENV['FILE']['LOG'], mode="w")
        file_handler.setFormatter(formatter)
        root = logging.getLogger()
        root.addHandler(file_handler)


    logger.propagate = True
    return logger

def redirect_logs(logfile: str):
    root = logging.getLogger()

    formatter = logging.Formatter(
        _PATTERN,
        datefmt="%d/%m/%Y %H:%M:%S"
    )

    # Remove ALL file/stream handlers
    for handler in root.handlers[:]:
        handler.close()
        root.removeHandler(handler)

    # Add new file handler
    file_handler = logging.FileHandler(logfile, mode="a", delay=True)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)
    root.setLevel(logging.DEBUG)
