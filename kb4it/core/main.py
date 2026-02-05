#!/usr/bin/env python

"""
KB4IT module. Entry point.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
# Description: Website static-generator based on Asciidoctor
"""

import os
import sys
import uuid
import argparse
import traceback
from kb4it.core.env import ENV
from kb4it.core.log import setup_logging
from kb4it.core.log import get_logger
from kb4it.core.util import now
from kb4it.core.perf import timeit
from kb4it.services.backend import Backend
from kb4it.services.frontend import Frontend
from kb4it.services.database import Database
from kb4it.services.builder import Builder
from kb4it.services.workflow import Workflow


class KB4IT:
    """KB4IT main class."""
    repo = {}

    def __init__(self, params: argparse.Namespace=None):
        """Initialize KB4IT class.
        Setup environment.
        Initialize main log.
        Register main services.
        """
        self.set_log_file()
        self.__setup_environment()
        if params is not None:
            self.params = vars(params)
        else:
            self.params = vars(argparse.Namespace())
            self.params['REPO_CONFIG_FILE'] = None

        # Initialize log
        if 'log_level' not in self.params:
            self.params['LOGLEVEL'] = 'INFO'
        setup_logging(self.params['log_level'], self.log_file)
        self.log = get_logger(__class__.__name__)
        self.log.debug(f"[CONTROLLER] - Temporary KB4IT Log file: {self.log_file}")
        self.log.debug(f"[CONTROLLER] - KB4IT {ENV['APP']['version']}")
        self.log.debug(f"[CONTROLLER] - CONF[SYS] PYTHON[{ENV['SYS']['PYTHON']['VERSION']}]")
        self.log.debug(f"[CONTROLLER] - CONF[SYS] PLATFORM[{ENV['SYS']['PLATFORM']['OS']}]")
        self.log.debug(f"[CONTROLLER] - CONF[ENV] GPATH[ROOT] DIR[{ENV['GPATH']['ROOT']}]")
        self.log.debug(f"[CONTROLLER] - CONF[ENV] LPATH[ROOT] DIR[{ENV['LPATH']['ROOT']}]")

        # Start up
        self.__check_params()
        self.__setup_services()

    def set_log_file(self):
        suffix = str(uuid.uuid1().time)
        self.log_file = f"{ENV['FILE']['LOG']}.{suffix}"

    def get_log_file(self):
        return self.log_file

    def __setup_logging(self, severity=None):
        """Set up logging."""
        self.log = get_logger(__class__.__name__)

    def __check_params(self):
        """Check arguments passed to the application."""
        for key in self.params:
            self.log.debug(f"[CONTROLLER] - CONF[CMDLINE] PARAM[{key}] VALUE[{self.params[key]}]")

    def get_params(self):
        """Return app configuration"""
        return self.params

    def __setup_environment(self):
        """Set up KB4IT environment."""
        # Create local paths if they do not exist
        for key, path in ENV['LPATH'].items():
            if not os.path.exists(path):
                os.makedirs(path)

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

    def get_services(self):
        """Get all registered services"""
        return self.services

    def get_service(self, name: str = {}):
        """Get or start a registered service."""
        try:
            self.log.debug(f"[CONTROLLER] - Getting service '{name}'")
            service = self.services.get(name)
            if service:
                logname = service.__class__.__name__
                if not service.is_started():
                    service.start(self, name)
                    self.log.debug(f"[CONTROLLER] - Service '{name}' started")
                return service
            else:
                self.stop()
        except Exception as error:
            self.log.error(f"[CONTROLLER] - Service {name} not registered")
            self.log.error(f"[CONTROLLER] - \t{error}")
            self.stop(error=True)
            return None

    def register_service(self, name, service):
        """Register a new service."""
        try:
            self.services[name] = service
            self.log.debug(f"[CONTROLLER] - Service[{name}] registered")
            return service
        except KeyError as error:
            self.log.error(f"[CONTROLLER] - {error}")
            return None

    def deregister_service(self, name):
        """Deregister a running service."""
        service = self.services.get(name)
        registered = service is not None
        started = service.is_started()
        if registered and started:
            service.end()
            self.log.debug(f"[CONTROLLER] - Service[{name}] unregistered")
        service = None


    # ~ @timeit
    def run(self):
        """Start application."""
        action = self.params['action']
        workflow = self.get_service('Workflow')
        self.log.debug(f"[CONTROLLER] - Executing KB4IT action '{action}'")
        if action == 'themes':
            workflow.list_themes()
        elif action == 'create':
            workflow.create_repository()
        elif action == 'build':
            workflow.build_website()
        elif action == 'info':
            workflow.info_repository()
        elif action == 'apps':
            workflow.list_apps(self.params['theme'])
        self.stop()

    def stop(self, error=False):
        """Stop registered services by executing the 'end' method (if any)."""
        if error:
            self.log.error(f"[CONTROLLER] - Execution aborted because of serious errors")
            self.log.error(f"[CONTROLLER] - \tTraceback:\n{traceback.print_exc()}")
            self.log.error(f"[CONTROLLER] - KB4IT {ENV['APP']['version']} finished at {now()}")
            sys.exit(-1)

        try:
            for name in self.services:
                self.deregister_service(name)
        except AttributeError:
            # KB4IT wasn't even started
            raise
        self.log.debug(f"[CONTROLLER] - KB4IT {ENV['APP']['version']} finished at {now()}")
        sys.exit()

# ~ class CustomHelpFormatter(argparse.RawDescriptionHelpFormatter):
    # ~ """Custom formatter to replace section titles in the help output."""

    # ~ def add_arguments(self, actions):
        # ~ if any(action.dest == 'action' for action in actions):
            # ~ self._root_section.heading = 'Actions available'
        # ~ super().add_arguments(actions)

def main():
    """Set up application arguments and execute."""
    extra_usage = """Thanks for using KB4IT!\n"""
    parser = argparse.ArgumentParser(
        prog='kb4it',
        description=f"KB4IT v{ENV['APP']['version']}\nCustomizable static website generator based on Asciidoctor sources",
        epilog=extra_usage,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '-L', '--log-level',
        help='Control output verbosity. Default set to INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO'
    )
    parser.add_argument(
        '-v', '--version',
        action='version',
        version=f"{ENV['APP']['shortname']} {ENV['APP']['version']}"
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

    # List apps for a specific theme
    theme_apps = subparsers.add_parser('apps', help='List all apps for a specific theme')
    theme_apps.add_argument('theme', help='Theme to query')

    # Run repository workflow
    repo_build = subparsers.add_parser(
        'build',
        help='Run workflow for a given repository',
        description='Based on your repository configuration, compile and build the website',
        epilog='Example:\n\n'
               '   kb4it build /home/jsmith/Documents/myrepo/config/repo.json'
    )

    repo_build.add_argument(
        'config',
        help='Path to the repository config file (mandatory)'
    )

    # Get repository info
    repo_info = subparsers.add_parser(
        'info',
        help='Get repository info from its config file',
        description='Based on your repository configuration, get all info available',
        epilog='Example:\n\n'
               '   kb4it info /home/jsmith/Documents/myrepo/config/repo.json'
    )

    repo_info.add_argument(
        'config',
        help='Path to the repository config file (mandatory)'
    )

    # Dispatch to the appropriate action handler
    try:
        params = parser.parse_args()
        app = KB4IT(params)
        app.run()
    except SystemExit as error:
        if error.code != 0 and error.code is not None:
            print("Run 'kb4it <action name> --help' to get help for a specific command.")

