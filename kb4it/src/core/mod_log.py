#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Log module.

# File: mod_log.py
# Author: Tomás Vírseda
# License: GPL v3
# Description: log module
"""

import logging


def get_logger(name, level=None):
    """Return a new logger."""
    if level is not None:
        if level == 'DEBUG':
            severity = logging.DEBUG
        elif level == 'INFO':
            severity = logging.INFO
        elif level == 'WARNING':
            severity = logging.WARNING
        elif level == 'ERROR':
            severity = logging.ERROR
        else:
            severity = logging.DEBUG
    else:
        severity = logging.INFO
    pattern = "%(levelname)7s | %(lineno)4d | %(name)-15s | %(asctime)s | %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=pattern)
    log = logging.getLogger(name)
    log.setLevel(severity)

    # ~ log.debug("Logger '%s' started with severity '%s'", name, level)
    # ~ formatter = logging.Formatter(pattern)
    # ~ fhl = logging.FileHandler(FILE['LOG'])
    # ~ fhl.setFormatter(formatter)
    # ~ fhl.setLevel(logging.DEBUG)
    # ~ log.addHandler(fhl)

    return log
