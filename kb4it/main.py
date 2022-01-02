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
import argparse
import tempfile
from argparse import Namespace
from kb4it.core.env import APP, LPATH, GPATH
from kb4it.core.log import get_logger
from kb4it.services.app import KB4ITApp
from kb4it.services.database import KB4ITDB
from kb4it.services.builder import KB4ITBuilder


class KB4IT:
    r"""
    KB4IT main class.

    It can be executed from command line:
    $HOME/.local/bin/kb4it -theme <None|THEME> -force -log DEBUG \
                           -sort <ATTRIBUTE> -source <SOURCE_PATH>
                           -target <TARGET_PATH>

    Or it can be called from another app as a library:
    Eg.:

    >>> from kb4it.kb4it import KB4IT
    >>> from argparse import Namespace
    >>> params = Namespace(
                    RESET=False, \
                    FORCE=True, \
                    LOGLEVEL='INFO', \
                    SORT_ATTRIBUTE=None, \
                    SOURCE_PATH='tmp/sources', \
                    TARGET_PATH='/tmp/output', \
                    THEME='techdoc'
                )
    >>> kb = KB4IT(params)
    >>> kb.run()
    """

    ready = False
    params = None
    log = None
    source_path = None
    target_path = None
    numdocs = 0
    tmpdir = None

    def __init__(self, params=None):
        """Initialize KB4IT class."""
        self.params = params
        self.setup_logging(self.params.LOGLEVEL)
        self.log.debug("[CONTROLLER] - KB4IT %s started", APP['version'])
        self.log.debug("[CONTROLLER] - Log level set to %s", self.params.LOGLEVEL)
        self.setup_services()
        self.setup_environment()
        self.check_params()

    def setup_logging(self, severity=None):
        """Set up logging."""
        self.log = get_logger(__class__.__name__, severity.upper())

    def check_params(self):
        """Check arguments passed to the application."""
        for key in vars(self.params):
            self.log.debug("[CONTROLLER] - Parameter[%s] Value[%s]", key, vars(self.params)[key])

        if not self.params.LIST_THEMES:
            # Check source path
            try:
                source = os.path.abspath(self.params.SOURCE_PATH)
            except:
                self.log.error("[CONTROLLER] - Invalid argments. See help.")
                self.log.error("[CONTROLLER] - Error. Source path '%s' not valid", self.params.SOURCE_PATH)
                return False

            # Check target path
            try:
                target = os.path.abspath(self.params.TARGET_PATH)
            except:
                self.log.error("[CONTROLLER] - Invalid argments. See help.")
                self.log.error("[CONTROLLER] - Error. Target path '%s' not valid", self.params.TARGET_PATH)
                return False

            # Check if theme was passed. If not, it will be autodetected
            # ~ if self.params.THEME is None:
                # ~ self.log.warning("[CONTROLLER] - Theme will be autodetected from source directory")

            self.ready = True
            if source == target:
                self.log.error("[CONTROLLER] - Error. Source and target paths are the same.")
                self.log.error("[CONTROLLER] - Source path: %s", source)
                self.log.error("[CONTROLLER] - Target path: %s", target)
                self.log.error("[CONTROLLER] - Check, please!")
                self.ready = False
                return True

    def get_params(self):
        """Return parametres."""
        return self.params

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
                'DB': KB4ITDB(),
                'App': KB4ITApp(),
                'Builder': KB4ITBuilder(),
            }
            for name in services:
                self.register_service(name, services[name])
        except Exception as error:
            self.log.error("[CONTROLLER] - %s", error)
            raise

    def get_service(self, name):
        """Get or start a registered service."""
        try:
            service = self.services[name]
            # ~ print(dir(service))
            # ~ print(service.__module__)
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
        if self.services[name] is not None:
            self.services[name].end()
            self.services[name] = None
            self.log.debug("[CONTROLLER] - Service '%s' unregistered", name)

    def run(self):
        """Start application."""
        if self.ready:
            srvapp = self.get_service('App')
            if self.params.RESET:
                if self.params.FORCE:
                    srvapp.reset()
                else:
                    self.log.warning("[CONTROLLER] - KB4IT environment NOT reset. You must force it!")
            else:
                srvapp.run()
                self.stop()
        else:
            if self.params.LIST_THEMES:
                self.params.SOURCE_PATH = LPATH['TMP_SOURCE']
                self.params.TARGET_PATH = LPATH['TMP_TARGET']
                srvapp = self.get_service('App')
                srvapp.list_themes()
        self.stop()

    def get_version(self):
        """Get KB4IT version."""
        return '%s %s' % (APP['shortname'], APP['version'])

    def stop(self):
        """Stop registered services by executing the 'end' method (if any)."""
        for name in self.services:
            self.deregister_service(name)
        self.log.debug("[CONTROLLER] - KB4IT %s finished", APP['version'])
        sys.exit()


def main():
    """Set up application arguments and execute."""
    extra_usage = """

Test application with these example commands:\n\n

1) Simple usage: autodetect theme in sources. In any, use the default one.

   $ kb4it /path/to/source /path/to/target

2) Force a clean compilation when you upgrade KB4IT or change any template

    $ kb4it /path/to/source /path/to/target -force

3) Tell KB4IT to use a specific attribute for sorting the database

    $ kb4it /path/to/source /path/to/target -sort Published

4) Specifiy a theme:

    $ kb4it /path/to/source /path/to/target -theme techdoc

5) Increase or decrease log verbosity. Default: INFO

    $ kb4it /path/to/source /path/to/target -log DEBUG
    $ kb4it /path/to/source /path/to/target -log ERROR

5) Combine them:

    $ kb4it /path/to/source /path/to/target -theme techdoc -sort Publised -log DEBUG -force

kb4it -theme techdoc -sort <date_attribute> -source <sources_dir> -target <target_dir> -log DEBUG

"""
    parser = argparse.ArgumentParser(
        prog='kb4it',
        description='KB4IT v%s\nStatic but customizable website generator based on Asciidoctor sources' % APP['version'],
        # ~ epilog=extra_usage,
        formatter_class=argparse.RawDescriptionHelpFormatter)


    group_kb4it = parser.add_argument_group('KB4IT arguments')
    # ~ group_opt = parser.add_mutually_exclusive_group()

    # KB4IT arguments

    group_kb4it.add_argument('-S', '--source', help='directory with Asciidoctor source files', dest='SOURCE_PATH')
    group_kb4it.add_argument('-T', '--target', help='target directory for output', dest='TARGET_PATH')

    # Optional arguments
    group_kb4it.add_argument('-l', '--list-themes', action='store_true', dest='LIST_THEMES', required=False, help='List all installed themes')
    group_kb4it.add_argument('-L', '--log', dest='LOGLEVEL', action='store', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO', help='Control output verbosity. Default to INFO')
    group_kb4it.add_argument('-R', '--reset', action='store_true', dest='RESET', help='reset environment')
    group_kb4it.add_argument('-F', '--force', action='store_true', dest='FORCE', help='force a clean compilation')
    group_kb4it.add_argument('-v', '--version', action='version', version='%s %s' % (APP['shortname'], APP['version']))
    group_kb4it.add_argument('-t', '--theme', dest='THEME', required=False, help='specify theme (techdoc, snippets, default, ...)')
    group_kb4it.add_argument('-s', '--sort', dest='SORT_ATTRIBUTE', help='sorting attribute (Published, Updated, ...)')

    params = parser.parse_args()
    app = KB4IT(params)
    app.run()
