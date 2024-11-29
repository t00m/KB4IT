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
import stat
import json
import multiprocessing
import argparse
from kb4it.core.env import ENV
from kb4it.core.log import get_logger
from kb4it.core.util import timestamp, copydir
from kb4it.services.backend import Backend
from kb4it.services.frontend import Frontend
from kb4it.services.database import Database
from kb4it.services.builder import Builder


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
        if 'LOGLEVEL' not in self.params:
            self.params.LOGLEVEL = 'INFO'
        self.__setup_logging(self.params.LOGLEVEL)

        self.log.info("[CONTROLLER] - KB4IT %s started at %s", ENV['APP']['version'], timestamp())

        # Start up
        self.__setup_environment()
        self.__check_params()
        self.__setup_services()

        #self.log.info("[CONTROLLER] - KB4IT %s started at %s", ENV['APP']['version'], timestamp())
        #self.log.debug("[CONTROLLER] - Log level set to %s", self.params.LOGLEVEL)
        #self.log.debug("[CONTROLLER] - Process: %s (%d)", ENV['PS']['NAME'], ENV['PS']['PID'])
        #self.log.debug("[CONTROLLER] - MaxWorkers: %d (default)", self.params.NUM_WORKERS)

        self.__gonogo()

    def __setup_logging(self, severity=None):
        """Set up logging."""
        self.log = get_logger(__class__.__name__, severity.upper())

    def __check_params(self):
        """Check arguments passed to the application."""

        self.log.info("[CONTROLLER] - Command line parameters:")
        for key in vars(self.params):
            self.log.info(f"[CONTROLLER] - \t{key}: {vars(self.params)[key]}")

    def get_app_params(self):
        """Return app configuration"""
        return self.params

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
                fpid.write(str(ENV['PS']['PID']))
            self.log.debug("[CONTROLLER] - Decision: Go")
        else:
            self.log.error(f"[CONTROLLER] - Decision: No Go")
            self.log.error(f"[CONTROLLER] - Reason: {no_go_reason}")
            self.stop()

    def get_services(self):
        """Get all registered services"""
        return self.services

    def get_service(self, name):
        """Get or start a registered service."""
        try:
            self.log.debug(f"[CONTROLLER] - Getting service '{name}'")
            service = self.services[name]
            logname = service.__class__.__name__
            if not service.is_started():
                service.start(self, logname, name)
            return service
        except Exception as error:
            self.log.error("[CONTROLLER] - Service %s not registered or not found", error)
            raise
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
        frontend = self.get_service('Frontend')

        if self.params.LIST_THEMES:
            frontend.theme_list()
        elif self.params.INIT:
            initialize = False
            theme, repo_path = self.params.INIT
            self.log.debug(f"[CONTROLLER] - Theme argument passed: {theme}")
            self.log.debug(f"[CONTROLLER] - Repo path argument passed: {repo_path}")
            theme_path = frontend.theme_search(theme=theme)
            if theme_path is None:
                self.log.error(f"[CONTROLLER] - Theme '{theme}' doesn't exist.")
                self.log.info("[CONTROLLER] - This is the list of themes available:")
                frontend.theme_list()
            else:
                if not os.path.exists(repo_path):
                    self.log.error(f"[CONTROLLER] - Repository path '{repo_path}' does not exist")
                else:
                    initialize = True

            if initialize:
                self.log.info(f"[CONTROLLER] - Repository path: {repo_path}")
                self.log.info(f"[CONTROLLER] - Using theme '{theme}' from path '{theme_path}'")
                repo_demo = os.path.join(theme_path, 'example', 'repo')
                copydir(repo_demo, repo_path)
                source_dir = os.path.join(repo_path, 'source')
                target_dir = os.path.join(repo_path, 'target')
                bin_dir = os.path.join(repo_path, 'bin')
                script = os.path.join(bin_dir, 'compile.sh')
                config_file = os.path.join(repo_path, 'config', 'repo.json')
                with open(config_file, 'r') as fc:
                    repoconf = json.load(fc)
                repoconf['source'] = source_dir
                repoconf['target'] = target_dir
                with open(config_file, 'w') as fc:
                    json.dump(repoconf, fc, sort_keys=True, indent=4)
                os.makedirs(bin_dir, exist_ok=True)
                with open(script, 'w') as fs:
                    fs.write(f'kb4it -r {config_file} -L INFO')
                os.chmod(script, stat.S_IRUSR | stat.S_IRGRP | stat.S_IWUSR | stat.S_IWGRP | stat.S_IXUSR | stat.S_IXGRP)
                self.log.info(f"[CONTROLLER] - Repository initialized")
                self.log.info(f"[CONTROLLER] - You can compile it by executing '{script}'")
                self.log.info(f"[CONTROLLER] - Add your documents in '{source_dir}'")
                self.log.info(f"[CONTROLLER] - Documents to be published in '{target_dir}'")
                self.log.info(f"[CONTROLLER] - Check your repository settings in '{config_file}'")
                self.log.info(f"[CONTROLLER] - For more KB4IT options, execute: kb4it -h")
        else:
            backend = self.get_service('Backend')
            backend.run()
        self.stop()

    def stop(self):
        """Stop registered services by executing the 'end' method (if any)."""
        try:
            for name in self.services:
                self.deregister_service(name)
        except AttributeError:
            # KB4IT wasn't even started
            pass
        self.log.debug("[CONTROLLER] - KB4IT %s finished at %s", ENV['APP']['version'], timestamp())
        sys.exit()


def main():
    """Set up application arguments and execute."""
    extra_usage = """Thanks for using KB4IT!\n"""
    parser = argparse.ArgumentParser(
        prog='kb4it',
        description='KB4IT v%s\nCustomizable static website generator based on Asciidoctor sources' % ENV['APP']['version'],
        epilog=extra_usage,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    NUM_WORKERS = get_default_workers()

    # KB4IT options
    kb4it_options = parser.add_argument_group('KB4IT Options')
    kb4it_options.add_argument('-f', '--force', help='Force a clean compilation', action='store_true', dest='FORCE', required=False, default=False)
    kb4it_options.add_argument('-i', '--init', help='Initialize repository', nargs=2, metavar=('THEME', 'REPO_PATH'), dest='INIT', required=False)
    kb4it_options.add_argument('-l', '--list-themes', help='List all installed themes', action='store_true', dest='LIST_THEMES', required=False, default=False)
    kb4it_options.add_argument('-r', '--repo', help='Use this repository config file', action='store', dest='REPO_CONFIG_FILE')
    kb4it_options.add_argument('-w', '--workers', help='Number of workers. Default is CPUs available/2. Default number of workers in this machine: %d' % NUM_WORKERS, type=int, action='store', dest='NUM_WORKERS', default=int(NUM_WORKERS), required=False)
    kb4it_options.add_argument('-L', '--log-level', help='Control output verbosity. Default set to INFO', dest='LOGLEVEL', action='store', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO', required=False)
    kb4it_options.add_argument('-v', '--version', help='Show current version', action='version', version='%s %s' % (ENV['APP']['shortname'], ENV['APP']['version']))

    params = parser.parse_args()
    app = KB4IT(params)
    app.run()
