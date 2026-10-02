#!/usr/bin/env python

"""
KB4IT module. Entry point.

# Author: Tomás Vírseda <tomasvirseda@gmail.com>
# License: GPLv3
# Description: Website static-generator based on Markdown
"""

import argparse
import fcntl
import os
import sys
import uuid

from kb4it.core.env import ENV
from kb4it.core.exceptions import KB4ITError, CompilationError, ConfigError, ThemeError
from kb4it.core.log import get_logger, setup_logging
from kb4it.services.backend import Backend
from kb4it.services.builder import Builder
from kb4it.services.database import Database
from kb4it.services.frontend import Frontend
from kb4it.services.workflow import Workflow

# Held open for the lifetime of the process; released automatically on exit.
_lock_fd = None


def _acquire_process_lock():
    """Acquire an exclusive process lock at startup."""
    global _lock_fd
    lock_path = ENV["FILE"]["LOCK"]
    os.makedirs(os.path.dirname(lock_path), exist_ok=True)
    # O_RDWR|O_CREAT never truncates, so if flock fails, the other
    # process's PID is still readable from the file.
    raw = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o644)
    fd = os.fdopen(raw, "r+")
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        fd.seek(0)
        other_pid = fd.read().strip()
        fd.close()
        msg = f"KB4IT is already running (PID {other_pid})" if other_pid else "KB4IT is already running"
        print(msg, file=sys.stderr)
        sys.exit(1)
    fd.seek(0)
    fd.truncate()
    fd.write(str(os.getpid()))
    fd.flush()
    _lock_fd = fd


class KB4IT:
    """KB4IT main class."""

    repo = {}

    def __init__(self, params: argparse.Namespace = None):
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
            self.params["REPO_CONFIG_FILE"] = None

        # Initialize log
        if "log_level" not in self.params:
            self.params["LOGLEVEL"] = "INFO"
        setup_logging(self.params["log_level"], self.log_file)
        self.log = get_logger(__class__.__name__)
        self.log.debug(f"[CONTROLLER] KB4IT version={ENV['APP']['version']}")
        self.log.debug(f"[CONTROLLER] SYS python={ENV['SYS']['PYTHON']['VERSION']}")
        self.log.debug(f"[CONTROLLER] SYS mako={ENV['SYS']['MAKO']['VERSION']}")
        self.log.debug(f"[CONTROLLER] SYS platform={ENV['SYS']['PLATFORM']['OS']}")
        self.log.debug(f"[CONTROLLER] GPATH_ROOT path={ENV['GPATH']['ROOT']}")
        self.log.debug(f"[CONTROLLER] LPATH_ROOT path={ENV['LPATH']['ROOT']}")

        # Start up
        self.__check_params()
        self.__setup_services()

    def set_log_file(self):
        """Generate a temporary log file."""
        suffix = str(uuid.uuid1().time)
        self.log_file = f"{ENV['FILE']['LOG']}.{suffix}"

    def get_log_file(self):
        """Get log file path."""
        return self.log_file

    def __check_params(self):
        """Check arguments passed to the application."""
        for key in sorted(self.params):
            self.log.debug(f"[CONTROLLER] PARAM name={key} value={self.params[key]}")

    def get_params(self):
        """Return app configuration."""
        return self.params

    def __setup_environment(self):
        """Create local paths if they do not exist."""
        for path in ENV["LPATH"].values():
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)

    def __setup_services(self):
        """Declare and register services."""
        self.services = {}
        services = {
            "DB": Database(),
            "Backend": Backend(),
            "Frontend": Frontend(),
            "Builder": Builder(),
            "Workflow": Workflow(),
        }
        for name, klass in services.items():
            self.register_service(name, klass)

    def get_services(self):
        """Get all registered services."""
        return self.services

    def get_service(self, name: str):
        """Get or start a registered service."""
        service = self.services.get(name) or None
        if service is None:
            self.log.error(f"[CONTROLLER] SERVICE_NOT_REGISTERED name={name}")
            raise KB4ITError(f"Service not registered: {name}")
        if not service.is_started():
            service.start(self)
        return service

    def register_service(self, name, service):
        """Register a new service."""
        try:
            self.services[name] = service
            self.log.debug(f"[CONTROLLER] SERVICE_REGISTER name={name}")
            return service
        except KeyError as error:
            self.log.error(f"[CONTROLLER] ERROR {error}")
            return None

    def deregister_service(self, name):
        """Deregister a running service."""
        service = self.services.get(name)
        registered = service is not None
        started = service.is_started()
        if registered and started:
            service.end()
            self.log.debug(f"[CONTROLLER] SERVICE_UNREGISTER name={name}")
        service = None

    def run(self):
        """Run the requested action. Returns True on success, False on error."""
        action = self.params["action"]
        self.log.debug(f"[CONTROLLER] START version={ENV['APP']['version']}")
        self.log.debug(f"[CONTROLLER] ACTION name={action}")
        error = False
        try:
            workflow = self.get_service("Workflow")
            if action == "themes":
                workflow.list_themes()
            elif action == "projects":
                workflow.list_projects()
            elif action == "create":
                workflow.create_repository()
            elif action == "build":
                workflow.build_website()
            elif action == "info":
                workflow.info_repository()
            elif action == "verify":
                workflow.verify_sources()
            elif action == "apps":
                workflow.list_apps(self.params["theme"])
        except ConfigError as e:
            self.log.error(f"[CONTROLLER] CONFIG_ERROR reason={e}")
            error = True
        except ThemeError as e:
            self.log.error(f"[CONTROLLER] THEME_ERROR reason={e}")
            error = True
        except CompilationError as e:
            self.log.error(f"[CONTROLLER] COMPILE_ERROR reason={e}")
            error = True
        except KB4ITError as e:
            self.log.error(f"[CONTROLLER] KB4IT_ERROR reason={e}")
            error = True
        self.stop(error=error)
        return not error

    def stop(self, error=False):
        """Stop registered services by executing the 'end' method (if any)."""
        if error:
            self.log.error("[CONTROLLER] ABORT reason=serious_errors")
        try:
            for name in self.services:
                self.deregister_service(name)
        except AttributeError as errmsg:
            # KB4IT wasn't even started
            self.log.error(f"[CONTROLLER] ERROR {errmsg}")
        self.log.debug(f"[CONTROLLER] END version={ENV['APP']['version']}")


