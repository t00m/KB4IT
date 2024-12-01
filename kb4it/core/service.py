#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Server module.
# File: mod_srv.py
# Author: Tomás Vírseda
# License: GPL v3
# Description: Service class
"""

import traceback as tb

from kb4it.core.log import get_logger


def get_traceback():
    """Get traceback."""
    return tb.format_exc()


class Service:
    """
    Service class.
    It is the base class for those modules acting as services.
    Different modules (GUI, Database, Ask, etc...) share same methods
    which is useful to start/stop them, simplify logging and, comunicate
    each other easily.
    """

    log = None
    logname = None
    section = None
    section_name = None

    def __init__(self, app=None):
        """Initialize Service instance."""
        if app is not None:
            self.app = app

        self.started = False

    def is_started(self):
        """
        Check if service is started.
        Return True or False if service is running / not running
        """
        return self.started

    def print_traceback(self):
        """Print traceback."""
        self.log.debug("[SERVICE] - %s", get_traceback())

    def start(self, app, name:str):
        """Start service."""
        self.started = True
        self.app = app
        self.logname = name
        conf = self.app.get_app_params()
        severity = conf.LOGLEVEL
        self.log = get_logger(name, severity)
        self.initialize()
        self.log.debug("[SERVICE] - Service %s started", name)

    def end(self):
        """End service.
        Use finalize for writting a custom end method
        """
        if self.started:
            self.started = False
            self.finalize()
            self.log.debug("[SERVICE] - Service %s finished", self.logname)

    def initialize(self, **kwargs):
        """Initialize service.
        All clases derived from Service class must implement this method
        """
        self.log.debug("[SERVICE] - Service %s started", self.logname)

    def finalize(self):
        """Finalize service.
        All clases derived from Service class must implement this method
        """
        pass

    def get_service(self, name):
        """Get service name."""
        return self.app.get_service(name)

