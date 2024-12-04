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
    pattern = "%(levelname)7s | %(lineno)4d | %(name)-10s | %(asctime)s.%(msecs)03d | %(message)s"
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
