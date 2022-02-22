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
import tempfile
from argparse import Namespace
from kb4it.core.env import APP, LPATH, GPATH
from kb4it.core.log import get_logger
from kb4it.services.backend import Backend
from kb4it.services.frontend import Frontend
from kb4it.services.database import Database
from kb4it.services.builder import Builder


class KB4IT:
    """KB4IT main class.
    """

    ready = False
    params = None
    log = None
    repo = {}
    numdocs = 0
    tmpdir = None

    def __init__(self, params=None):
        """Initialize KB4IT class."""
        self.params = params

        # Initialize log
        try:
            self.setup_logging(self.params.LOGLEVEL)
        except:
            self.setup_logging(severity='INFO')

        self.log.debug("[CONTROLLER] - KB4IT %s started", APP['version'])
        self.log.debug("[CONTROLLER] - Log level set to %s", self.params.LOGLEVEL)

        # Start up
        self.setup_environment()
        self.check_params()
        self.setup_services()

    def setup_logging(self, severity=None):
        """Set up logging."""
        self.log = get_logger(__class__.__name__, severity.upper())

    def check_params(self):
        """Check arguments passed to the application."""
        for key in vars(self.params):
            self.log.debug("[CONTROLLER] - Parameter[%s] Value[%s]", key, vars(self.params)[key])

        if not self.params.LIST_THEMES:
            # Get repository configuration path. Mandatory
            try:
                repo_path = os.path.abspath(self.params.REPO_PATH)
                self.log.debug("[CONTROLLER] - Repository configuration path: %s", repo_path)
                if not os.path.exists(repo_path):
                    self.log.error("[CONTROLLER] - Repository configuration path doesn't exist.")
                    self.stop()
            except Exception as error:
                self.log.error("[CONTROLLER] - Error: %s", error)
                self.log.error("[CONTROLLER] - The repository config path is mandatory.")
                self.log.error("[CONTROLLER] - Error. Repository configuration path is not valid")
                self.stop()

            with open(repo_path, 'r') as conf:
                self.repo = json.load(conf)

            # Check source and target paths
            try:
                title = self.repo['title']
                source = self.repo['source']
                target = self.repo['target']
                theme = self.repo['theme']
                sort = self.repo['sort']
            except Exception as error:
                self.log.error("[CONTROLLER] - Repository configuration is not valid. Check and fix, please:")
                self.log.error("[CONTROLLER] - It must contain a title, a valid source and target paths, a valid theme name and the sorting property.")
                self.log.error("[CONTROLLER] - Error: %s", error)
                self.stop()

            if source == target:
                self.log.error("[CONTROLLER] - Error. Source and target paths are the same. That is not possible.")
                self.log.error("[CONTROLLER] - Source path: %s", source)
                self.log.error("[CONTROLLER] - Target path: %s", target)
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

    def setup_environment(self):
        """Set up KB4IT environment."""
        self.log.debug("[CONTROLLER] - Setting up %s environment", APP['shortname'])
        self.log.debug("[CONTROLLER] - Global path[%s]", GPATH['ROOT'])
        self.log.debug("[CONTROLLER] - Local path[%s]", LPATH['ROOT'])

        # Create local paths if they do not exist
        for entry in LPATH:
            if not os.path.exists(LPATH[entry]):
                os.makedirs(LPATH[entry])
                self.log.debug("[CONTROLLER] - Directory[%s] created", LPATH[entry])
            else:
                self.log.debug("[CONTROLLER] - Directory[%s] already exists", LPATH[entry])

    def setup_services(self):
        """Declare and register services."""
        self.services = {}
        try:
            services = {
                'DB': Database(),
                'Backend': Backend(),
                'Frontend': Frontend(),
                'Builder': Builder(),
            }
            for name in services:
                self.register_service(name, services[name])
        except Exception as error:
            self.log.error("[CONTROLLER] - %s", error)
            raise

    def get_services(self):
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
            raise

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
                self.repo['source'] = LPATH['TMP_SOURCE']
                self.repo['target'] = LPATH['TMP_TARGET']
                frontend = self.get_service('Frontend')
                frontend.theme_list()
        self.stop()

    def get_version(self):
        """Get KB4IT version."""
        return '%s %s' % (APP['shortname'], APP['version'])

    def stop(self):
        """Stop registered services by executing the 'end' method (if any)."""
        try:
            for name in self.services:
                self.deregister_service(name)
        except AttributeError:
            # KB4IT wasn't even started
            pass
        self.log.debug("[CONTROLLER] - KB4IT %s finished", APP['version'])
        sys.exit()

def main():
    """Set up application arguments and execute."""
    extra_usage = """"""
    parser = argparse.ArgumentParser(
        prog='kb4it',
        description='KB4IT v%s\nCustomizable static website generator based on Asciidoctor sources' % APP['version'],
        epilog=extra_usage,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    # KB4IT arguments
    kb4it_options = parser.add_argument_group('KB4IT Options')
    kb4it_options.add_argument('-r', help='Repository config file', dest='REPO_PATH')
    kb4it_options.add_argument('-l', help='List all installed themes', action='store_true', dest='LIST_THEMES', required=False)
    kb4it_options.add_argument('-L', help='Control output verbosity. Default to INFO', dest='LOGLEVEL', action='store', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO')
    kb4it_options.add_argument('-v', help='Show current version', action='version', version='%s %s' % (APP['shortname'], APP['version']))

    params = parser.parse_args()
    app = KB4IT(params)
    app.run()
