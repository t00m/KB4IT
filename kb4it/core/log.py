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

# Custom log levels
STORY = 55
TRACE = 5
PERF = 45
WORKFLOW = 35

logging.addLevelName(TRACE, "TRACE")
logging.addLevelName(STORY, "STORY")
logging.addLevelName(PERF, "PERF")
logging.addLevelName(WORKFLOW, "WORKFLOW")

# Custom Logger class to add new logging methods
class CustomLogger(logging.getLoggerClass()):
    def trace(self, msg, *args, **kwargs):
        self.log(TRACE, msg, *args, stacklevel=2, **kwargs)

    def perf(self, msg, *args, **kwargs):
        self.log(PERF, msg, *args, stacklevel=2, **kwargs)

    def workflow(self, msg, *args, **kwargs):
        self.log(WORKFLOW, msg, *args, stacklevel=2, **kwargs)

    def story(self, msg, *args, **kwargs):
        self.log(STORY, msg, *args, stacklevel=2, **kwargs)

# Set CustomLogger as the default logger class
logging.setLoggerClass(CustomLogger)

def get_logger(name, level=None):
    """Return a new logger with custom levels."""
    if level is not None:
        level_dict = {
            'TRACE': TRACE,
            'STORY': STORY,
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
