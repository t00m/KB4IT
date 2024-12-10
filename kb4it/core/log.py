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

from kb4it.core.env import ENV

# Define custom log levels
TRACE = 5
PERF = 45
WORKFLOW = 35

logging.addLevelName(TRACE, "TRACE")
logging.addLevelName(PERF, "PERF")
logging.addLevelName(WORKFLOW, "WORKFLOW")

# Helper functions for new logging levels
def trace(msg, *args, **kwargs):
    logging.log(TRACE, msg, *args, **kwargs)

def perf(msg, *args, **kwargs):
    logging.log(PERF, msg, *args, **kwargs)

def workflow(msg, *args, **kwargs):
    logging.log(WORKFLOW, msg, *args, **kwargs)

# Custom Logger class to add new logging methods
class CustomLogger(logging.getLoggerClass()):
    def trace(self, msg, *args, **kwargs):
        self.log(TRACE, msg, *args, **kwargs)

    def perf(self, msg, *args, **kwargs):
        self.log(PERF, msg, *args, **kwargs)

    def workflow(self, msg, *args, **kwargs):
        self.log(WORKFLOW, msg, *args, **kwargs)

# Set CustomLogger as the default logger class
logging.setLoggerClass(CustomLogger)

def get_logger(name, level=None):
    """Return a new logger with custom levels."""
    if level is not None:
        level_dict = {
            'TRACE': TRACE,
            'PERF': PERF,
            'WORKFLOW': WORKFLOW,
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        severity = level_dict.get(level, logging.DEBUG)  # Default to DEBUG if level is unknown
    else:
        severity = logging.INFO

    pattern = "%(levelname)10s | %(lineno)4d | %(name)-10s | %(asctime)s.%(msecs)03d | %(message)s"
    logging.basicConfig(level=logging.DEBUG,
                        format=pattern,
                        filename=ENV['FILE']['LOG'],
                        datefmt='%d/%m/%Y %I:%M:%S',
                        filemode='w'
                       )
    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)

    # Create a console (stream) handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(severity)  # Set the severity level for console logging
    formatter = logging.Formatter(pattern)
    console_handler.setFormatter(formatter)
    log.addHandler(console_handler)

    return log
