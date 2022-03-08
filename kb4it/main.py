#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
KB4IT module. Entry point.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
# Description: Website static-generator based on Asciidoctor
"""

import os
import sys
import json
import argparse
from kb4it.core.env import ENV  # APP, LPATH, GPATH
from kb4it.core.log import get_logger
from kb4it.services.backend import Backend
from kb4it.services.frontend import Frontend
from kb4it.services.database import Database
from kb4it.services.builder import Builder


class KB4IT:
    """KB4IT main class.
    """

    def __init__(self, params=None):
        """Initialize KB4IT class.

        Setup environment.
        Initialize main log.
        Register main services.
        """
        self.params = params

        # Initialize log
        self.__setup_logging(self.params.LOGLEVEL)
        self.log.info("[CONTROLLER] - KB4IT %s started", ENV['APP']['version'])
        self.log.info("[CONTROLLER] - Log level set to %s", self.params.LOGLEVEL)

        # Start up
        self.__setup_environment()
        self.__check_params()
        self.__setup_services()

    def __setup_logging(self, severity=None):
        """Set up logging."""
        self.log = get_logger(__class__.__name__, severity.upper())

    def __check_params(self):
        """Check arguments passed to the application."""
        for key in vars(self.params):
            self.log.debug("[CONTROLLER] - Parameter[%s] Value[%s]", key, vars(self.params)[key])

        if not self.params.LIST_THEMES:
            # Get repository configuration path. Mandatory
            if self.params.REPO_PATH is None:
                self.log.error("[CONTROLLER] - Repository config path parameter (-r) is mandatory.")
                self.stop()

            repo_path = os.path.abspath(self.params.REPO_PATH)
            self.log.debug("[CONTROLLER] - Repository configuration path: %s", repo_path)
            if not os.path.exists(repo_path):
                self.log.error("[CONTROLLER] - Repository configuration path doesn't exist.")
                self.stop()

            with open(repo_path, 'r') as conf:
                try:
                    self.repo = json.load(conf)
                except json.decoder.JSONDecodeError:
                    self.log.error("[CONTROLLER] - Repository config file couldn't be read")
                    self.stop()

            # Check source and target paths
            mandatory = ['title', 'source', 'target', 'theme', 'sort']
            for key in mandatory:
                if key in self.repo:
                    self.log.debug("[CONTROLLER] - Repository Key[%s]: Found!", key)
                else:
                    self.log.error("[CONTROLLER] - Repository configuration is not valid. Check and fix, please:")
                    self.log.error("[CONTROLLER] - It must contain a title, a valid source and target paths, a valid theme name and the sorting property.")
                    self.log.error("[CONTROLLER] - Key missing: %s", key)
                    self.stop()

            if self.repo['source'] == self.repo['target']:
                self.log.error("[CONTROLLER] - Error. Source and target paths are the same. That is not possible.")
                self.log.error("[CONTROLLER] - Source path: %s", self.repo['source'])
                self.log.error("[CONTROLLER] - Target path: %s", self.repo['target'])
                self.log.error("[CONTROLLER] - Check, please!")
                self.stop()

            self.log.debug("[CONTROLLER] - Preliminar checks passed.")
            self.ready = True
        else:
            self.ready = False

    def get_app_conf(self):
        """Return app configuration"""
        return self.params

    def get_repo_conf(self):
        """Return repos configuration"""
        return self.repo

    def __setup_environment(self):
        """Set up KB4IT environment."""
        self.log.debug("[CONTROLLER] - Setting up %s environment", ENV['APP']['shortname'])
        self.log.debug("[CONTROLLER] - Global path[%s]", ENV['GPATH']['ROOT'])
        self.log.debug("[CONTROLLER] - Local path[%s]", ENV['LPATH']['ROOT'])

        # Create local paths if they do not exist
        for key, path in ENV['LPATH'].items():
            if not os.path.exists(path):
                os.makedirs(path)
                self.log.debug("[CONTROLLER] - LPATH[%s] Dir[%s]: created", key, path)
            else:
                self.log.debug("[CONTROLLER] - LPATH[%s] Dir[%s]: already exists", key, path)

    def __setup_services(self):
        """Declare and register services."""
        self.services = {}
        services = {
            'DB': Database(),
            'Backend': Backend(),
            'Frontend': Frontend(),
            'Builder': Builder(),
        }
        for name, klass in services.items():
            self.register_service(name, klass)

    def get_services(self):
        """Get all registered services"""
        return self.services

    def get_service(self, name):
        """Get or start a registered service."""
        try:
            service = self.services[name]
            logname = service.__class__.__name__
            if not service.is_started():
                service.start(self, logname, name)
            return service
        except KeyError as service:
            self.log.error("[CONTROLLER] - Service %s not registered or not found", service)
            return None

    def register_service(self, name, service):
        """Register a new service."""
        try:
            self.services[name] = service
            self.log.debug("[CONTROLLER] - Service[%s] registered", name)
        except KeyError as error:
            self.log.error("[CONTROLLER] - %s", error)

    def deregister_service(self, name):
        """Deregister a running service."""
        service = self.services[name]
        registered = service is not None
        started = service.is_started()
        # ~ self.log.debug("[CONTROLLER] - Service[%s] - Registered[%s] / Started[%s]", name, registered, started)
        if registered and started:
            service.end()
        service = None
        self.log.debug("[CONTROLLER] - Service[%s] unregistered", name)

    def run(self):
        """Start application."""
        if self.ready:
            backend = self.get_service('Backend')
            try:
                backend.run()
            except Exception as error:
                self.log.error(error)
                raise
            self.stop()
        else:
            if self.params.LIST_THEMES:
                self.repo = {}
                self.repo['source'] = ENV['LPATH']['TMP_SOURCE']
                self.repo['target'] = ENV['LPATH']['TMP_TARGET']
                frontend = self.get_service('Frontend')
                frontend.theme_list()
        self.stop()

    def stop(self):
        """Stop registered services by executing the 'end' method (if any)."""
        try:
            for name in self.services:
                self.deregister_service(name)
        except AttributeError:
            # KB4IT wasn't even started
            pass
        self.log.debug("[CONTROLLER] - KB4IT %s finished", ENV['APP']['version'])
        sys.exit()


def main():
    """Set up application arguments and execute."""
    extra_usage = """"""
    parser = argparse.ArgumentParser(
        prog='kb4it',
        description='KB4IT v%s\nCustomizable static website generator based on Asciidoctor sources' % ENV['APP']['version'],
        epilog=extra_usage,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    # KB4IT arguments
    kb4it_options = parser.add_argument_group('KB4IT Options')
    kb4it_options.add_argument('-r', help='Repository config file', dest='REPO_PATH')
    kb4it_options.add_argument('-l', help='List all installed themes', action='store_true', dest='LIST_THEMES', required=False)
    kb4it_options.add_argument('-L', help='Control output verbosity. Default set to INFO', dest='LOGLEVEL', action='store', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO')
    kb4it_options.add_argument('-v', help='Show current version', action='version', version='%s %s' % (ENV['APP']['shortname'], ENV['APP']['version']))

    params = parser.parse_args()
    app = KB4IT(params)
    app.run()
