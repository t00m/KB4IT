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
import math
import multiprocessing
import argparse
import traceback
from kb4it.core.env import ENV
from kb4it.core.log import get_logger
from kb4it.core.util import now
from kb4it.core.perf import timeit
from kb4it.services.backend import Backend
from kb4it.services.frontend import Frontend
from kb4it.services.database import Database
from kb4it.services.builder import Builder
from kb4it.services.workflow import Workflow

def get_default_workers():
    """Calculate default number or workers.
    Workers = Number of CPU / 2
    Minimum workers = 1
    """
    ncpu = multiprocessing.cpu_count()
    workers = ncpu/2
    return math.ceil(workers)


class KB4IT:
    """KB4IT main class."""
    repo = {}

    def __init__(self, params: argparse.Namespace=None):
        """Initialize KB4IT class.

        Setup environment.
        Initialize main log.
        Register main services.
        """
        if params is not None:
            self.params = params
        else:
            self.params = argparse.Namespace()
            self.params.REPO_CONFIG_FILE = None

        # Initialize log
        if 'log_level' not in vars(self.params):
            self.params.LOGLEVEL = 'INFO'
        self.__setup_logging(self.params.log_level)

        self.log.debug(f"[CONTROLLER] - KB4IT {ENV['APP']['version']} started at {now()} using PID {ENV['SYS']['PS']['PID']}")
        self.log.debug(f"[CONTROLLER] - Python environment:")
        self.log.debug(f"[CONTROLLER] - \tVersion: {ENV['SYS']['PYTHON']['VERSION']}")
        self.log.debug(f"[CONTROLLER] - Platform:")
        self.log.debug(f"[CONTROLLER] - \tOperating System: {ENV['SYS']['PLATFORM']['OS']}")

        # Start up
        self.__setup_environment()
        self.__check_params()
        self.__setup_services()

        #self.log.info("[CONTROLLER] - KB4IT %s started at %s", ENV['APP']['version'], now())
        #self.log.debug("[CONTROLLER] - Log level set to %s", self.params.LOGLEVEL)
        #self.log.debug("[CONTROLLER] - Process: %s (%d)", ENV['PS']['NAME'], ENV['PS']['PID'])
        #self.log.debug("[CONTROLLER] - MaxWorkers: %d (default)", self.params.NUM_WORKERS)

        self.__gonogo()

    def __setup_logging(self, severity=None):
        """Set up logging."""
        self.log = get_logger(__class__.__name__, severity.upper())

    def __check_params(self):
        """Check arguments passed to the application."""

        self.log.trace("[CONTROLLER] - Command line parameters:")
        for key in vars(self.params):
            self.log.trace(f"[CONTROLLER] - \t{key}: {vars(self.params)[key]}")

    def get_params(self):
        """Return app configuration"""
        return self.params

    def __setup_environment(self):
        """Set up KB4IT environment."""
        self.log.trace("[CONTROLLER] - Setting up %s environment", ENV['APP']['shortname'])
        self.log.trace("[CONTROLLER] - \tGlobal path[%s]", ENV['GPATH']['ROOT'])
        self.log.trace("[CONTROLLER] - \tLocal path[%s]", ENV['LPATH']['ROOT'])

        # Create local paths if they do not exist
        for key, path in ENV['LPATH'].items():
            if not os.path.exists(path):
                os.makedirs(path)
                self.log.trace("[CONTROLLER] - \tLPATH[%s] Dir[%s]: created", key, path)
            else:
                self.log.trace("[CONTROLLER] - \tLPATH[%s] Dir[%s]: already exists", key, path)

    def __setup_services(self):
        """Declare and register services."""
        self.services = {}
        services = {
            'DB': Database(),
            'Backend': Backend(),
            'Frontend': Frontend(),
            'Builder': Builder(),
            'Workflow': Workflow(),
        }
        for name, klass in services.items():
            self.register_service(name, klass)

    def __gonogo(self):
        """Go/No-Go decision making"""
        can_run = False
        no_go_reason = ''
        pidfile = os.path.join(ENV['LPATH']['VAR'], 'kb4it.pid')
        if os.path.exists(pidfile):
            pid = open(pidfile, 'r').read()
            if os.path.exists('/proc/%s'):
                can_run = False
                no_go_reason = 'Previous process (%s) still running?' % pid
            else:
                can_run = True
        else:
            # Previous Pid file doesn't exist. Continue
            can_run = True

        if can_run:
            # Write current Pid to file
            with open(pidfile, 'w') as fpid:
                fpid.write(str(ENV['SYS']['PS']['PID']))
            self.log.debug("[CONTROLLER] - Decision: Go")
        else:
            self.log.error(f"[CONTROLLER] - Decision: No Go")
            self.log.error(f"[CONTROLLER] - Reason: {no_go_reason}")
            self.stop()

    def get_services(self):
        """Get all registered services"""
        return self.services

    def get_service(self, name: str = {}):
        """Get or start a registered service."""
        self.log.trace(f"[CONTROLLER] - Getting service '{name}'")
        try:
            service = self.services[name]
            logname = service.__class__.__name__
            if not service.is_started():
                service.start(self, name)
            return service
        except Exception as error:
            self.log.error(f"[CONTROLLER] - Service {name} not registered")
            self.log.error(f"[CONTROLLER] - \t{error}")
            self.stop(error=True)
            #raise
            #return None

    def register_service(self, name, service):
        """Register a new service."""
        try:
            self.services[name] = service
            self.log.trace("[CONTROLLER] - Service[%s] registered", name)
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
        self.log.trace("[CONTROLLER] - Service[%s] unregistered", name)

    @timeit
    def run(self):
        """Start application."""

        action = self.params.action
        self.log.debug(f"[CONTROLLER] - Executing action: {action}")
        workflow = self.get_service('Workflow')

        if action == 'themes':
            workflow.list_themes()
        elif action == 'create':
            workflow.create_repository()
        elif action == 'build':
            workflow.build_website()
        self.stop()

    def stop(self, error=False):
        """Stop registered services by executing the 'end' method (if any)."""
        if error:
            self.log.error("[CONTROLLER] - Execution aborted because of serious errors")
            self.log.error(f"[CONTROLLER] - \tTraceback:\n{traceback.print_exc()}")
            self.log.error(f"[CONTROLLER] - KB4IT {ENV['APP']['version']} finished at {now()}")
            sys.exit(-1)

        try:
            for name in self.services:
                self.deregister_service(name)
        except AttributeError:
            # KB4IT wasn't even started
            raise
        self.log.debug("[CONTROLLER] - KB4IT %s finished at %s", ENV['APP']['version'], now())
        sys.exit()

class CustomHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """Custom formatter to replace section titles in the help output."""

    def add_arguments(self, actions):
        if any(action.dest == 'action' for action in actions):
            self._root_section.heading = 'Actions available'
        super().add_arguments(actions)

def main():
    """Set up application arguments and execute."""
    extra_usage = """Thanks for using KB4IT!\n"""
    parser = argparse.ArgumentParser(
        prog='kb4it',
        description=f'KB4IT v{ENV["APP"]["version"]}\nCustomizable static website generator based on Asciidoctor sources',
        epilog=extra_usage,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '-L', '--log-level',
        help='Control output verbosity. Default set to INFO',
        choices=['TRACE', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'WORKFLOW', 'PERF', 'STORY'],
        default='INFO'
    )
    parser.add_argument(
        '-v', '--version',
        action='version',
        version=f'{ENV["APP"]["shortname"]} {ENV["APP"]["version"]}'
    )

    # Add subcommands for actions
    subparsers = parser.add_subparsers(
        dest='action',
        required=True,
        help='Action to perform'
    )

    # Initialize repository
    init_parser = subparsers.add_parser('create', help='Initialize a new repository')
    init_parser.add_argument('theme', help='Theme to use for initialization')
    init_parser.add_argument('repo_path', help='Path to the repository')

    # List themes
    subparsers.add_parser('themes', help='List all installed themes')

    # run repository workflow
    workflow_parser = subparsers.add_parser(
        'build',
        help='Run workflow for a given repository',
        description='Based on your repository configuration, compile and build the website',
        epilog='Example:\n\n'
               ' - Compile a repository with 10 workers. Do not force a clean compilation:\n'
               '   kb4it run-workflow /home/jsmith/Documents/myrepo/config/repo.json false --workers=10\n'
    )
    workflow_parser.add_argument(
        'config',
        help='Path to the repository config file (mandatory)'
    )
    workflow_parser.add_argument(
        '-f', '--force',
        action='store_true',
        default=False,
        help='Force a clean compilation'
    )
    workflow_parser.add_argument(
        '-w', '--workers',
        help=f'Number of workers. Default is CPUs available/2. Default: {get_default_workers()}',
        type=int,
        default=get_default_workers()
    )


    # Dispatch to the appropriate action handler
    try:
        params = parser.parse_args()
        app = KB4IT(params)
        app.run()
    except SystemExit as error:
        if error.code != 0 and error.code is not None:
            print("Run 'kb4it <action name> --help' to get help for a specific command.")

