#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
KB4IT module. Entry point.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# Version: 0.4
# License: GPLv3
# Description: Build a static documentation site based on Asciidoctor
"""

import os
import sys
import argparse
from kb4it.src.core.mod_env import APP, LPATH, GPATH
from kb4it.src.core.mod_log import get_logger
from kb4it.src.services.srv_app import Application
from kb4it.src.services.srv_db import KB4ITDB
from kb4it.src.services.srv_builder import Builder

class KB4IT:
    """KB4IT Application class."""

    params = None
    log = None
    source_path = None
    target_path = None
    numdocs = 0
    tmpdir = None

    def __init__(self, params):
        """Initialize KB4IT class."""
        self.params = params
        self.setup_logging(params.LOGLEVEL)
        self.check_params()
        self.setup_services()
        self.setup_environment()

    def check_params(self):
        source = os.path.abspath(self.params.SOURCE_PATH)
        target = os.path.abspath(self.params.TARGET_PATH)
        if source == target:
            self.log.error("Error. Source and target paths are the same.")
            self.log.error("Source path: %s", source)
            self.log.error("Target path: %s", target)
            self.log.error("Check, please!")
            sys.exit(-1)

    def get_params(self):
        """Return parametres."""
        return self.params

    def setup_environment(self):
        """Set up KB4IT environment."""
        self.log.debug("Setting up %s environment", APP['shortname'])
        self.log.debug("Global path: %s", GPATH['ROOT'])
        self.log.debug("Local path: %s", LPATH['ROOT'])

        # Create local paths if they do not exist
        for entry in LPATH:
            self.log.debug("Checking if directory '%s' exists", LPATH[entry])
            if not os.path.exists(LPATH[entry]):
                os.makedirs(LPATH[entry])
                self.log.debug("Creating directory '%s'", LPATH[entry])

    def setup_logging(self, severity=None):
        """Set up logging."""
        self.log = get_logger(__class__.__name__, severity.upper())
        self.log.debug("Log level set to: %s", severity.upper())

    def setup_services(self):
        """Set up services."""
        # Declare and register services
        self.services = {}
        try:
            services = {
                'DB': KB4ITDB(),
                'App': Application(),
                'Builder': Builder(),
            }
            for name in services:
                self.register_service(name, services[name])
        except Exception as error:
            self.log.error(error)
            raise

    def get_service(self, name):
        """Get or start a registered service."""
        try:
            service = self.services[name]
            logname = service.__class__.__name__
            if not service.is_started():
                service.start(self, logname, name)
            return service
        except KeyError as service:
            self.log.error("Service %s not registered or not found", service)
            raise

    def register_service(self, name, service):
        """Register a new service."""
        try:
            self.services[name] = service
            self.log.debug("Service '%s' registered", name)
        except KeyError as error:
            self.log.error(error)

    def deregister_service(self, name):
        """Deregister a running service."""
        self.services[name].end()
        self.services[name] = None

    def check_parameters(self, params):
        """Check paramaters from command line."""
        self.params = params
        self.source_path = params.SOURCE_PATH

        self.target_path = params.TARGET_PATH
        if self.target_path is None:
            self.target_path = os.path.abspath(os.path.curdir + '/target')
            self.log.debug("\tNo target path provided. Using: %s", self.target_path)

        if not os.path.exists(self.target_path):
            os.makedirs(self.target_path)
            self.log.debug("\tTarget path %s created", self.target_path)

        self.log.debug("\tScript directory: %s", GPATH['ROOT'])
        self.log.debug("\tResources directory: %s", GPATH['RESOURCES'])
        self.log.debug("\tSource directory: %s", self.source_path)
        self.log.debug("\tTarget directory: %s", self.target_path)
        self.log.debug("\tTemporary directory: %s", self.tmpdir)

    def run(self):
        """Start application."""
        srvapp = self.get_service('App')
        srvapp.run()
        self.stop()

    def stop(self):
        """Stop registered services by executing the 'end' method (if any)."""
        for name in self.services:
            self.deregister_service(name)
        self.log.debug("KB4IT %s finished", APP['version'])


def main():
    """Execute application."""
    parser = argparse.ArgumentParser(description='KB4IT %s by Tomás Vírseda' % APP['version'])

    parser.add_argument('-force', action='store_true', dest='FORCE', help='Force a clean compilation')
    parser.add_argument('-theme', dest='THEME', help='Specify theme. Otherwise, it uses the default one', required=False)
    parser.add_argument('-source', dest='SOURCE_PATH', help='Source directory with asciidoctor source files', required=True)
    parser.add_argument('-target', dest='TARGET_PATH', help='Target directory')
    parser.add_argument('-sort', dest='SORT_ATTRIBUTE', help='Choose another attribute for sorting instead the default timestamp')
    parser.add_argument('-log', dest='LOGLEVEL', help='Increase output verbosity', action='store', default='INFO')
    parser.add_argument('-version', action='version', version='%s %s' % (APP['shortname'], APP['version']))
    params = parser.parse_args()
    app = KB4IT(params)
    app.run()
