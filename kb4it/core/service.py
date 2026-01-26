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

    def __init__(self, app=None):
        """Initialize Service instance."""

        self.modname = self.__class__.__name__
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
        self.log.debug(f"Traceback:\n{get_traceback()}")

    def start(self, app, name:str):
        """Start service."""
        self.started = True
        self.app = app
        params = self.app.get_params()
        severity = params['log_level']
        self.log = get_logger(f"{self.modname}")
        self.initialize()
        # ~ self.log.debug(f"Service {self.modname} started")

    def end(self):
        """End service.
        Use finalize for writting a custom end method
        """
        if self.started:
            self.started = False
            self.finalize()
            # ~ self.log.debug(f"Service {self.modname} finished")

    def initialize(self, **kwargs):
        """Initialize service.
        All clases derived from Service class must implement this method
        """
        pass

    def finalize(self):
        """Finalize service.
        All clases derived from Service class must implement this method
        """
        pass

    def get_service(self, name):
        """Get service name."""
        return self.app.get_service(name)

