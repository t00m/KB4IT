#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
KB4IT module. Entry point.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
# Description: Website static-generator based on Asciidoctor
"""

import os
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
        if params is not None:
            self.params = params
        else:
            tmp_source = os.path.join(LPATH['TMP'], 'source')
            tmp_target = os.path.join(LPATH['TMP'], 'target')
            self.params = Namespace(RESET=False, FORCE=False, LOGLEVEL='INFO', SORT_ATTRIBUTE=None, SOURCE_PATH=tmp_source, TARGET_PATH=tmp_target, THEME=None)
        try:
            self.setup_logging(self.params.LOGLEVEL)
        except TypeError:
            self.setup_logging('INFO')
        self.check_params()
        self.setup_services()
        self.setup_environment()

    def check_params(self):
        """Check arguments passed to the application."""
        self.ready = True
        source = os.path.abspath(self.params.SOURCE_PATH)
        target = os.path.abspath(self.params.TARGET_PATH)
        if source == target:
            self.log.error("[MAIN] - Error. Source and target paths are the same.")
            self.log.error("[MAIN] - Source path: %s", source)
            self.log.error("[MAIN] - Target path: %s", target)
            self.log.error("[MAIN] - Check, please!")
            self.ready = False

    def get_params(self):
        """Return parametres."""
        return self.params

    def setup_environment(self):
        """Set up KB4IT environment."""
        self.log.debug("[MAIN] - Setting up %s environment", APP['shortname'])
        self.log.debug("[MAIN] - Global path: %s", GPATH['ROOT'])
        self.log.debug("[MAIN] - Local path: %s", LPATH['ROOT'])

        # Create local paths if they do not exist
        for entry in LPATH:

            if not os.path.exists(LPATH[entry]):
                os.makedirs(LPATH[entry])
                self.log.debug("[MAIN] - Creating directory '%s'", LPATH[entry])
            else:
                self.log.debug("[MAIN] - Directory '%s' already exists", LPATH[entry])

    def setup_logging(self, severity=None):
        """Set up logging."""
        self.log = get_logger(__class__.__name__, severity.upper())
        self.log.debug("[MAIN] - Log level set to: %s", severity.upper())

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
            self.log.error("[MAIN] - %s", error)
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
            self.log.error("[MAIN] - Service %s not registered or not found", service)
            raise

    def register_service(self, name, service):
        """Register a new service."""
        try:
            self.services[name] = service
            self.log.debug("[MAIN] - Service '%s' registered", name)
        except KeyError as error:
            self.log.error("[MAIN] - %s", error)

    def deregister_service(self, name):
        """Deregister a running service."""
        self.services[name].end()
        self.services[name] = None

    def run(self):
        """Start application."""
        if self.ready:
            srvapp = self.get_service('App')
            if self.params.RESET:
                if self.params.FORCE:
                    srvapp.reset()
                else:
                    self.log.warning("[MAIN] - KB4IT environment NOT reset. You must force it!")
            else:
                srvapp.run()
                self.stop()

    def get_version(self):
        """Get KB4IT version."""
        return '%s %s' % (APP['shortname'], APP['version'])

    def stop(self):
        """Stop registered services by executing the 'end' method (if any)."""
        for name in self.services:
            self.deregister_service(name)
        self.log.debug("[MAIN] - KB4IT %s finished", APP['version'])


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

    # Mandatory arguments
    parser.add_argument('SOURCE_PATH', help='directory with Asciidoctor source files')
    parser.add_argument('TARGET_PATH', help='target directory for output')

    # Optional arguments
    parser.add_argument('-reset', action='store_true', dest='RESET',
                        help='reset environment')
    parser.add_argument('-force', action='store_true', dest='FORCE',
                        help='force a clean compilation')
    parser.add_argument('-theme', dest='THEME', required=False,
                        help='specify theme (techdoc, snippets, default, ...)')
    parser.add_argument('-sort', dest='SORT_ATTRIBUTE',
                        help='sorting attribute (Published, Updated, ...)')
    parser.add_argument('-log', dest='LOGLEVEL', action='store',
                        default='INFO',
                        help='increase output verbosity (DEBUG | INFO | ERROR)')
    parser.add_argument('-version', action='version',
                        version='%s %s' % (APP['shortname'],
                                           APP['version']))
    params = parser.parse_args()
    app = KB4IT(params)
    app.run()
