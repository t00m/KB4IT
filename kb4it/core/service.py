#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Server module.

# File: mod_srv.py
# Author: Tomás Vírseda
# License: GPL v3
# Description: Service class
"""

from kb4it.core.log import get_logger
from kb4it.core.util import get_traceback


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

    def start(self, app, logname, section_name):
        """Start service."""
        self.started = True
        self.app = app
        self.logname = logname
        self.section_name = section_name
        params = self.app.get_params()
        severity = params.LOGLEVEL
        self.log = get_logger(logname, severity)
        self.initialize()
        self.log.debug("[SERVICE] - Service %s started" , logname)

    def end(self):
        """End service.

        Use finalize for writting a custom end method
        """
        self.started = False
        self.finalize()
        self.log.debug("[SERVICE] - Service %s finished" , self.logname)

    def initialize(self):
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