def main():
    """Set up application arguments and execute."""
    _acquire_process_lock()

    # When called with no arguments in an interactive terminal, launch the TUI
    if len(sys.argv) == 1 and sys.stdin.isatty() and sys.stdout.isatty():
        try:
            from kb4it.tui.app import run as run_tui
            run_tui()
        except ImportError as exc:
            print(f"TUI requires the 'textual' library: {exc}")
            print("Install it with: pip install textual")
        except KeyboardInterrupt:
            pass
        return

    extra_usage = """Thanks for using KB4IT!\n"""
    parser = argparse.ArgumentParser(
        prog="kb4it",
        description=f"KB4IT v{ENV['APP']['version']}\nCustomizable \
            static website generator based on Markdown sources",
        epilog=extra_usage,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "-L",
        "--log-level",
        help="Control output verbosity. Default set to INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"{ENV['APP']['shortname']} {ENV['APP']['version']}",
    )

    # Add subcommands for actions
    subparsers = parser.add_subparsers(
        dest="action", required=True, help="Action to perform"
    )

    # Initialize repository
    init_parser = subparsers.add_parser(
        "create", help="Initialize a new repository")
    init_parser.add_argument("theme", help="Theme to use for initialization")
    init_parser.add_argument(
        "app",
        nargs="?",
        default="default",
        help="App template to use (default: 'default')",
    )
    init_parser.add_argument("repo_path", help="Path to the repository")

    # List themes
    subparsers.add_parser("themes", help="List all installed themes")

    # List projects
    subparsers.add_parser("projects", help="List all projects created by the user")

    # List apps for a specific theme
    theme_apps = subparsers.add_parser(
        "apps", help="List all apps for a specific theme"
    )
    theme_apps.add_argument("theme", help="Theme to query")

    # Run repository workflow
    repo_build = subparsers.add_parser(
        "build",
        help="Run workflow for a given repository",
        description="Based on your repository configuration, compile and build the website",
        epilog="Example:\n\n"
        "   kb4it build /home/jsmith/Documents/myrepo/config/repo.json",
    )

    repo_build.add_argument(
        "config", help="Path to the repository config file (mandatory)"
    )
    repo_build.add_argument(
        "-f", "--force",
        action="store_true",
        default=False,
        help="Force recompilation of all documents, ignoring content hashes",
    )

    # Get repository info
    repo_info = subparsers.add_parser(
        "info",
        help="Get repository info from its config file",
        description="Based on your repository configuration, get all info available",
        epilog="Example:\n\n"
        "   kb4it info /home/jsmith/Documents/myrepo/config/repo.json",
    )

    repo_info.add_argument(
        "config", help="Path to the repository config file (mandatory)"
    )

    # Verify repository sources
    repo_verify = subparsers.add_parser(
        "verify",
        help="Verify project sources for a given repository",
        description="Check if all source files in the project are KB4IT conformant",
        epilog="Example:\n\n"
        "   kb4it verify /home/jsmith/Documents/myrepo/config/repo.json",
    )

    repo_verify.add_argument(
        "config", help="Path to the repository config file (mandatory)"
    )

    # Dispatch to the appropriate action handler
    try:
        params = parser.parse_args()
        app = KB4IT(params)
        success = app.run()
        sys.exit(0 if success else 1)
    except SystemExit:
        raise
    except Exception as error:
        print(f"Error: {error}")
        print("Run 'kb4it <action name> --help' to get help for a specific command.")
        sys.exit(1)


if __name__ == "__main__":
    main()
